# RRA-V0-REPAIR-03 execution record

## Scope and commits

All benchmark and audit runs used only `config/dev_seeds.json` (seeds 0–129,
1,560 objects per scenario and mode). No eval seeds or eval results were used.
The frozen limits remain unchanged: `MAX_TIME_CORRECTION = 0.50`, tolerance,
classification thresholds, `safe_residual_threshold`, and the consecutive
failure threshold of 3.

| Item | Commit | Change |
|---|---|---|
| S2 | `5c7440f` | Convert motion lead using `nominal_speed + slope`; escalate for a non-positive denominator. |
| S1 | `a7aa8f4` | Expose saturation and skip at the command decision using the latest correction. |
| S3 | `fb3f6d2` | Issue at the first sample at or past the pick-window start. |
| S5 | `5db7ba3` | Share the `MAX_TIME_CORRECTION` constant with world horizon validation. |
| S4 | `ec1e0b5` | Correct REPAIR-02 hashes and add command outcome detail to failure traces. |

Every implementation commit was followed by the full 14-scenario dev benchmark.
The S4 benchmark is the final code result below; intermediate stage runs used the
same seeds and showed the expected changes as S1 and S3 were added.

## Final dev benchmark

Success rate uses all 1,560 objects as its denominator. MAE is over attempted
objects. Terminal counts are compensation-on, ordered as
`picked / attempt_failed / rejected / escalated / skipped`. Escalations are the
episode escalation metric.

| Scenario | Off success | On success | Off MAE | On MAE | On terminal counts | On escalations |
|---|---:|---:|---:|---:|---|---:|
| nominal | 1.000 | 1.000 | 0.051 | 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| bias-low | 1.000 | 1.000 | 0.094 | 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| bias-mid | 0.000 | 1.000 | 0.254 | 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| bias-high | 0.000 | 1.000 | 0.452 | 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| drift-low | 1.000 | 1.000 | 0.070 | 0.051 | 1560 / 0 / 0 / 0 / 0 | 0 |
| drift-mid | 0.032 | 1.000 | 0.275 | 0.052 | 1560 / 0 / 0 / 0 / 0 | 0 |
| drift-high | 0.000 | 0.401 | 0.536 | 0.053 | 625 / 0 / 0 / 0 / 935 | 74 |
| moving-low | 0.987 | 1.000 | 0.129 | 0.052 | 1560 / 0 / 0 / 0 / 0 | 0 |
| moving-mid | 0.000 | 0.203 | 0.595 | 0.054 | 316 / 0 / 0 / 0 / 1244 | 116 |
| moving-high | 0.000 | 0.000 | 0.965 | 0.000 | 0 / 0 / 0 / 1442 / 118 | 130 |
| load-low | 0.677 | 1.000 | 0.167 | 0.052 | 1560 / 0 / 0 / 0 / 0 | 0 |
| load-mid | 0.000 | 0.242 | 0.631 | 0.055 | 377 / 0 / 0 / 0 / 1183 | 108 |
| load-high | 0.000 | 0.008 | 0.879 | 0.055 | 13 / 0 / 0 / 1456 / 91 | 130 |
| combo | 0.000 | 0.008 | 0.338 | 0.149 | 13 / 1 / 0 / 1546 / 0 | 130 |

### Comparison with `9cb87e4`

The baseline was rerun at `9cb87e4` with the same dev seeds and benchmark
procedure. These compensation-on rates fell by more than 0.02:

| Scenario | Baseline rate | Final rate | Picked objects changed to saturated skip | Picked objects changed to safe-stop skip | Net fewer picks |
|---|---:|---:|---:|---:|---:|
| drift-high | 0.988 | 0.401 | 547 | 369 | 916 |
| moving-mid | 0.853 | 0.203 | 424 | 590 | 1014 |
| load-mid | 0.673 | 0.242 | 287 | 386 | 673 |

Some baseline `attempt_failed / missed pick window` objects also became skips:
14 saturated and 5 safe-stop skips in drift-high; 123 saturated and 102
safe-stop skips in moving-mid; 280 saturated and 151 safe-stop skips in
load-mid. Saturated skips count toward the unchanged consecutive-failure rule;
an isolated saturated skip does not independently trigger `safe_stop`.

The correction-saturated outcome count was 561 in drift-high, 547 in moving-mid,
and 567 in load-mid. In moving-mid and load-mid, these represent a substantial
conversion of prior misses and picks into the explicit saturation terminal
reason. The measured success-rate reductions above are retained as-is.

## Pick-window misses and command audit

Compensation-on objects with a non-picked terminal outcome and reason
`missed pick window`, excluding escalated outcomes:

| Scenario | Objects |
|---|---:|
| combo | 1 |
| All other scenarios | 0 |

The remaining object is not saturated. Its failure trace is:

| Scenario / seed / target | x0 | True ETA | Applied ETA | Command time | Position error | Time error | Saturated |
|---|---:|---:|---:|---:|---:|---:|---|
| combo / 10 / 0 | -4.175993 | 3.445205 | 3.550378 | 3.600000 | 0.202370 | 0.049622 | false |

The sampled command counts contained no target with more than one command.
The window-crossing test also verifies that a window skipped between samples
still issues exactly one command.

## Tests and repository checks

- `.venv/bin/pytest -q`: **24 passed**.
- The new saturation, motion ETA, and skipped-window tests failed on the original
  implementation before their corresponding fixes.
- `tests/test_repair02.py` remains green as regression protection.
- `git diff 6377fa6..HEAD -- config/eval_seeds.json` is empty.
- REPAIR-02 R1 and R2 hashes are corrected to `fe25590` and `f944b00`.
