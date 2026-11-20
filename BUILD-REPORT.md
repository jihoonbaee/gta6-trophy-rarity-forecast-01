# V3 build report

Built fresh from `/home/hatch/workspace/makefun/gta6-trophy-rarity-v3/DESAIN-BRIEF-V3.md` on 20 November 2026. The entry uses only Python's standard library, with no network or randomness. The deliverables are `main.py`, `README.md` (with all three exact requested badges), and this report. `verify.py` and `.verification/` are local reproducibility evidence, not dependencies of the entry.

All eight mandatory verification groups completed successfully. The large R=0 → R=1 discontinuity remains a design defect: ordinary trophy output medians jump by **1.1475685080005587–1.1516426136719735 logits** in the specified small-change experiment. This report does not claim final forecasting accuracy.

## Sources and execution scope

Read only the V3 prose brief, the authorized kit's RULES and p00/p01, the three explicitly authorized devtools, and files in this workdir. No previous entry or previous brief was read. No starter README was found by the permitted filename search, so the three badge lines supplied by the user were used exactly. No web browsing, API use, bundling, entry check, submission, GitHub operation, or credential access occurred. All generated files are inside `/tmp/trophy-v3-build`.

The local harness executes the authorized devtool source in memory. It redirects the synthetic generator's obsolete kit input path to the authorized kit27 p00 and redirects test_synth.py's import-time work directory into this workdir. It imports only the scorer functions; it never runs the scorer's old entry-loading main function. No external devtool was modified. The supplied final-style generator was used as written: it produces 120 reads 30 minutes apart, with R=119 because player counts change at every read despite the generator's comment about step patterns. The additional seeded final-like generator in test_synth.py also ran; its randomness is confined to verification and never enters main.py.

## Exact commands

The only top-level shell command was the following, run twice from `/tmp/trophy-v3-build` (both executions exited 0). The second run followed additional assertions for rounding, spread, factor caps, nulls, zeros, and 30-minute final-style spacing; entry code was unchanged between runs.

```sh
python3 -B verify.py
```

Each invocation made these exact five subprocess calls. The first four used cwd `/tmp/trophy-v3-build`; the last used cwd `/tmp/trophy-v3-build/.verification`. Environment was inherited with `PYTHONDONTWRITEBYTECODE=1` and the two explicit directory overrides below. No environment values were displayed or inspected for secrets.

```sh
MAKEFUN_INPUT_DIR=/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input MAKEFUN_OUTPUT_DIR=/tmp/trophy-v3-build/.verification/practice1 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /tmp/trophy-v3-build/main.py
MAKEFUN_INPUT_DIR=/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input MAKEFUN_OUTPUT_DIR=/tmp/trophy-v3-build/.verification/practice2 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /tmp/trophy-v3-build/main.py
MAKEFUN_INPUT_DIR=/tmp/trophy-v3-build/.verification/generated MAKEFUN_OUTPUT_DIR=/tmp/trophy-v3-build/.verification/synthetic1 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /tmp/trophy-v3-build/main.py
MAKEFUN_INPUT_DIR=/tmp/trophy-v3-build/.verification/generated MAKEFUN_OUTPUT_DIR=/tmp/trophy-v3-build/.verification/synthetic2 PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /tmp/trophy-v3-build/main.py
MAKEFUN_INPUT_DIR=/home/hatch/workspace/makefun/kits/gta6-trophy-rarity-forecast-01-kit27/gta6-trophy-rarity-forecast-01-kit/input MAKEFUN_OUTPUT_DIR=/tmp/trophy-v3-build/.verification/grader PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -P -s /tmp/trophy-v3-build/main.py
```

Other actions used file read/search and apply_patch tools, not shell commands. Full subprocess argv/cwd records and numerical evidence are in `.verification/results.json`; `verify.py` contains all in-process assertions and diagnostic definitions.

## 1. Practice determinism

PASS. p00 and p01 each ran twice, and both pairs were byte-identical. Both cases also happen to produce identical forecasts because their frozen scenarios hit the same caps.

