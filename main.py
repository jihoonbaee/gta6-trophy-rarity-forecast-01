"""Deterministic V3 trophy-rate quantiles; Python standard library only."""

import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import NormalDist, median

EPOCH = datetime(2026, 11, 19, tzinfo=timezone.utc)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
NORMAL_Z = tuple(NormalDist().inv_cdf(t) for t in LEVELS)
PLAYER_FACTOR = 6.06
EARNER_FACTOR = 1.34


def timestamp(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def hours(text):
    return (timestamp(text) - EPOCH).total_seconds() / 3600


def logit(rate):
    p = min(99.99, max(0.01, rate)) / 100
    return math.log(p / (1 - p))


def inverse(value):
    if value >= 0:
        return 100 / (1 + math.exp(-value))
    e = math.exp(value)
    return 100 * e / (1 + e)


def rounded(value):
    result = float(Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
    return int(result) if result.is_integer() else result


def quantiles(center, spread):
    result = []
    for z in NORMAL_Z:
        q = min(99.99, max(0.01, rounded(inverse(center + z * spread))))
        result.append(max(result[-1], q) if result else q)
    return result


def distinct(history):
    result = []
    for row in history:
        if (not result or row["players_tracked"] != result[-1]["players_tracked"]
                or row["rates"] != result[-1]["rates"]):
            result.append(row)
    return result


def fit(xs, ys, weights):
    total = sum(weights)
    mx = sum(w * x for w, x in zip(weights, xs)) / total
    my = sum(w * y for w, y in zip(weights, ys)) / total
    variance = sum(w * (x - mx) ** 2 for w, x in zip(weights, xs))
    slope = (sum(w * (x - mx) * (y - my) for w, x, y in zip(weights, xs, ys))
             / variance if variance > 0 else 0.0)
    intercept = my - slope * mx
    residual = math.sqrt(sum(w * (y - intercept - slope * x) ** 2
                             for w, x, y in zip(weights, xs, ys)) / total)
    return slope, residual


def frozen_factors(horizon_minutes):
    exponent = min(1.0, max(0.0, horizon_minutes / 90))
    return PLAYER_FACTOR ** exponent, EARNER_FACTOR ** exponent


def forecast(case):
    trophies = case["trophies"]
    history = distinct(case["history"])
    if not history or not any(r["players_tracked"] > 0 for r in history):
        return {"trophies": [{"id": t["id"], "q": quantiles(logit(1), 2)}
                             for t in sorted(trophies, key=lambda t: t["id"])]}
    times = [hours(r["at"]) for r in history]
    xs = [math.log1p(t) for t in times]
    target_x = math.log1p(hours(case["target"]))
    horizon = max(0.0, hours(case["target"]) - times[-1])
    span = max(0.0, times[-1] - times[0])
    refreshes = len(history) - 1
    weights = [2 ** (-(times[-1] - t) / 12) for t in times]
    walk = 0.5 * math.sqrt(max(0, case["horizon_minutes"]) / 1440)
    models, steps_all, emerging_tiers = [], [], set()
    for i, trophy in enumerate(trophies):
        indices = [j for j, row in enumerate(history) if row["rates"][i] is not None]
        rates = [history[j]["rates"][i] for j in indices]
        ys = [logit(r) for r in rates]
        slope, residual = (fit([xs[j] for j in indices], ys, [weights[j] for j in indices])
                           if indices else (0.0, 0.0))
        steps = [logit(b["rates"][i]) - logit(a["rates"][i])
                 for a, b in zip(history, history[1:])
                 if a["rates"][i] is not None and b["rates"][i] is not None]
        steps_all.extend(steps)
        if rates and rates[0] == 0 and any(r > 0 for r in rates[1:]):
            emerging_tiers.add(trophy["tier"])
        models.append((rates, ys, slope, residual if len(indices) >= 3 else None, steps))
    residuals = [m[3] for m in models if m[3] is not None]
    pooled_residual = median(residuals) if residuals else 0.0
    if refreshes == 0:
        jump = 1.0
    else:
        rms = math.sqrt(sum(s * s for s in steps_all) / len(steps_all)) if steps_all else 0.0
        count = min(10.0, max(1.0, refreshes * horizon / span)) if span else 1.0
        jump = min(1.2, 0.6 * rms * math.sqrt(count))
    rows = []
    for trophy, (rates, ys, slope, residual, steps) in zip(trophies, models):
        if not rates:
            q = quantiles(logit(0.5), 2.0)
        elif rates[-1] >= 99.99:
            q = [99.8, 100, 100, 100, 100]
        else:
            spread = min(2.2, max(1.0 if refreshes == 0 else 0.55,
                                  walk, pooled_residual if residual is None else residual, jump))
            center = ys[-1]
            if all(r == 0 for r in rates):
                center = logit(0.01)
                if trophy["tier"] in emerging_tiers:
                    spread = min(2.2, max(1.0, walk, pooled_residual, jump))
                else:
                    spread = min(0.55, max(0.30, walk))
            elif refreshes == 0:
                players, earners = frozen_factors(horizon * 60)
                center = 0.75 * logit(rates[-1] * earners / players) + 0.25 * center
            else:
                delta = slope * (target_x - xs[-1])
                if abs(delta) < 1e-9:
                    delta = 0.0
                nonzero = [s for s in steps if s != 0]
                if nonzero:
                    agreement = (0.5 if len(nonzero) < 2 or abs(delta) < 1e-9
                                 else sum(s * delta > 0 for s in nonzero) / len(nonzero))
                    distance = span / (span + horizon) if span + horizon else 0.0
                    change = refreshes / (refreshes + 2) * agreement * distance * delta
                    center += min(1.0, max(-1.0, change))
            q = quantiles(center, spread)
        rows.append({"id": trophy["id"], "q": q})
    return {"trophies": sorted(rows, key=lambda row: row["id"])}


def main():
    source = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    destination = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        output = json.dumps(forecast(case), separators=(",", ":"), allow_nan=False) + "\n"
        (destination / (path.stem + ".out")).write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
