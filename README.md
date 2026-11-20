[![make.fun](https://make.fun/badge.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge-rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge-reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

V3 forecasts five trophy earn-rate quantiles using distinct page refreshes,
a damped logit trend, and a calibrated dilution scenario for frozen histories.
Frozen scenarios use player/earner factors 6.06/1.34 at 90 minutes and a
0.75/0.25 scenario/persistence logit blend. Boundary and zero-rate rules
follow the V3 design brief. These are forecasting assumptions, not evidence
of final accuracy; practice calibration uses the same observed refresh.

Run with Python 3.13 and the standard library:

```sh
MAKEFUN_INPUT_DIR=/path/to/input MAKEFUN_OUTPUT_DIR=/path/to/output python3 main.py
```

Defaults are `/input` and `/output`. Each `.in` JSON case produces a compact
`.out` JSON forecast of the same filename stem, in sorted filename order.
The program uses no network or randomness. See BUILD-REPORT.md for verification.
