# Build Report: K1h

## Commands and setup

The practice kit is at `/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit`.

Commands run (working directory `/tmp/trophy-k1h-fix`, except where noted):

```sh
mkdir -p run1 run2 && MAKEFUN_INPUT_DIR="/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input" MAKEFUN_OUTPUT_DIR="/tmp/trophy-k1h-fix/run1" python3 main.py && MAKEFUN_INPUT_DIR="/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input" MAKEFUN_OUTPUT_DIR="/tmp/trophy-k1h-fix/run2" python3 main.py && cmp -s run1/p00.out run2/p00.out && cmp -s run1/p01.out run2/p01.out && wc -c run1/p00.out run1/p01.out && printf '%s\n' 'practice byte comparison: identical'
mkdir -p out && MAKEFUN_INPUT_DIR="/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input" MAKEFUN_OUTPUT_DIR="/tmp/trophy-k1h-fix/out" python3 main.py && python3 verify_work.py
python3 verify_work.py
```

The first run of `verify_work.py` failed in its late-reversal fixture: the `-0.30 * (h - 9)` reversal made both fast and slow slopes negative, so the intended positive-slow-trend guard precondition was absent. I changed only this verification fixture to `-0.18 * (h - 9)` and reran it successfully. Entry files were not modified.

Grader-style command, run with working directory `/tmp`:

```sh
mkdir -p /tmp/trophy-k1h-grader-out && MAKEFUN_INPUT_DIR="/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input" MAKEFUN_OUTPUT_DIR="/tmp/trophy-k1h-grader-out" python3 /tmp/trophy-k1h-fix/main.py -P -s && cmp -s /tmp/trophy-k1h-fix/run1/p00.out /tmp/trophy-k1h-grader-out/p00.out && cmp -s /tmp/trophy-k1h-fix/run1/p01.out /tmp/trophy-k1h-grader-out/p01.out && printf '%s\n' 'grader-style -P -s: outputs identical to practice run'
```

Its output was `grader-style -P -s: outputs identical to practice run`.

I also ran `python3 /home/hatch/workspace/makefun/gta6-trophy-rarity-devtools/score_local.py`. It printed `worked example OK: mean pinball 0.403404` and its boundary diagnostic, then failed loading practice cases because the tool's default `Path.home()` kit location resolves to a nonexistent isolated-environment path. The verifier loads this same permitted tool and sets `scorer.KIT` and `scorer.ENTRY` explicitly; its worked example and reconstructions below completed successfully.

## Verifications

1. **Determinism:** Ran both practice inputs twice into separate output directories. `cmp` passed for both files. Output sizes were 2,794 bytes each, 5,588 bytes total. The grader-style run also matched the first run byte-for-byte.

2. **Output format:** Both outputs parsed and validated: exactly 55 rows, IDs 1 through 55 once each, five finite ordered quantiles in [0, 100], and under 65,536 bytes. `verify_work.py` reported `format p00: rows=55 ids=1..55 bytes=2794 OK` and the same for p01.

3. **Scorer worked example:** Passed at exactly the required displayed value: `worked example OK: mean pinball 0.403404`.

4. **Synthetic scenarios:** The verifier reported the following losses, each separately against the generated truth and the two stated comparators. These are synthetic logic/sensitivity diagnostics, not forecasting-accuracy evidence.

   | Scenario | Distinct reads | Kink | Guard count | K1h loss | Persistence loss | 24h OLS loss |
   |---|---:|---|---:|---:|---:|---:|
   | stable | 13 | false | 0 | 0.076949 | 0.099428 | 0.099428 |
   | dilution | 13 | false | 0 | 0.315776 | 0.320760 | 0.264170 |
   | progression | 13 | false | 0 | 0.222815 | 0.224296 | 0.183805 |
   | reversal | 13 | false | 0 | 4.708833 | 4.556402 | 4.965433 |
   | zero | 13 | false | 0 | 0.194966 | 0.233937 | 0.181609 |
   | staleness | 2 | false | 0 | 0.111778 | 0.027196 | 0.027196 |

   The 120-read final-style case ran and validated as 55 rows. Synthetic determinism and edge-case output checks passed: `determinism OK on synthetic + edge cases`.

