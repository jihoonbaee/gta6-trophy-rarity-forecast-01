# K1g build report

**Fix:** The frozen branch now uses the design's rounded scenario factors (`6.06` for players and `1.34` for earners) in place of the exact aggregate ratios. All nine local verifications were rerun and still pass.

Built `main.py` fresh from the K1g prose brief. All nine local verifications passed on Python 3.12.3. The entry uses the standard library and retains the locked guard thresholds.

## Commands run

Shell commands, from `/tmp/trophy-k1g-build`:

```sh
python3 --version
python3 -B verify_k1g.py
python3 -B verify_k1g.py
python3 -B verify_k1g.py
rm -r -- .verification
python3 -c 'import sys; print(sys.executable)'
```

The first harness attempt hit a stale kit path in the allowed synthetic generator; the path was redirected in memory to the specified kit. The second attempt reached the practice checks, then failed in the harness's exact comparison of floating-point hour differences. Switching that assertion to exact timestamp deltas fixed it. The third attempt completed. No entry code changed between these attempts. The temporary `verify_k1g.py` was removed by patch after verification.

The harness ran the following subprocesses (shell equivalents shown with exact argv and environment; `env -i` describes how the subprocess environment was constructed). The third command used `/tmp/trophy-k1g-build/.verification/in` as its working directory; the others used `/tmp/trophy-k1g-build`.

```sh
env -i MAKEFUN_INPUT_DIR=/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input MAKEFUN_OUTPUT_DIR=/tmp/trophy-k1g-build/.verification/out /usr/bin/python3 /tmp/trophy-k1g-build/main.py
env -i MAKEFUN_INPUT_DIR=/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input MAKEFUN_OUTPUT_DIR=/tmp/trophy-k1g-build/.verification/out2 /usr/bin/python3 /tmp/trophy-k1g-build/main.py
env -i MAKEFUN_INPUT_DIR=/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input MAKEFUN_OUTPUT_DIR=/tmp/trophy-k1g-build/.verification/grader /usr/bin/python3 -P -s /tmp/trophy-k1g-build/main.py
env -i MAKEFUN_INPUT_DIR=/tmp/trophy-k1g-build/.verification/in MAKEFUN_OUTPUT_DIR=/tmp/trophy-k1g-build/.verification/out /usr/bin/python3 /tmp/trophy-k1g-build/main.py
```

The harness loaded `score_local.py` as a library and used the allowed `synth.py` generators. It supplied its own output validator, sensitivity fixtures, curve/decomposition diagnostics, and independent fit arithmetic.

## 1, 2, 3 and 6: Reproducibility, format, scorer and grader invocation

- **1:** Two normal CLI runs produced byte-identical output for each of p00 and p01.
- **2:** Each output was 2,794 bytes, compact JSON with a final newline. Each contained 55 rows, IDs 1 through 55 once each in order, only the required keys, and five finite nondecreasing quantiles in `[0,100]` per row. Quantiles satisfied the decimal and integer rendering requirements.
- **3:** The scorer matched each item in the RULES worked example at six decimals and produced exactly `0.403404` at the grader's scoring precision.
- **6:** The CLI run with `-P -s` from a different directory produced the same bytes for both cases.

## 4: Synthetic scenarios

Mean logit pinball loss; lower is better. Persistence is the documented house persistence forecast with random-walk spread. Curve is a local implementation of the documented house trend comparator: unweighted least squares over the last 24 hours of raw reads, logit rate against log-time, fitted level at target, and random-walk plus residual RMS in quadrature; it falls back to persistence for fewer than three reads. The final-style fixture had exactly 120 reads at 30-minute intervals. All 17 generated sensitivity and edge outputs passed format validation; the batch took 0.1643 seconds locally, including process startup.

| Scenario | K1g | Persistence | Curve | Decomp n | Decomp mean absolute median gap (pp) | Decomp max gap (pp) |
|---|---:|---:|---:|---:|---:|---:|
| Stable | 0.109460401 | 0.099388182 | 0.099433811 | 54 | 0.000000 | 0.0000 |
| Dilution | 0.339070025 | 0.436524282 | 0.124618736 | 54 | 0.115346 | 0.2669 |
| Progression | 0.281332743 | 0.344740861 | 0.117247556 | 54 | 1.300574 | 2.9954 |
| Reversal | 0.245281804 | 0.255806225 | 0.403917123 | 54 | 0.014693 | 0.0352 |
| Staleness | 0.111232290 | 0.026637913 | 0.028546870 | 54 | 0.001041 | 0.0021 |
| Zero to positive | 0.129204565 | 0.148988097 | 0.130060719 | 51 | 3.879873 | 99.4070 |
| Final-style | 0.246239009 | 0.275244338 | 0.237104489 | 54 | 0.045339 | 0.1092 |

