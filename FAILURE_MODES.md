# Known failure modes — RRA V0

All numbers: blind eval v2 (seeds 2000–2099, 1,200 objects per scenario/mode, `bench.md`, artifact `2418406`) unless marked *dev* (seeds 0–129, `diag/REPAIR-04.md`). "on" = compensation on.

## Current V0 failure modes (fast rule layer)

1. **Correction envelope (explicit skip).** Time correction is clamped to ±0.5 s. When the post-clamp residual × estimated speed exceeds the pick tolerance (0.2), the object is skipped as `correction_infeasible` instead of issuing a command known to miss. on-mode skips: moving-mid 142, load-mid 385, moving-high 76, load-high 46 (of 1,200). This trades success rate for zero silent failures.
2. **Hard escalation (fail-closed).** |residual| > 1.25 triggers `ESCALATE` and stops the episode. moving-high, load-high and combo escalate in all 100 eval episodes; on success is 0.010 / 0.023 / 0.007. Recovering from these states is the System-2 objective, not a fast-layer tuning target.
3. **Boundary admissions.** Clamped-but-feasible objects are attempted; some miss with the explicit reason `missed pick window`. on-mode `attempt_failed`: drift-high 23, moving-mid 39, load-mid 28, moving-high 1, load-high 3, combo 1.
4. **Outcome-escalation trade-off.** Three consecutive failed or skipped objects stop the episode. This prevents repeated bad actions but forfeits later objects that might have been recoverable (load-mid: 18 escalations; moving-mid: 1). The rule is active in both modes, so off-mode coverage is below 1 under disturbance.
5. **Model limits.**
   - Motion lead is extrapolated at constant slope; a load step changes slope mid-approach, which makes load-mid the weakest mid scenario (on success 0.656).
   - Disturbance classification is heuristic over a 12-sample window and lags the first samples.
   - Lateral (y) error is not compensated; the gripper is fixed at `y_pick`.
   - Actuator response delay (`load_response_delay`, default 0) is not estimated.
   - The simulator is idealized: noiseless sensor, no actuator dynamics, occlusion or collisions. Results say nothing about hardware.

## Failure modes found and fixed during V0 (lessons for other teams)

| Failure | Symptom | Fix |
|---|---|---|
| Unreachable horizon | Objects with ETA > 7.95 s were never sampled in their pick window → ~1.5 % silent misses even in nominal | `fe25590` horizon covers latest corrected window; config validator refuses unreachable settings |
| Sign error | A bias-style correction was applied to physical lead (drift below classifier threshold) → pushed picks later instead of earlier | `f944b00` separate sensor offset from motion lead |
| Vacuous time check | Command time was the sample time, so controller time error was always 0 | `d0a9917` command uses the planned arrival time |
| Silent skips | Objects could end with no command, no escalation and no reason | `bf04288` exactly one terminal state per object; `9cb87e4` outcome escalation |
| Silent clamp saturation | Clamped correction still issued a command known to miss | `a7aa8f4` explicit saturation (too strict) → `21e38a0` skip only when post-clamp error exceeds tolerance |
| Magic scheduling margin | A 1 ms window margin hid missed windows between samples | `fb3f6d2` trigger on window crossing |
| Metric aggregation | Episode-averaged MAE diluted errors with unattempted episodes | `b025bd4` error sum over attempts |
| Burned eval | eval v1 (1000–1099) was published and affected by the horizon bug | Retired; eval v2 frozen in `ff1ac91` before the single run |
