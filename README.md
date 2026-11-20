# K1h GTA VI trophy rarity forecast

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/jihoonbaee/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/jihoonbaee/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

`main.py` forecasts five earn-rate quantiles for each trophy from distinct
Exophase observations. It implements the K1h prose design: guarded 3-hour
and 12-hour weighted logit trends, a calibrated frozen-history scenario,
boundary rules, and conditional spread scaling when at least 12 distinct
reads show no players-growth kink.

Run with Python 3.13 and the standard library:

```sh
MAKEFUN_INPUT_DIR=/path/to/input MAKEFUN_OUTPUT_DIR=/path/to/output python3 main.py
```

The defaults are `/input` and `/output`. Every `*.in` file is processed in
filename order and produces a compact JSON `.out` file with a final newline.
The program uses no network or randomness. See `BUILD-REPORT.md` for local
verification results and known forecasting limitations.
