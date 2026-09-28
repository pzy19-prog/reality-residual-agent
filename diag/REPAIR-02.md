# RRA-V0-REPAIR-02 execution record

## Baseline: tests against d197f1e

Command: `.venv/bin/pytest -q tests/test_repair02.py`

Result on the unchanged implementation: **6 failed, 1 passed** (`0.32s`).
The passing test is `test_regression_sensor_offset_positive_time_delta`; this is expected
because the existing positive correction for a constant sensor offset is already
correct. The six failures cover the unreachable-horizon validation, physical-lead
correction sign, early nominal reachability, applied-plan command time, terminal
outcomes, and consecutive-failure escalation.

The strengthened R3 assertion observed at least one issued command, then failed
because `Command.expected_time` was the sample time instead of the associated
`applied_plan.expected_arrival_time`. It also requires a non-grid expected time,
so the old sampling-time behavior cannot pass by matching a grid-aligned plan.

## Dev benchmark deltas

All runs below use exactly `config/dev_seeds.json` (seeds `0–129`, 1,560
objects per scenario and mode). The first row is the test-only baseline at
`edb8b44`; each later row records the implementation stage. The metrics use
the same fixed seeds at every stage.

| Stage | nominal off/on | bias-low off/on | drift-low off/on | moving-mid on misses | load-mid on misses | combo off/on |
|---|---:|---:|---:|---:|---:|---:|
| Baseline `edb8b44` | 0.985 / 0.985 | 1.000 / 0.985 | 0.985 / 0.970 | 231 | 449 | 0.000 / 0.005 |
| R1 `fe25590` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 231 | 449 | 0.000 / 0.005 |
| R2 `f944b00` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 0.992 | 231 | 449 | 0.000 / 0.014 |
| R3 `d0a9917` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 226 | 449 | 0.000 / 0.014 |
| R4 `bf04288` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 226 | 449 | 0.000 / 0.014 |
| R5 | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 230 | 510 | 0.000 / 0.014 |

R1 restored the nominal, bias-low, and drift-low successes lost to the short
episode horizon. At R1, moving-mid had 231 misses and load-mid had 449 misses
in compensation-on mode (out of 1,560 objects each). At R2, those counts are
unchanged. The R2 on success rates for bias-high, drift-high, moving-high, and
load-high are respectively `1.000`, `0.987`, `0.011`, and `0.023`; none fell
from R1. Drift-low had 12 misses at R2, caused by the moving prediction window
crossing the half-sample boundary between observations; the R3 scheduling margin
removed them.

No dev scenario's compensation-on success rate decreased by more than `0.02`
from R2 to R3. R5 stops an episode
after three consecutive failed or skipped outcomes, so moving-mid and load-mid
have more misses than at R4; their remaining misses are shown above.

## Terminal-outcome audit

After R5, every dev seed was run in all 14 configured scenarios with
compensation both off and on. All 3,640 receipts had exactly one outcome per
object, unique target IDs, valid terminal counts summing to `object_count`, and
nonempty reasons for every skipped outcome. There were no receipt violations.

In compensation-on mode, the only non-picked outcomes in episodes without an
escalation were isolated `attempt_failed` results. Each has the nonempty reason
`missed pick window`; counts across all dev seeds were:

| Scenario | Non-picked outcomes without escalation | Reason |
|---|---:|---|
| drift-high | 19 | `missed pick window` |
| load-mid | 359 | `missed pick window` |
| moving-mid | 216 | `missed pick window` |

All other compensation-on scenarios had zero such outcomes. No eval seeds or
eval benchmark results were read.