Decomposition is diagnostic only: collapse repeats, separately fit log players and log implied earners against log-time on matching observations with 12-hour weights, omit points with earners below 0.05, and use the slope difference to extrapolate from the last rate. Differences above are against K1g medians, for ordinary positive-rate trophies with enough points. These scenarios test mechanics and sensitivity; they do not validate forecast accuracy on real data.

Empty and all-nonpositive-player histories both returned median 1%. The single-rate fixture kept that trophy at its observed median and returned 0.5% for the all-null trophy. In the unlock fixture the persistent bronze zeros (IDs 5 and 6, with same-tier unlocks) had q95 of 0.0518%, versus 0.0228% for the persistent gold zero (ID 7, without same-tier unlocks).

## 5: Sensitivity

- **5a:** Appending a later identical read to the stable case left output byte-identical.
- **5c:** Reducing the staleness case from 13 to 4 polls while keeping both distinct states and their first timestamps left output byte-identical.
- **5d:** At truth 95%, the fixed `[99.8,100,100,100,100]` row costs **5.126700364744** mean pinball (or 0.093212733904 of a 55-trophy mean). The same row costs 0.059952685424 at truth 100%. An all-100 row costs 6.265801387808 at 95% and zero at 100%.

### 5b: R = 0 to R = 1 discontinuity

Appended one read to p00 one second before its checkpoint, retaining the same players and all rates except ID 3, increased from 1.25% to 1.26%. The target and declared horizon were unchanged. The new read moved the whole case from the frozen prior to the trend branch. All 55 medians and exact changes at output precision are below. Changes are in percentage points; the largest was **+1.3809 pp for unchanged ID 20**. All 54 ordinary medians increased; the boundary trophy was unchanged.

| ID | R=0 median | R=1 median | Change (pp) |
|---:|---:|---:|---:|
| 1 | 0.2033 | 0.6300 | +0.4267 |
| 2 | 100.0000 | 100.0000 | +0.0000 |
| 3 | 0.4035 | 1.2602 | +0.8567 |
| 4 | 0.3551 | 1.1000 | +0.7449 |
| 5 | 0.3551 | 1.1000 | +0.7449 |
| 6 | 0.3551 | 1.1000 | +0.7449 |
| 7 | 0.3551 | 1.1000 | +0.7449 |
| 8 | 0.3551 | 1.1000 | +0.7449 |
| 9 | 0.3551 | 1.1000 | +0.7449 |
| 10 | 0.3551 | 1.1000 | +0.7449 |
| 11 | 0.3551 | 1.1000 | +0.7449 |
| 12 | 0.3551 | 1.1000 | +0.7449 |
| 13 | 0.3551 | 1.1000 | +0.7449 |
| 14 | 0.2033 | 0.6300 | +0.4267 |
| 15 | 0.2033 | 0.6300 | +0.4267 |
| 16 | 0.2517 | 0.7800 | +0.5283 |
| 17 | 0.2033 | 0.6300 | +0.4267 |
| 18 | 0.2033 | 0.6300 | +0.4267 |
| 19 | 0.2517 | 0.7800 | +0.5283 |
| 20 | 0.6591 | 2.0400 | +1.3809 |
| 21 | 0.3034 | 0.9400 | +0.6366 |
| 22 | 0.2517 | 0.7800 | +0.5283 |
| 23 | 0.2517 | 0.7800 | +0.5283 |
| 24 | 0.2517 | 0.7800 | +0.5283 |
| 25 | 0.2033 | 0.6300 | +0.4267 |
| 26 | 0.2033 | 0.6300 | +0.4267 |
| 27 | 0.2517 | 0.7800 | +0.5283 |
| 28 | 0.2033 | 0.6300 | +0.4267 |
| 29 | 0.2517 | 0.7800 | +0.5283 |
| 30 | 0.2033 | 0.6300 | +0.4267 |
| 31 | 0.2033 | 0.6300 | +0.4267 |
| 32 | 0.2033 | 0.6300 | +0.4267 |
| 33 | 0.3034 | 0.9400 | +0.6366 |
| 34 | 0.2517 | 0.7800 | +0.5283 |
| 35 | 0.4035 | 1.2500 | +0.8465 |
| 36 | 0.2517 | 0.7800 | +0.5283 |
| 37 | 0.3034 | 0.9400 | +0.6366 |
| 38 | 0.5070 | 1.5700 | +1.0630 |
| 39 | 0.3034 | 0.9400 | +0.6366 |
| 40 | 0.2517 | 0.7800 | +0.5283 |
| 41 | 0.3034 | 0.9400 | +0.6366 |
| 42 | 0.2517 | 0.7800 | +0.5283 |
| 43 | 0.2517 | 0.7800 | +0.5283 |
| 44 | 0.3034 | 0.9400 | +0.6366 |
| 45 | 0.2517 | 0.7800 | +0.5283 |
| 46 | 0.2517 | 0.7800 | +0.5283 |
| 47 | 0.2517 | 0.7800 | +0.5283 |
| 48 | 0.2517 | 0.7800 | +0.5283 |
| 49 | 0.2517 | 0.7800 | +0.5283 |
| 50 | 0.2517 | 0.7800 | +0.5283 |
| 51 | 0.2517 | 0.7800 | +0.5283 |
| 52 | 0.2517 | 0.7800 | +0.5283 |
| 53 | 0.3034 | 0.9400 | +0.6366 |
| 54 | 0.2517 | 0.7800 | +0.5283 |
| 55 | 0.2517 | 0.7800 | +0.5283 |

