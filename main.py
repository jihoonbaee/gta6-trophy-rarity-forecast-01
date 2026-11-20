"""K1g quantile forecasts for GTA VI trophy earn rates."""

import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from statistics import NormalDist, median


EPOCH = datetime(2026, 11, 19, tzinfo=timezone.utc)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
NORMAL_QUANTILES = tuple(NormalDist().inv_cdf(level) for level in LEVELS)
PLAYER_FACTOR = 6.06
EARNER_FACTOR = 1.34


def clamp(value, low, high):
    return min(high, max(low, value))


def hours_at(timestamp):
    return (datetime.fromisoformat(timestamp) - EPOCH).total_seconds() / 3600


def logit(rate):
    p = clamp(rate, 0.01, 99.99) / 100
    return math.log(p / (1 - p))


def quantiles(center, spread):
    result = []
    for z in NORMAL_QUANTILES:
        rate = 100 / (1 + math.exp(-(center + z * spread)))
        rounded = Decimal(str(rate)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        q = clamp(float(rounded), 0.01, 99.99)
        if result:
            q = max(q, result[-1])
        result.append(int(q) if q == int(q) else q)
    return result


def distinct_reads(history):
    distinct = []
    for read in history:
        if distinct:
            prev = distinct[-1]
            if read["players_tracked"] == prev["players_tracked"] and read["rates"] == prev["rates"]:
                continue
        distinct.append(read)
    return distinct


def linear_fit(points):
    """Return slope and weighted RMS residual, if defined, for (x, y, weight)."""
    if len(points) < 2:
        return 0.0, None
    total = math.fsum(w for _, _, w in points)
    mean_x = math.fsum(w * x for x, _, w in points) / total
    mean_y = math.fsum(w * y for _, y, w in points) / total
    variance = math.fsum(w * (x - mean_x) ** 2 for x, _, w in points)
    covariance = math.fsum(w * (x - mean_x) * (y - mean_y) for x, y, w in points)
    slope = covariance / variance if variance else 0.0
    residual = None
    if len(points) >= 3:
        residual = math.sqrt(math.fsum(
            w * (y - mean_y - slope * (x - mean_x)) ** 2 for x, y, w in points
        ) / total)
    return slope, residual


def player_kink(reads, hours):
    if len(reads) < 12:
        return False
    n = len(reads) // 4
    points = [(h, math.log(max(1, r["players_tracked"])), 1) for h, r in zip(hours, reads)]
    g_q1, _ = linear_fit(points[:n])
    g_q4, _ = linear_fit(points[-n:])
    return g_q1 > 0.01 and g_q4 < 0.5 * g_q1


def use_slow_fit(kink, slope3, slope12):
    return not kink and abs(slope12) > 0.1 and slope3 / slope12 < 0.3


def scenario_factors(horizon_minutes):
    power = clamp(horizon_minutes / 90, 0, 1)
    return PLAYER_FACTOR ** power, EARNER_FACTOR ** power


def trend_change(slope, dx, steps, refreshes, span, horizon):
    delta = slope * dx
    moving = [step for step in steps if step != 0]
    if not moving or abs(delta) < 1e-9:
        return 0.0
    agreement = 0.5
    if len(moving) >= 2:
        agreement = sum((step > 0) == (delta > 0) for step in moving) / len(moving)
    distance = span / (span + horizon) if span + horizon else 0.0
    return clamp((refreshes / (refreshes + 2)) * agreement * distance * delta, -1, 1)


def forecast(case):
    trophies = case["trophies"]
    reads = distinct_reads(case["history"])
    ordered = sorted(enumerate(trophies), key=lambda item: item[1]["id"])
    if not any(r["players_tracked"] > 0 for r in reads):
        return {"trophies": [{"id": t["id"], "q": quantiles(logit(1), 2)} for _, t in ordered]}

    hours = [hours_at(read["at"]) for read in reads]
    xs = [math.log1p(hour) for hour in hours]
    target = hours_at(case["target"])
    horizon = max(0, target - hours[-1])
    span = hours[-1] - hours[0]
    dx = math.log1p(target) - xs[-1]
    refreshes = len(reads) - 1
    walk = 0.5 * math.sqrt(case["horizon_minutes"] / 1440)

    rates = [list(column) for column in zip(*(read["rates"] for read in reads))]
    observed = [[rate for rate in column if rate is not None] for column in rates]
    emerging_tiers = {
        t["tier"] for t, values in zip(trophies, observed)
        if values and values[0] == 0 and any(rate > 0 for rate in values[1:])
    }
    fits = [(0.0, None)] * len(trophies)
    steps = [[] for _ in trophies]
    if refreshes:
        kink = player_kink(reads, hours)
        weights3 = [0.5 ** ((hours[-1] - h) / 3) for h in hours]
        weights12 = [0.5 ** ((hours[-1] - h) / 12) for h in hours]
        for i, column in enumerate(rates):
            ys = [logit(rate) if rate is not None else None for rate in column]
            steps[i] = [b - a for a, b in zip(ys, ys[1:]) if a is not None and b is not None]
            fast, slow = (
                linear_fit([(x, y, w) for x, y, w in zip(xs, ys, weights) if y is not None])
                for weights in (weights3, weights12)
            )
            fits[i] = slow if use_slow_fit(kink, fast[0], slow[0]) else fast

        squares = [step ** 2 for series in steps for step in series]
        rms = math.sqrt(math.fsum(squares) / len(squares)) if squares else 0.0
        count = clamp(refreshes * horizon / span, 1, 10) if span else 10
        jump = min(1.2, 0.6 * rms * math.sqrt(count))
        rate_factor = 1.0
    else:
        players, earners = scenario_factors(horizon * 60)
        rate_factor = earners / players
        jump = 1.0

    residuals = [residual for _, residual in fits if residual is not None]
    pooled_residual = median(residuals) if residuals else 0.0
    rows = []
    for i, trophy in ordered:
        values = observed[i]
        if not values:
            q = quantiles(logit(0.5), 2)
        elif values[-1] >= 99.99:
            q = [99.8, 100, 100, 100, 100]
        elif not any(values):
            if trophy["tier"] in emerging_tiers:
                spread = clamp(max(walk, pooled_residual, jump), 1.0, 2.2)
            else:
                spread = clamp(walk, 0.30, 0.55)
            q = quantiles(logit(0.01), spread)
        else:
            last = values[-1]
            center = logit(last)
            slope, residual = fits[i]
            if refreshes:
                center += trend_change(slope, dx, steps[i], refreshes, span, horizon)
            else:
                center = 0.75 * logit(last * rate_factor) + 0.25 * center
            spread = clamp(max(walk, pooled_residual if residual is None else residual, jump),
                           0.55 if refreshes else 1.0, 2.2)
            q = quantiles(center, spread)
        rows.append({"id": trophy["id"], "q": q})
    return {"trophies": rows}


def main():
    inputs = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    outputs = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    outputs.mkdir(parents=True, exist_ok=True)
    for source in sorted(inputs.glob("*.in")):
        case = json.loads(source.read_text(encoding="utf-8"))
        result = json.dumps(forecast(case), separators=(",", ":"), allow_nan=False)
        (outputs / source.with_suffix(".out").name).write_text(result + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
