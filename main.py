"""Deterministic K1h trophy-rate quantile forecast; standard library only."""

import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import NormalDist, median


ORIGIN = datetime(2026, 11, 19, tzinfo=timezone.utc)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
Z = tuple(NormalDist().inv_cdf(tau) for tau in LEVELS)


def hours(timestamp):
    return (datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            - ORIGIN).total_seconds() / 3600.0


def clamp(value, low, high):
    return min(high, max(low, value))


def logit(rate):
    p = clamp(rate, 0.01, 99.99) / 100.0
    return math.log(p / (1.0 - p))


def inverse_logit(value):
    if value >= 0:
        return 100.0 / (1.0 + math.exp(-value))
    e = math.exp(value)
    return 100.0 * e / (1.0 + e)


def quantiles(center, spread):
    result = []
    for z in Z:
        value = clamp(inverse_logit(center + z * spread), 0.01, 99.99)
        value = float(Decimal(str(value)).quantize(Decimal("0.0001"),
                                                 rounding=ROUND_HALF_UP))
        if result:
            value = max(value, result[-1])
        result.append(int(value) if value.is_integer() else value)
    return result


def distinct_reads(history):
    result = []
    for read in history:
        if (not result or read["players_tracked"] != result[-1]["players_tracked"]
                or read["rates"] != result[-1]["rates"]):
            result.append(read)
    return result


def fit(xs, ys, weights):
    """Weighted slope and population residual standard deviation."""
    total = sum(weights)
    if not xs or total == 0:
        return 0.0, None
    mx = sum(w * x for w, x in zip(weights, xs)) / total
    my = sum(w * y for w, y in zip(weights, ys)) / total
    variance = sum(w * (x - mx) ** 2 for w, x in zip(weights, xs))
    slope = (sum(w * (x - mx) * (y - my)
                 for w, x, y in zip(weights, xs, ys)) / variance
             if variance > 0 else 0.0)
    residual = (math.sqrt(sum(w * (y - my - slope * (x - mx)) ** 2
                              for w, x, y in zip(weights, xs, ys)) / total)
                if len(xs) >= 3 else None)
    return slope, residual


def kink_detector(reads, times):
    nq = len(reads) // 4
    if len(reads) < 12 or nq < 3:
        return False, None, None
    players = [math.log(max(1, r["players_tracked"])) for r in reads]
    g_q1 = fit(times[:nq], players[:nq], [1.0] * nq)[0]
    g_q4 = fit(times[-nq:], players[-nq:], [1.0] * nq)[0]
    return g_q1 > 0.01 and g_q4 < 0.5 * g_q1, g_q1, g_q4