## 7: Zero horizon

In both fixtures the checkpoint, target, and last distinct observation shared a timestamp and `horizon_minutes` was 0. The CLI matched the rounded last rates for all **54 ordinary trophies** in each of the moving and frozen fixtures. ID 2's boundary row still had median 100 in both.

## 8: Frozen factors and manual blend

At 90 minutes, the player factor is exactly `6.06` and the non-universal earner factor is exactly `1.34`. The rate multiplier is `1.34/6.06`, approximately `0.221122112211`. Practice declares a 90-minute checkpoint horizon, but collapsing to the first repeated read gives effective target gaps of 279.17733333 and 309.17733333 minutes. Both give the same capped factors as 90 minutes.

Hand calculation from each last rate `r`, common to p00 and p01: `s = r * (1.34/6.06)`, `L(x) = ln(x/(100-x))` for these unclamped rates, `m = 0.75 L(s) + 0.25 L(r)`, and rate `= 100/(1+exp(-m))`.

| ID | Last % | Scenario % | L(s) | L(r) | 0.75 L(s) + 0.25 L(r) | Inverse % | CLI % |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 1.25 | 0.2764026403 | -5.8882989674 | -4.3694478525 | -5.5085861887 | 0.4035480772 | 0.4035 |
| 4 | 1.10 | 0.2432343234 | -6.0164648861 | -4.4987990588 | -5.6370484293 | 0.3550717916 | 0.3551 |
| 20 | 2.04 | 0.4510891089 | -5.3967394684 | -3.8716094242 | -5.0154569574 | 0.6590871820 | 0.6591 |

The independent calculation with spread 1.0 also reproduced all five quantiles for each of these rows in both files.

## 9: Guard and kink

Synthetic fixture: 21 distinct reads at `h = 0, 3, ..., 60`, target `h = 66`. For IDs 3 and 4 the generator rounded the inverse logit of `a + b * (1.25 ln(1 + min(h,54)) - 0.145 max(0,h-54))` to two decimals, with `(a,b) = (-4,1)` and `(-5,0.8)` respectively. Both rates rose for 54 hours, then fell sharply for 6 hours. Players were `round(100000 exp(0.03 h))` for the late-reversal case and `round(100000 exp(0.03 min(h,36)))` for the kink case. The trophy paths are identical between fixtures so the comparison isolates the kink.

Manual slope calculation, using the rounded inputs and independently tabulating the normal equations: `x = ln(1+h)`, `y = logit(rate)`, `w = 2^((h-60)/half_life)`. Below, `W=Σw`, `X=Σwx`, `Y=Σwy`, `XX=Σwx²`, `XY=Σwxy`. Substitute in `(W*XY-X*Y)/(W*XX-X*X)` using unrounded totals.