| Case | Output bytes | SHA-256 (both runs) |
| --- | ---: | --- |
| p00 | 2794 | 9ba183b64897232ccbd31628f35094ec26d04944edad7d6e08876e28b6390c70 |
| p01 | 2794 | 9ba183b64897232ccbd31628f35094ec26d04944edad7d6e08876e28b6390c70 |

## 2. Format

PASS. Each practice output has exactly the top-level key `trophies`, exactly 55 rows, IDs 1–55 once each in ascending order, exactly `id` and `q` per row, five finite non-decreasing numbers in [0,100], and file size strictly below 65,536 bytes. JSON is compact and newline-terminated. Every generated output was also validated and compared byte-for-byte across two runs. The generated batch has 13 cases: the seven requested scenarios, the devtool's two edge cases and seeded final-like case, single/missing-rate history, empty history, and no positive tracked players.

## 3. Scorer worked example and conditional practice diagnostics

PASS. The RULES worked example gives raw floating-point mean **0.40340433785720897**, which is **0.403404 exactly at the rules' six-decimal score precision**. Both sets of five published item losses agree within half a unit in their last printed decimal. No artificial truncation of the raw mean was used. This worked example validates the scorer formula.

Practice A/B/C are conditional reconstructions, not known answers or bounds on truth. Results below apply separately and identically to p00 and p01:

| Reconstruction | V3 loss | House persistence with its random-walk spread |
| --- | ---: | ---: |
| A | 0.27284989810311067 | 1.4009576828005517 |
| B | 0.2770931871147506 | 1.4221741278587539 |
| C | 0.29633839634139436 | 1.5172889649782626 |

Matching an aggregate baseline near 1.51 does not identify the correct answer allocation. Differences from 1.40/1.42/1.52 do not disprove the scorer. Calibration and these reconstructions use the same one observed refresh, so practice improvement is near-circular and not independent forecasting evidence.

## 4. Synthetic scenarios and decomposition diagnostic

PASS as sensitivity/logic executions. These results are not validation against real future data. Persistence-point repeats each last rate five times. House persistence uses the devtool's documented random-walk spread. The trend comparator is an **undamped, last-rate-anchored weighted direct logit regression** on distinct observations, using the same 12-hour weights and log-time mapping as the candidate. It reuses candidate boundary/zero behavior and estimates candidate spread from its rounded q25/q75; this introduces a small rounding discrepancy. It is a documented comparator, not a claim to reproduce the house curve baseline.

| Scenario | Reads / R | V3 | Persistence point | House persistence | Undamped direct trend | Log players/earners diagnostic |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Stable | 13 / 12 | 0.109460401 | 0 | 0.099388182 | 0.109454096 | 0.109454096 |
| Dilution | 13 / 12 | 0.339871697 | 0.782475319 | 0.436524282 | 0.137619446 | 0.137011957 |
| Progression | 13 / 12 | 0.282999096 | 0.629502950 | 0.344740861 | 0.119777385 | 0.118296386 |
| Reversal | 13 / 12 | 0.251124983 | 0.481278556 | 0.255806225 | 0.235812680 | 0.235791014 |
| Staleness | 13 / 1 | 0.111232290 | 0.008954339 | 0.026637913 | 0.111118107 | 0.111118107 |
| Zero-to-positive | 13 / 12 | 0.131816367 | 0.069200824 | 0.148988097 | 0.135728276 | 0.528293319 |
| Final-style | 120 / 119 | 0.241618460 | 0.319613437 | 0.275244338 | 0.241513482 | 0.241407511 |

The candidate loses to point persistence on stable, staleness, and zero-to-positive. The trend comparator does better on several smooth growth scenarios. These are reported without changing the specified design.

Decomposition exists only in verify.py: fit log players and log earners separately with the same x and weights, subtract their extrapolated changes, apply that rate ratio to the last observed rate, then convert to logit. Earners below 0.05 are excluded. Candidate median differences are stored for **every trophy in every scenario** in `.verification/results.json`, under `decomposition_median_minus_candidate_pp`. Examples: final-style IDs 3/20/55 differ by −0.0649/−0.1002/−0.0380 percentage points; staleness id20 differs by −0.0021; zero-to-positive ids3/4 differ by +98.6146/+99.4746. The last two expose severe undamped extrapolation saturation in this diagnostic. It is not part of main.py.