5. **Sensitivity:** (a) Adding an identical read left the serialized forecast unchanged. (b) Adding one small distinct read to frozen p00 measured median jumps in percentage points for IDs 1–55, in order: `+0.4369, +0.0000, +0.8567, +0.7551, +0.7551, +0.7551, +0.7551, +0.7551, +0.7551, +0.7551, +0.7551, +0.7551, +0.7551, +0.4369, +0.4369, +0.5385, +0.4369, +0.4369, +0.5385, +1.3911, +0.6468, +0.5385, +0.5385, +0.5385, +0.4369, +0.4369, +0.5385, +0.4369, +0.5385, +0.4369, +0.4369, +0.4369, +0.6468, +0.5385, +0.8567, +0.5385, +0.6468, +1.0732, +0.6468, +0.5385, +0.6468, +0.5385, +0.5385, +0.6468, +0.5385, +0.5385, +0.5385, +0.5385, +0.5385, +0.5385, +0.5385, +0.5385, +0.6468, +0.5385, +0.5385`. This is a measurable R=0 to R=1 discontinuity; the largest positive shift was +1.3911 points (ID 20). (c) Changing polling cadence while keeping distinct refreshes the same produced identical output. (d) The fixed 100% row scored against 95% truth costs `5.126700365` mean loss per five quantiles.

6. **Grader-style run:** `python3 /tmp/trophy-k1h-fix/main.py -P -s` succeeded from `/tmp`; both outputs were byte-identical to the practice run.

7. **Zero horizon:** Trend and frozen cases passed: ordinary-rate medians equal the last observed rates to four decimal places. Output: `zero horizon: exact-to-4dp medians for ordinary rates, trend and frozen`.

8. **Frozen branch:** On both practice cases, factors were exactly players `6.06` and earners `1.34`; reported diagnostics show one distinct read. The hand calculations and output medians for three trophies were:

   | Case | ID | Last rate | Manual weighted-logit median | Output median |
   |---|---:|---:|---:|---:|
   | p00 and p01 | 3 | 1.25 | 0.40354808 | 0.40350000 |
   | p00 and p01 | 4 | 1.10 | 0.35507179 | 0.35510000 |
   | p00 and p01 | 5 | 1.10 | 0.35507179 | 0.35510000 |

   Difference is the required output rounding to four decimals.

9. **Late-reversal guard and kink block:** In the corrected late-reversal synthetic case, guard fired for 54 trophies and no kink was detected. Hand-checked trophies:

   | ID | slope3 | slope12 | ratio | Guard | Manual 12h median | Output median |
   |---:|---:|---:|---:|---|---:|---:|
   | 3 | -0.289000 | 0.135160 | -2.138206 | true | 1.939914 | 1.939900 |
   | 4 | -0.289790 | 0.134785 | -2.150012 | true | 1.708729 | 1.708700 |

   The kink synthetic detected a kink with `g_q1=0.150134`, `g_q4=0.004124`; guard count was 0 and IDs 3 and 4 selected the 3h slopes (`-0.289000` and `-0.289790`). Practice p00 and p01 each had `kink=False` and `guards=0`.

10. **K1h spread scale:** Stable, non-kink, 13-read case used factor 0.7. For IDs 3, 4, and 5 raw spread was 0.550000, scaled spread 0.385000; recovered from final quantiles: 0.384996, 0.384986, 0.384986. Medians were 1.25, 1.1, and 1.1, unchanged by scaling. The kink case used factor 1.0; for IDs 3 and 4 raw/recovered spreads were 0.550000/0.550008 and 0.550000/0.549998. The 11-distinct-read kink-shaped short case reported `detector_kink=False factor=1.0`, as the detector is unavailable below 12 reads. Practice p00/p01 each used factor 1.0 with one distinct read.

## Full verifier output