| ID | Half-life | W | X | Y | XX | XY | Slope | RMS residual |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 3h | 1.99999905 | 8.11477347 | 0.89321365 | 32.93795133 | 3.58633536 | -2.870493377 | 0.244799433 |
| 3 | 12h | 6.12005059 | 23.04934615 | 2.91044576 | 88.35989460 | 12.43186680 | 0.947877588 | 0.347504744 |
| 4 | 3h | 1.99999905 | 8.11477347 | -2.88491451 | 32.93795133 | -11.73541631 | -2.294358034 | 0.195688980 |
| 4 | 12h | 6.12005059 | 23.04934615 | -8.68736315 | 88.35989460 | -31.54147662 | 0.758595120 | 0.277865141 |

To calculate each median, multiply the slope by `ln(67/61)`, then by `(20/22)*(matches/20)*(60/66)`. There are 18 matches for a positive delta and 2 for a negative one. The resulting shifts are below the 1.0 cap. Add the shift to the logit of the last rate (53.47% for ID 3, 15.60% for ID 4) and invert.

| ID | slope3/slope12 | 3h shift | 12h shift | 3h median | 12h median | Reversal CLI | Kink CLI |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | -3.028337639 | -0.022256704 | +0.066145311 | 52.9159 | 55.1113 | 55.1113 | 52.9159 |
| 4 | -3.024482987 | -0.017789571 | +0.052936698 | 15.3672 | 16.3097 | 16.3097 | 15.3672 |

| Case | Distinct / raw reads | g_q1 (per hour) | g_q4 (per hour) | Kink | Guard fires |
|---|---:|---:|---:|---|---:|
| Late reversal | 21 / 21 | 0.0300000445 | 0.0299999300 | No | 2 (IDs 3, 4) |
| Kink | 21 / 21 | 0.0300000445 | 0.0000000000 | Yes | 0 |
| p00 | 1 / 7 | n/a | n/a | No | 0 |
| p01 | 1 / 8 | n/a | n/a | No | 0 |

Quartile slopes used unweighted OLS on raw hours and log players, first and last five distinct reads. The late-reversal slopes and ratios satisfy the guard, and the CLI matches the independently calculated slow medians. In the kink fixture the last quartile has less than half the first quartile's growth, blocking the guard despite the same strong slow slopes and negative ratios. Practice stays in the frozen branch. The harness also verified that `|slope12| = 0.1` and ratio `= 0.3` do not fire, and that 11 reads do not enable kink detection. No thresholds were retuned.

## Practice reconstruction (diagnostic only)

Both practice cases gave the same numbers. A assigns the 103 additional non-universal earners proportional to old counts; B uses squared counts; C uses proportional counts only for rates at least 1.10%. These are conditional allocations, neither verified answers nor bounds on the truth. A match to the reported 1.51 baseline would not validate an allocation. Scorer validation comes from the worked example in verification 3. The prior and the reconstructions share the same refresh aggregates, so this is not an independent accuracy test.

| Case | Allocation | Persistence | K1g |
|---|---|---:|---:|
| p00 | A | 1.400957683 | 0.272849898 |
| p00 | B | 1.422174128 | 0.277093187 |
| p00 | C | 1.517288965 | 0.296338396 |
| p01 | A | 1.400957683 | 0.272849898 |
| p01 | B | 1.422174128 | 0.277093187 |
| p01 | C | 1.517288965 | 0.296338396 |

## Remaining defects and verification limits

- The `R=0` to `R=1` branch change has a material discontinuity: a +0.01 pp input change to one trophy moved all ordinary medians, including a +1.3809 pp jump for an unchanged trophy. This is a remaining model defect specified by the design.
- The fixed universal-trophy row pays high loss if universality fails. The symmetric logit spread remains uncalibrated and does not capture delayed unlocks or one-sided dilution. The frozen prior rests on one observed refresh.
- Quantized flat steps can trip the guard, and a kink can block it during a genuine late reversal. The synthetic guard checks establish that the rules execute as specified; they do not establish which choice is more accurate on final data.
- No implementation deviation was found in the tested cases. Byte identity against the prior candidate is unverified. The `-P -s` test used the local Python 3.12.3 interpreter; a direct Python 3.13 grader test and real final or house-model comparisons were not established by this build.