def forecast(case, diagnostics=None):
    trophies = case["trophies"]
    reads = distinct_reads(case["history"])
    if not reads or not any(r["players_tracked"] > 0 for r in reads):
        return {"trophies": [{"id": t["id"], "q": quantiles(logit(1), 2.0)}
                             for t in sorted(trophies, key=lambda t: t["id"])]}
    times = [hours(r["at"]) for r in reads]
    xs = [math.log1p(t) for t in times]
    target = hours(case["target"])
    horizon = max(0.0, target - times[-1])
    span = max(0.0, times[-1] - times[0])
    refreshes = len(reads) - 1
    kink, g_q1, g_q4 = kink_detector(reads, times)
    scale = 0.7 if not kink and len(reads) >= 12 else 1.0
    random_walk = 0.5 * math.sqrt(max(0, case["horizon_minutes"]) / 1440.0)
    models = []
    pooled_steps = []
    emerged_tiers = set()
    for i, trophy in enumerate(trophies):
        valid = [j for j, r in enumerate(reads) if r["rates"][i] is not None]
        rates = [reads[j]["rates"][i] for j in valid]
        ys = [logit(rate) for rate in rates]
        vx = [xs[j] for j in valid]
        fits = [fit(vx, ys, [0.5 ** ((times[-1] - times[j]) / half_life)
                            for j in valid]) for half_life in (3.0, 12.0)]
        (slope3, residual3), (slope12, residual12) = fits
        guard = (refreshes >= 1 and not kink and abs(slope12) > 0.1
                 and slope3 / slope12 < 0.3)
        slope, residual = fits[1 if guard else 0]
        steps = []
        for left, right in zip(reads, reads[1:]):
            a, b = left["rates"][i], right["rates"][i]
            if a is not None and b is not None:
                step = logit(b) - logit(a)
                pooled_steps.append(step)
                if step != 0:
                    steps.append(step)
        if rates and rates[0] == 0 and any(r > 0 for r in rates[1:]):
            emerged_tiers.add(trophy["tier"])
        models.append(dict(rates=rates, steps=steps, slope=slope,
                           residual=residual, slope3=slope3, slope12=slope12,
                           residual3=residual3, residual12=residual12, guard=guard))
    residuals = [m["residual"] for m in models if m["residual"] is not None]
    pooled_residual = median(residuals) if residuals else 0.0
    step_rms = math.sqrt(sum(s * s for s in pooled_steps) / len(pooled_steps)) if pooled_steps else 0.0
    expected_refreshes = clamp(refreshes * horizon / span, 1.0, 10.0) if span > 0 else 1.0
    jump = min(1.2, 0.6 * step_rms * math.sqrt(expected_refreshes)) if refreshes else 1.0
    exponent = clamp(horizon * 60.0 / 90.0, 0.0, 1.0)
    players_factor = 6.06 ** exponent
    earners_factor = 1.34 ** exponent
    rows = []
    for trophy, model in zip(trophies, models):
        rates = model["rates"]
        if not rates:
            q = quantiles(logit(0.5), 2.0)
        elif rates[-1] >= 99.99:
            q = [99.8, 100, 100, 100, 100]
        else:
            last = rates[-1]
            center = logit(last)
            residual = model["residual"] if model["residual"] is not None else pooled_residual
            spread = clamp(max(random_walk, residual, jump), 1.0 if refreshes == 0 else 0.55, 2.2)
            if all(r == 0 for r in rates):
                center = logit(0.01)
                if trophy["tier"] in emerged_tiers:
                    spread = clamp(max(random_walk, pooled_residual, jump), 1.0, 2.2)
                else:
                    spread = clamp(random_walk, 0.30, 0.55)
            elif refreshes == 0:
                scenario = last * earners_factor / players_factor
                center = 0.75 * logit(scenario) + 0.25 * logit(last)
            else:
                delta = model["slope"] * (math.log1p(target) - xs[-1])
                steps = model["steps"]
                if not steps:
                    agreement = 0.0
                elif abs(delta) < 1e-9 or len(steps) < 2:
                    agreement = 0.5
                else:
                    agreement = sum(s * delta > 0 for s in steps) / len(steps)
                distance = span / (span + horizon) if span + horizon > 0 else 0.0
                weight = refreshes / (refreshes + 2.0) * agreement * distance
                center += clamp(weight * delta, -1.0, 1.0)
            scaled_spread = min(2.2, spread * scale)
            q = quantiles(center, scaled_spread)
            model.update(center=center, spread=spread, scaled_spread=scaled_spread)
        rows.append({"id": trophy["id"], "q": q})
    if diagnostics is not None:
        diagnostics.update(distinct=len(reads), refreshes=refreshes, kink=kink,
                           g_q1=g_q1, g_q4=g_q4, scale=scale, models=models,
                           random_walk=random_walk, jump=jump, step_rms=step_rms,
                           pooled_residual=pooled_residual,
                           players_factor=players_factor, earners_factor=earners_factor)
    return {"trophies": sorted(rows, key=lambda row: row["id"])}


def main():
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(input_dir.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        result = forecast(case)
        (output_dir / (path.stem + ".out")).write_text(
            json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n",
            encoding="utf-8")


if __name__ == "__main__":
    main()