```text
practice p00: distinct=1 kink=False scale=1.0 guards=0
 frozen factors players=6.06 earners=1.34
 blend p00 id=3: rate=1.25 manual=0.40354808 output=0.40350000
 blend p00 id=4: rate=1.1 manual=0.35507179 output=0.35510000
 blend p00 id=5: rate=1.1 manual=0.35507179 output=0.35510000
practice p01: distinct=1 kink=False scale=1.0 guards=0
 frozen factors players=6.06 earners=1.34
 blend p01 id=3: rate=1.25 manual=0.40354808 output=0.40350000
 blend p01 id=4: rate=1.1 manual=0.35507179 output=0.35510000
 blend p01 id=5: rate=1.1 manual=0.35507179 output=0.35510000
worked example OK: mean pinball 0.403404
reconstruction p00 A: loss=0.272849898
reconstruction p00 B: loss=0.277093187
reconstruction p00 C: loss=0.296338396
reconstruction p01 A: loss=0.272849898
reconstruction p01 B: loss=0.277093187
reconstruction p01 C: loss=0.296338396
scenario stable: reads=13 kink=False guard_count=0 loss_k1h=0.076949 loss_persistence=0.099428 loss_24h_OLS=0.099428
scenario dilution: reads=13 kink=False guard_count=0 loss_k1h=0.315776 loss_persistence=0.320760 loss_24h_OLS=0.264170
scenario progression: reads=13 kink=False guard_count=0 loss_k1h=0.222815 loss_persistence=0.224296 loss_24h_OLS=0.183805
scenario reversal: reads=13 kink=False guard_count=0 loss_k1h=4.708833 loss_persistence=4.556402 loss_24h_OLS=4.965433
scenario zero: reads=13 kink=False guard_count=0 loss_k1h=0.194966 loss_persistence=0.233937 loss_24h_OLS=0.181609
scenario staleness: reads=2 kink=False guard_count=0 loss_k1h=0.111778 loss_persistence=0.027196 loss_24h_OLS=0.027196
final-style 120 reads: valid, 55 rows
sensitivity 5a: one identical read added; byte-serialized forecast unchanged
sensitivity 5b median jumps (percentage points), id=jump: 1=+0.4369, 2=+0.0000, 3=+0.8567, 4=+0.7551, 5=+0.7551, 6=+0.7551, 7=+0.7551, 8=+0.7551, 9=+0.7551, 10=+0.7551, 11=+0.7551, 12=+0.7551, 13=+0.7551, 14=+0.4369, 15=+0.4369, 16=+0.5385, 17=+0.4369, 18=+0.4369, 19=+0.5385, 20=+1.3911, 21=+0.6468, 22=+0.5385, 23=+0.5385, 24=+0.5385, 25=+0.4369, 26=+0.4369, 27=+0.5385, 28=+0.4369, 29=+0.5385, 30=+0.4369, 31=+0.4369, 32=+0.4369, 33=+0.6468, 34=+0.5385, 35=+0.8567, 36=+0.5385, 37=+0.6468, 38=+1.0732, 39=+0.6468, 40=+0.5385, 41=+0.6468, 42=+0.5385, 43=+0.5385, 44=+0.6468, 45=+0.5385, 46=+0.5385, 47=+0.5385, 48=+0.5385, 49=+0.5385, 50=+0.5385, 51=+0.5385, 52=+0.5385, 53=+0.6468, 54=+0.5385, 55=+0.5385
sensitivity 5c: same distinct refreshes, extra polls; output identical
sensitivity 5d: 100%-fixed row scored against truth 95% costs 5.126700365 mean per five quantiles
zero horizon: exact-to-4dp medians for ordinary rates, trend and frozen
guard reversal id=3: slope3=-0.289000 slope12=0.135160 ratio=-2.138206 fires=True median_manual12=1.939914 output=1.939900
guard reversal id=4: slope3=-0.289790 slope12=0.134785 ratio=-2.150012 fires=True median_manual12=1.708729 output=1.708700
late-reversal guard fires=54; kink=False
kink case: detected=True g_q1=0.150134 g_q4=0.004124; guard fires=0
 kink id=3: slope3=-0.289000 slope12=0.135160 selected=3h guard=False
 kink id=4: slope3=-0.289790 slope12=0.134785 selected=3h guard=False
scale stable id=3: raw=0.550000 x0.7=0.385000 recovered=0.384996 median=1.25
scale stable id=4: raw=0.550000 x0.7=0.385000 recovered=0.384986 median=1.1
scale stable id=5: raw=0.550000 x0.7=0.385000 recovered=0.384986 median=1.1
scale kink id=3: factor=1.0 raw=0.550000 recovered=0.550008
scale kink id=4: factor=1.0 raw=0.550000 recovered=0.549998
scale short case: distinct=11 detector_kink=False factor=1.0
format p00: rows=55 ids=1..55 bytes=2794 OK
format p01: rows=55 ids=1..55 bytes=2794 OK
```

## Practice reconstructions (diagnostic only)

The A/B/C losses, printed by the verifier, are not ground truth and do not establish forecast accuracy:

| Case | A | B | C |
|---|---:|---:|---:|
| p00 | 0.272849898 | 0.277093187 | 0.296338396 |
| p01 | 0.272849898 | 0.277093187 | 0.296338396 |

## Remaining defects and deviations

- The one-small-refresh sensitivity shows a nonzero branch transition; its largest measured median change is +1.3911 percentage points (ID 20). This is the measured behavior, not concealed.
- The original late-reversal test fixture did not meet its own positive slow-slope precondition. The test-only fixture was adjusted from a `-0.30` to `-0.18` hourly reversal coefficient; with that change it verifies fallback on 54 trophies and manual fallback medians on two trophies.
- The standalone `score_local.py` command cannot locate the kit using its default path in this isolated environment. Its worked example passed, and the verifier's explicit path setup enabled the practice reconstructions. This is an environment/tool-path limitation, not an entry failure.
- Synthetic losses are scenario diagnostics only. No real final history or final answer was available to validate accuracy, and the frozen practice reconstruction is not an independent holdout.
