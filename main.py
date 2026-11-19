#!/usr/bin/env python3
"""GTA6 Trophy-Rarity-Forecast — candidate entry (fresh implementation).

Persistence-centered damped direct trend with a frozen-history prior
scenario branch. Standard library only, deterministic, no network.
Implements Design Brief v2 final (19 Nov 2026) from prose; no earlier
candidate code was read or used.

Layout: one forecast file per input case. Input directory from
MAKEFUN_INPUT_DIR (default /input), output directory from
MAKEFUN_OUTPUT_DIR (default /output).
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from statistics import NormalDist

EPOCH = datetime(2026, 11, 19, 0, 0, 0, tzinfo=timezone.utc)
HALF_LIFE_HOURS = 12.0
MAX_INCREMENT_LOGIT = 1.0
SPREAD_MIN = 0.55
SPREAD_MAX = 2.2
FROZEN_SPREAD_MIN = 1.0
FROZEN_REF_HORIZON_MIN = 90.0
PLAYER_GROWTH = 3.0
EARNER_GROWTH = 1.6
DELTA_EPS = 1e-9
DEFAULT_LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
NORM = NormalDist()


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def parse_time(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def hours_since_epoch(moment):
    return (moment - EPOCH).total_seconds() / 3600.0


def log_time(moment):
    """x = ln(1 + hours since 2026-11-19T00:00Z).

    Raises ValueError when the transform is undefined (1 + hours <= 0);
    the caller degrades that case to a persistence forecast instead of
    silently changing the formula.
    """
    value = 1.0 + hours_since_epoch(moment)
    if value <= 0.0:
        raise ValueError(
            "log-time undefined (1 + hours = %r) for %s" % (value, moment)
        )
    return math.log(value)


def clamp_pct(pct):
    return min(99.99, max(0.01, pct))


def logit_pct(pct):
    p = clamp_pct(pct) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit_pct(y):
    return 100.0 / (1.0 + math.exp(-y))


def round4(value):
    """Round to 4 decimals, halves away from zero; whole numbers as int."""
    quantized = Decimal(str(value)).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    number = float(quantized)
    if number == int(number):
        return int(number)
    return number


def finalize_quantiles(values):
    """Round, clamp to [0.01, 99.99], then force non-decreasing order."""
    out = []
    previous = None
    for value in values:
        current = min(99.99, max(0.01, round4(value)))
        if previous is not None and current < previous:
            current = previous
        out.append(current)
        previous = current
    return out


def quantiles_from(median_logit, spread, levels):
    values = [
        inv_logit_pct(median_logit + NORM.inv_cdf(tau) * spread)
        for tau in levels
    ]
    return finalize_quantiles(values)


def weighted_linregress(xs, ys, ws):
    """Weighted least squares y = a + b*x. None when the slope is undefined."""
    total_w = sum(ws)
    if total_w <= 0.0:
        return None
    mean_x = sum(w * x for w, x in zip(ws, xs)) / total_w
    mean_y = sum(w * y for w, y in zip(ws, ys)) / total_w
    sxx = sum(w * (x - mean_x) ** 2 for w, x in zip(ws, xs))
    if sxx <= 0.0:
        return None
    sxy = sum(w * (x - mean_x) * (y - mean_y) for w, x, y in zip(ws, xs, ys))
    slope = sxy / sxx
    return (mean_y - slope * mean_x, slope)


def median_of(values):
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        return None
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


# ---------------------------------------------------------------------------
# History preparation
# ---------------------------------------------------------------------------

def dedupe_history(history):
    """Collapse consecutive identical reads into one observation.

    Two reads are identical when players_tracked and the full rates list
    (including null positions) agree. The collapsed observation keeps the
    FIRST read's timestamp. Returns [(timestamp, players, rates), ...].
    """
    observations = []
    for read in history:
        key = (read.get("players_tracked"), tuple(read.get("rates") or []))
        if observations and observations[-1][3] == key:
            continue
        observations.append(
            (
                parse_time(read["at"]),
                read.get("players_tracked"),
                list(read.get("rates") or []),
                key,
            )
        )
    return [(t, p, r) for (t, p, r, _k) in observations]


# ---------------------------------------------------------------------------
# Per-case forecast
# ---------------------------------------------------------------------------

def forecast_case(case):
    trophies = case["trophies"]
    levels = case.get("levels") or list(DEFAULT_LEVELS)
    history = case.get("history") or []
    target = parse_time(case["target"])
    horizon_minutes = max(0.0, float(case.get("horizon_minutes") or 0.0))

    observations = dedupe_history(history)
    # Guardrail 1: validate the log-time domain on every timestamp used.
    for (moment, _p, _r) in observations:
        log_time(moment)
    x_target = log_time(target)

    # Edge case: no history, or no read with a positive player count.
    if not observations or not any((p or 0) > 0 for (_t, p, _r) in observations):
        return {
            "trophies": [
                {
                    "id": trophy["id"],
                    "q": quantiles_from(logit_pct(1.0), 2.0, levels),
                }
                for trophy in sorted(trophies, key=lambda t: t["id"])
            ]
        }

    refresh_count = max(0, len(observations) - 1)
    first_time = observations[0][0]
    last_time = observations[-1][0]
    span_hours = max(
        0.0, (last_time - first_time).total_seconds() / 3600.0
    )
    horizon_hours = max(0.0, (target - last_time).total_seconds() / 3600.0)
    prior_h_minutes = max(0.0, (target - last_time).total_seconds() / 60.0)

    # Per-trophy series over distinct observations: (x, logit, weight).
    # Recency weights use age relative to the last distinct observation
    # (uniform weight rescaling cannot change a weighted fit, so the
    # reference point is immaterial).
    series = []
    last_rate = []
    for index in range(len(trophies)):
        points = []
        last = None
        for (moment, _p, rates) in observations:
            rate = rates[index] if index < len(rates) else None
            if rate is None:
                continue
            last = rate
            age_hours = max(
                0.0, (last_time - moment).total_seconds() / 3600.0
            )
            points.append(
                (
                    log_time(moment),
                    logit_pct(rate),
                    0.5 ** (age_hours / HALF_LIFE_HOURS),
                )
            )
        series.append(points)
        last_rate.append(last)

    # Trend fits and weighted residual RMS per trophy (trend branch only).
    fits = []
    residuals = []
    for points in series:
        fit = None
        residual = None
        if refresh_count >= 1 and len(points) >= 2:
            fit = weighted_linregress(
                [p[0] for p in points],
                [p[1] for p in points],
                [p[2] for p in points],
            )
        if fit is not None and len(points) >= 3:
            intercept, slope = fit
            num = sum(
                w * (y - (intercept + slope * x)) ** 2
                for (x, y, w) in points
            )
            den = sum(w for (_x, _y, w) in points)
            residual = math.sqrt(num / den) if den > 0.0 else None
        fits.append(fit)
        residuals.append(residual)
    median_residual = median_of([r for r in residuals if r is not None])

    # Pooled refresh step size: RMS of logit changes between consecutive
    # distinct observations, across all trophies, INCLUDING zero changes.
    changes = []
    for index in range(len(trophies)):
        previous = None
        for (_t, _p, rates) in observations:
            rate = rates[index] if index < len(rates) else None
            if rate is None:
                previous = None
                continue
            current = logit_pct(rate)
            if previous is not None:
                changes.append(current - previous)
            previous = current
    if changes:
        step_size = math.sqrt(sum(c * c for c in changes) / len(changes))
    else:
        step_size = 0.0

    # Refresh-jump spread component (case level).
    if refresh_count == 0:
        refresh_jump = 1.0
    else:
        if span_hours > 0.0:
            expected = (refresh_count / span_hours) * horizon_hours
        else:
            expected = 1.0
        expected = min(10.0, max(1.0, expected))
        refresh_jump = min(0.6 * step_size * math.sqrt(expected), 1.2)

    random_walk = 0.5 * math.sqrt(horizon_minutes / 1440.0)

    def general_spread(trophy_index):
        residual = residuals[trophy_index]
        if residual is None:
            residual = median_residual if median_residual is not None else 0.0
        spread = max(random_walk, residual, refresh_jump)
        floor = FROZEN_SPREAD_MIN if refresh_count == 0 else SPREAD_MIN
        return min(SPREAD_MAX, max(floor, spread))

    # Which tiers have a trophy that moved from 0% to positive (0% rule).
    moved_tiers = set()
    for index, trophy in enumerate(trophies):
        first_nonnull = None
        moved = False
        for (_t, _p, rates) in observations:
            rate = rates[index] if index < len(rates) else None
            if rate is None:
                continue
            if first_nonnull is None:
                first_nonnull = rate
            elif first_nonnull == 0 and rate > 0:
                moved = True
                break
        if moved:
            moved_tiers.add(trophy.get("tier"))

    # Map trophy id -> position in the case's trophy list (the series,
    # fits and residuals lists are indexed by that position).
    id_to_position = {trophy["id"]: i for i, trophy in enumerate(trophies)}

    rows = []
    for trophy in sorted(trophies, key=lambda t: t["id"]):
        position = id_to_position[trophy["id"]]
        points = series[position]
        rate = last_rate[position]

        # No non-null rate at all for this trophy.
        if rate is None:
            rows.append(
                {
                    "id": trophy["id"],
                    "q": quantiles_from(logit_pct(0.5), 2.0, levels),
                }
            )
            continue

        # 100% trophies: fixed coherent row (all branches).
        if rate >= 99.99:
            rows.append(
                {
                    "id": trophy["id"],
                    "q": [99.8 if tau < 0.20 else 100 for tau in levels],
                }
            )
            continue

        # 0% trophies: only when never observed positive (a trophy that
        # was positive before and diluted to 0% takes the normal branch).
        ever_positive = any(
            (rates[position] or 0) > 0
            for (_t, _p, rates) in observations
            if position < len(rates) and rates[position] is not None
        )
        if rate == 0 and not ever_positive:
            if trophy.get("tier") in moved_tiers:
                spread = general_spread(position)
                spread = min(SPREAD_MAX, max(1.0, spread))
            else:
                spread = min(0.55, max(0.30, random_walk))
            rows.append(
                {
                    "id": trophy["id"],
                    "q": quantiles_from(logit_pct(0.01), spread, levels),
                }
            )
            continue

        if refresh_count == 0:
            # Frozen-history prior branch: 50/50 blend (logit space) of
            # the dilution scenario and persistence.
            player_factor = min(
                PLAYER_GROWTH,
                PLAYER_GROWTH
                ** (prior_h_minutes / FROZEN_REF_HORIZON_MIN),
            )
            earner_factor = min(
                EARNER_GROWTH,
                EARNER_GROWTH
                ** (prior_h_minutes / FROZEN_REF_HORIZON_MIN),
            )
            dilution_rate = rate * (earner_factor / player_factor)
            median_logit = (
                logit_pct(dilution_rate) + logit_pct(rate)
            ) / 2.0
            spread = general_spread(position)
        else:
            # Trend branch: persistence anchor + damped fitted increment.
            fit = fits[position]
            if fit is None or len(points) < 2:
                # Guardrail 2: fewer than two distinct non-null points
                # (including exactly one non-null rate) -> persistence,
                # no trend.
                median_logit = logit_pct(rate)
                spread = general_spread(position)
            else:
                _intercept, slope = fit
                # Delta is measured from THIS trophy's last non-null
                # observation (points are chronological), so the fitted
                # increment shares its reference point with the
                # persistence anchor (the trophy's last observed rate).
                # With no trailing nulls this equals the case's last
                # observation; the horizon-zero property then holds
                # per trophy even when a trophy is null in the latest
                # read(s).
                x_trophy_last = points[-1][0]
                delta = slope * (x_target - x_trophy_last)
                steps = []
                previous = None
                for (_t, _p, rates) in observations:
                    r = rates[position] if position < len(rates) else None
                    if r is None:
                        previous = None
                        continue
                    current = logit_pct(r)
                    if previous is not None:
                        step = current - previous
                        if step != 0.0:
                            steps.append(step)
                    previous = current
                if not steps:
                    weight = 0.0
                else:
                    if abs(delta) < DELTA_EPS or len(steps) < 2:
                        agreement = 0.5
                    else:
                        agreeing = sum(
                            1
                            for s in steps
                            if (s > 0) == (delta > 0)
                        )
                        agreement = agreeing / len(steps)
                    distance = span_hours / (span_hours + horizon_hours) \
                        if (span_hours + horizon_hours) > 0.0 else 0.0
                    weight = (
                        (refresh_count / (refresh_count + 2.0))
                        * agreement
                        * distance
                    )
                increment = weight * delta
                increment = max(
                    -MAX_INCREMENT_LOGIT,
                    min(MAX_INCREMENT_LOGIT, increment),
                )
                median_logit = logit_pct(rate) + increment
                spread = general_spread(position)

        rows.append(
            {
                "id": trophy["id"],
                "q": quantiles_from(median_logit, spread, levels),
            }
        )

    return {"trophies": rows}


def persistence_fallback(case):
    """Degradation for cases the forecaster cannot process (e.g. an
    out-of-domain timestamp): every quantile equals the trophy's last
    observed rate, mirroring the grader's invalid-case handling."""
    trophies = case["trophies"]
    levels = case.get("levels") or list(DEFAULT_LEVELS)
    history = case.get("history") or []
    rows = []
    for trophy in sorted(trophies, key=lambda t: t["id"]):
        index = trophy["id"] - 1
        last = None
        for read in history:
            rates = read.get("rates") or []
            if 0 <= index < len(rates) and rates[index] is not None:
                last = rates[index]
        value = 0.5 if last is None else round4(last)
        rows.append({"id": trophy["id"], "q": [value] * len(levels)})
    return {"trophies": rows}


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(input_dir) if n.endswith(".in"))
    for name in names:
        case_id = name[:-3]
        with open(
            os.path.join(input_dir, name), "r", encoding="utf-8"
        ) as handle:
            case = json.load(handle)
        try:
            result = forecast_case(case)
        except Exception as exc:  # never crash a whole run on one case
            print(
                "warning: %s: %s; using persistence fallback" % (name, exc),
                file=sys.stderr,
            )
            result = persistence_fallback(case)
        out_path = os.path.join(output_dir, case_id + ".out")
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(result, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