Latest local runtime: 0.067658608 seconds for the two practice cases combined, and 0.118794340 seconds for all 13 generated cases combined, including interpreter startup. These are local timings, not grader measurements.

## 5. Sensitivity

**5a identical read:** PASS, exactly unchanged forecast objects after appending an identical read with a later timestamp, tested on practice, dilution, and final-style.

**5b R=0 → R=1:** Starting with p00, increase every ordinary trophy's rate in its final raw read by **0.01 percentage point**, keep player count and universal rate unchanged, and keep timestamps/checkpoint/target fixed. This creates exactly one distinct refresh. The table gives actual rounded output medians and the signed logit difference computed from those output medians. All differences are positive, so signed differences also equal jump magnitudes. Decimal logit values below preserve the recorded Python floating-point results. The change includes the intentional tiny observed rate increment as well as the branch switch.

| Trophy ID | Frozen median % | R=1 median % | Change pp | Change logit |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 2 | 100 | 100 | 0 | 0 |
| 3 | 0.4035 | 1.2603 | 0.8568 | 1.1475685080005587 |
| 4 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 5 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 6 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 7 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 8 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 9 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 10 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 11 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 12 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 13 | 0.3551 | 1.1103 | 0.7552 | 1.1475938667298218 |
| 14 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 15 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 16 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 17 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 18 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 19 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 20 | 0.6591 | 2.0503 | 1.3912 | 1.1489694226644134 |
| 21 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 22 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 23 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 24 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 25 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 26 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 27 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 28 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 29 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 30 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 31 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 32 | 0.2033 | 0.6403 | 0.4370 | 1.1516426136719735 |
| 33 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 34 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 35 | 0.4035 | 1.2603 | 0.8568 | 1.1475685080005587 |
| 36 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 37 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 38 | 0.5070 | 1.5803 | 1.0733 | 1.1477052804825831 |
| 39 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 40 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 41 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 42 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 43 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 44 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 45 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 46 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 47 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 48 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 49 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 50 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 51 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 52 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 53 | 0.3034 | 0.9503 | 0.6469 | 1.1482354870155866 |
| 54 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |
| 55 | 0.2517 | 0.7903 | 0.5386 | 1.1495889393193712 |

**5c polling cadence:** PASS. Inserting an identical poll 10 seconds after every original observation produces exactly equal forecasts for practice, dilution, and final-style. First observation times for distinct states are preserved, as required; moving actual refresh timestamps would change the evidence and is not this test.

**5d universal trophy failure:** The fixed `[99.8,100,100,100,100]` row has loss **5.126700364743543** if the truth is 95%, contributing **0.09321273390442807** to a 55-trophy case mean. If truth stays at 100%, that row still costs **0.059952685424466634** because q05 is below 100. Universal confidence is a material assumption.

## 6. Grader-style run

PASS. `/usr/bin/python3 -P -s /tmp/trophy-v3-build/main.py` from the different cwd `/tmp/trophy-v3-build/.verification`, with explicit directory overrides, produced byte-identical p00/p01 files to the ordinary run. All imports are standard library; the entry does not depend on cwd or verify.py.

## 7. Zero horizon

PASS on both generated branches. In each case checkpoint = target = timestamp of last distinct observation and horizon_minutes = 0. All **54 ordinary trophies per branch** had q50 exactly equal to their last rates after four-decimal rounding. The universal row is excluded under its separate boundary rule. Spread remains nonzero as allowed. The persistent-zero median 0.01 and its narrower spread were also checked separately.

## 8. Frozen factors, spread, and manual blend arithmetic

PASS. The implementation follows the prose's explicit rounded constants **6.06 and 1.34**, rather than substituting the context ratios 3868/638 = 6.06269592476489 and 408/305 = 1.337704918032787.

