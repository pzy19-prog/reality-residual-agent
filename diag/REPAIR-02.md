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

Will be recorded after each implementation commit using only seeds `0–129`.
