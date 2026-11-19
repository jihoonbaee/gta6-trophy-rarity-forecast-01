[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/jihoonbaee/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/jihoonbaee/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

# GTA VI Trophy Rarity Forecast — persistence-centered damped trend

Entry for [Forecast how many GTA VI players earn each trophy in week one](https://make.fun/c/gta6-trophy-rarity-forecast-01)
(make.fun competition `gta6-trophy-rarity-forecast-01`).

A deterministic, standard-library-only Python program that forecasts, for
every Grand Theft Auto VI trophy on PlayStation 5, its earn rate on Exophase
at a future target, as five quantiles (0.05, 0.25, 0.5, 0.75, 0.95) of the
logit-scale pinball loss objective. It reads each case file, forecasts from
the case's own history of Exophase page reads, and writes one forecast file
per case. No network access, no randomness.

## Design

- **Persistence default.** The forecast median starts at the last observed
  rate. Any deviation from persistence must be earned by refresh evidence.
- **Damped direct trend.** A recency-weighted log-time trend of the logit
  rate is applied as an anchored increment from the last observation,
  damped by three factors: the number of *distinct* refreshes, directional
  agreement across refresh steps, and extrapolation distance (horizon vs.
  observed history span). Identical repeated polls are collapsed before
  fitting and count as no evidence.
- **Frozen-history prior (scenario, not a law).** When the history is fully
  frozen (no refresh observed), the median blends a dilution scenario
  (3x players, 1.6x earners at a 90-minute reference horizon, scaled by
  horizon) 50/50 with persistence, with a wide spread. The scenario
  parameters are unvalidated design choices.
- **Boundary rules.** Trophies at 100% use a fixed coherent row
  (99.8, 100, 100, 100, 100) from an 80% point mass at 100. Trophies at
  0% are treated as rounded evidence: persistent zeros stay near the
  lower boundary with a narrow spread, while zeros in a tier where
  trophies have started unlocking get a wider spread.
- **Spread.** The maximum of three logit-scale components (random walk,
  weighted trend residual, refresh jump) — not their quadrature sum, since
  the components describe overlapping movement. The spread is an
  uncalibrated construction, not a calibrated uncertainty.

## Files

- `main.py` — the entry program (Python 3.13, standard library only).
- `LICENSE` — MIT.

## Running

```text
python3 main.py
```

Input directory from `MAKEFUN_INPUT_DIR` (default `/input`), output
directory from `MAKEFUN_OUTPUT_DIR` (default `/output`). One `.out` file
per `.in` case. Runtime is far below the 8-second per-case limit
(measured max ~0.03 s/case on the practice cases).

## Verification (local)

- Scorer verified against the RULES worked example (mean pinball loss
  0.403404, exact).
- Deterministic: repeated runs are byte-identical, including a
  grader-style run (`python3 -P -s` from another working directory).
- Format: 55 rows, ids 1–55 exactly once, five non-decreasing quantiles
  per row, file under the 65,536-byte limit.
- Horizon-zero test: at zero extrapolation distance the median equals
  the last observed rate.
- Sensitivity tests: identical reads and polling cadence do not change
  the output; scenario tests cover stable rates, dilution, progression,
  reversal, prolonged staleness, and zero-to-positive transitions.

## Known limitations

- **Frozen-to-first-refresh jump (known defect).** Moving from the
  frozen-history branch (R=0) to the trend branch (R=1) shifts the
  median by a mean of 0.31 logit (max 0.32, measured on the practice
  cases with one small change added). The switch is documented in the
  design; fixing it would require a methodology change, which was
  deliberately not made for this candidate.
- **The frozen-history prior is an unvalidated scenario.** Its growth
  parameters (3x players, 1.6x earners) are design choices, not measured
  quantities, and the same dilution prior is assumed to transfer to any
  future frozen history.
- **Practice cannot validate the trend branch.** Both practice cases
  have flat histories, so the practice score only exercises the
  frozen-history branch, boundary handling, and spread. It cannot
  establish any advantage of the trend engine on moving final history.
- **House AI strength is unknown.** Beating the published persistence /
  trend baselines (≈1.51) does not prove beating the unpublished house
  AI model.
- **Spread is uncalibrated.** Fit residuals measure historical fit, not
  long-horizon predictive uncertainty.

## License

MIT — see `LICENSE`.