| Horizon from last distinct observation | Player factor | Earner factor |
| ---: | ---: | ---: |
| 0 minutes | 1 | 1 |
| 45 minutes | 2.4617067250182343 | 1.1575836902790226 |
| 90 minutes | 6.06 | 1.34 |
| 900 minutes | 6.06 | 1.34 |

At h=90, the scenario multiplies rates by 1.34/6.06 = **0.22112211221122116**. After collapsing identical polls, both practices' retained timestamp is 2026-11-18T23:50:49.360Z, so h is actually **279.17733333333337** minutes for p00 and **309.17733333333337** for p01. Both hit the same factor caps as h=90. This distinction follows the brief's last-distinct-observation horizon definition.

Independent manual substitution from the last rates uses S = r × 1.34 / 6.06, Lp = ln((r/100)/(1−r/100)), Ls = ln((S/100)/(1−S/100)), M = 0.75 Ls + 0.25 Lp, then median = 100/(1+exp(−M)). These calculations use elementary arithmetic directly, not the entry's frozen-factor or blend helper.

| Trophy | Last r % | Scenario S % | Persistence logit Lp | Scenario logit Ls | Weighted M | Unrounded median % | Entry q50 % |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 1.25 | 0.27640264026402644 | −4.3694478524670215 | −5.8882989674151345 | −5.508586188678106 | 0.40354807717955843 | 0.4035 |
| 4 | 1.10 | 0.24323432343234327 | −4.498799058824342 | −6.016464886115455 | −5.637048429292677 | 0.3550717916396141 | 0.3551 |
| 20 | 2.04 | 0.4510891089108911 | −3.871609424227842 | −5.396739468392086 | −5.0154569573510255 | 0.6590871819715468 | 0.6591 |

For example id3: 0.75 × (−5.8882989674151345) + 0.25 × (−4.3694478524670215) = −5.508586188678106. Id4 gives −5.637048429292677 and id20 gives −5.0154569573510255 by the same explicit weights. Each inverse and half-up rounding matches the output. Full five-quantile rows for all three trophies also exactly match spread **1.0**, confirming the frozen floor. Specific persistent-zero exceptions retain their separately specified 0.30–0.55 spread.

## Remaining defects, limitations, and interpretation choices

- The approximately 1.15-logit branch discontinuity is large and remains deliberately present to match V3. A tiny observation change switches away from the dilution prior.
- Frozen calibration is based on one refresh; future refresh factors can differ, and frozen rates can rise. The retained persistence weight is a design hedge, not validated calibration.
- Trend damping, floors, tier rules, universal confidence, and symmetric normal spreads are unvalidated design assumptions. Symmetry misses directional dilution, delayed unlocks, and point masses. The measured universal-to-95 loss is substantial.
- Stable, stale, and zero-to-positive synthetic results expose losses relative to point persistence. Synthetic successes do not establish real forecasting accuracy, final 4.52-day accuracy, or superiority over house AI (whose strength is unknown).
- Local Python is **3.12.3**, not the grader's 3.13. All required checks ran successfully here; execution on Python 3.13 was not measured. The code uses standard library APIs available in both versions.
- Negative extrapolation horizons are treated as zero for growth and nonnegative time widths; valid contest cases target the future. Time mapping follows the specified epoch and assumes timestamps lie in its log1p domain. Malformed JSON or fundamentally invalid schemas are not given an unspecified recovery strategy.
- With nulls, persistence is the last non-null rate and fitting skips missing values; the global last distinct timestamp anchors extrapolation, as the brief defines. A single usable rate produces zero slope. Weighted residual fallback uses only trophies with at least three usable distinct observations.
- The manual arithmetic verification is performed by direct formula substitution in the test harness and explicitly shown above; it does not rely on the entry's forecast center. Diagnostic comparator spread reconstructed from rounded output has minor rounding error, and undamped decomposition can saturate badly. These are test-comparator limitations, not entry deviations.

No known deviation from the specified entry algorithm remains. No final score or independent practice answer is available from the authorized local files.
