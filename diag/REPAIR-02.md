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
`edb8b44`; each later row records the code at the named implementation commit.

| Stage | nominal off/on | bias-low off/on | drift-low off/on | moving-mid off/on | load-mid off/on | combo off/on |
|---|---:|---:|---:|---:|---:|---:|
| Baseline `edb8b44` | 0.985 / 0.985 | 1.000 / 0.985 | 0.985 / 0.970 | 0.000 / 0.852 | 0.000 / 0.712 | 0.000 / 0.005 |
| R1 `4972e4b` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 0.000 / 0.852 | 0.000 / 0.712 | 0.000 / 0.005 |
| R2 `cceee71` | 1.000 / 1.000 | 1.000 / 1.000 | 1.000 / 0.992 | 0.000 / 0.852 | 0.000 / 0.712 | 0.000 / 0.014 |

R1 restored the nominal, bias-low, and drift-low successes lost to the short
episode horizon. At R1, moving-mid had 231 misses and load-mid had 449 misses
in compensation-on mode (out of 1,560 objects each). At R2, those counts are
unchanged. The R2 on success rates for bias-high, drift-high, moving-high, and
load-high are respectively `1.000`, `0.987`, `0.011`, and `0.023`; none fell
from R1. Drift-low has 12 misses, all caused by a prediction window crossing
the exact half-sample boundary between observations; R3 will use the planned
arrival time for the controller check and handle the floating-point boundary.
