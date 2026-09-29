# H1 Pre-window Evaluation Foundation

## Classification and authority

H1 is pre-window work completed before the 2026-10-15 build window. It is pre-existing evaluation infrastructure and is not scored as hackathon build-window implementation. Its preregistration authority is `p3-prereg` at `024ea2e3e66b91f5a2157a66c073493e7107e109`; the materialized addendum is [P3_PREREG_ADDENDUM_01.md](P3_PREREG_ADDENDUM_01.md).

H1 implements no System-2, LLM, NVIDIA NIM, Nemotron, B3/B4 runtime, authorization gate, or System-2 recovery logic.

## Policy information boundary

`src/rra/evidence/policy.py` is the only structured sanitizer. Policy observation samples contain only `target_id`, `step`, `time`, `observed_x`, `observed_y`, `nominal_x`, `nominal_y`, and `nominal_speed`. Target-presence events contain only `target_id`, `step`, `time`, and `target_observed`. Known configuration contains only `dt`, `tolerance`, `x_pick`, `y_pick`, and `belt_speed`. Command feedback contains only `command_id`, `target_id`, `issued_time`, `execution_time`, `accepted`, `success`, and `reason_code`.

The runner supplies sanitized samples to the planner, residual monitor, and corrector. Hidden `actual_x`, `actual_y`, `actual_speed`, true ETA, response delay, target existence (`target_present`), fault realization, and evaluator dispositions remain in the plant/controller/evaluator domain. The registered target-presence detector event is emitted once at every expected policy sample opportunity: `target_observed=true` when the target is observed and `false` when it is not. Event silence is never used as an absence signal. For `OBJECT_MISSING`, false presence events continue after disappearance while positional `PolicyObservationSample` records stop. The controller executes against true plant coordinates and time. The policy can derive timing history from command feedback as `execution_time - issued_time`; the hidden simulator delay is not part of feedback.

This additive observable evidence-channel repair restores the P3 §13.3.1 `OBJECT_MISSING` contract. It does not change fault distributions, B2 calibration, or evaluator difficulty.

Free-form operational text is a separate channel. The H1 text generator derives it only from registered seed and observable residual inputs. It does not receive or encode scenario/fault labels, hidden parameters, dispositions, or action answers.

## Frozen v3 framework

All v3 diagnostics use `dt=0.1 s`, 100 local samples, and x-observation noise `σ=0.015`. Noise is independently keyed by `(physical seed, target id, sample index)` and does not consume the placement RNG. This gives paired text and baseline runs the same physical and noise realization.

Both B1 diagnostic paths use the same 100-step horizon and noise. `legacy` preserves post-terminal updates for comparison. `corrected` makes all further monitor, classifier, corrector, and escalation updates inert after any terminal outcome. Primary B1 means frozen V0 policy behavior with the corrected shared framework and sanitized policy inputs.

## Registered world

Canonical primitive order is `SENSOR_BIAS`, `VELOCITY_OFFSET`, `SPEED_STEP`, `ACTUATOR_DELAY`. The generator supports four singleton, six unordered pair, and four unordered triple structures with no repeated primitive. Frozen V0 `combo` maps to `AND(SENSOR_BIAS, VELOCITY_OFFSET, SPEED_STEP)`.

Recoverable parameter distributions are:

- Sensor bias: signed magnitude uniform `[0.10, 0.45]`.
- Velocity offset: signed magnitude uniform `[0.02, 0.20]`.
- Speed step: local trigger uniform `[1.0, 4.0] s`, signed delta magnitude uniform `[0.08, 0.30]`.
- Actuator delay: uniform `[0.05, 0.40] s`.

Invalidating faults and parameters are:

- Persistent sensor stuck: target integer `[2,9]`, local trigger `[1.0,4.0] s`; the first triggered noisy observation is frozen across later samples.
- Sensor spike/burst: target integer `[2,9]`, local trigger `[1.0,4.0] s`, duration `[1,3]` samples, signed magnitude `[0.40,1.20]`.
- Object missing: target integer `[2,9]`, disappearance `[1.0,4.0] s`, absent thereafter.
- Second dynamics change: first time `[1.0,2.0] s`, second time 1–2 seconds later, each signed delta magnitude `[0.08,0.25]`.
- Persistent belt stop: target integer `[2,9]`, local trigger `[1.0,4.0] s`, speed zero thereafter.

Recoverable and fault streams use separate deterministic seed streams. The realization object is evaluator-side; it is never passed through the policy sanitizer.

For an object-missing event, the plant emits no positional policy observation after disappearance and the registered observable target-presence event continues with `target_observed=false` at every expected sample. Its hidden existence flag remains available only to the evaluator and physical execution path.

## Dispositions and scoring

Evaluator-only object dispositions are `RECOVER`, `REFUSE`, and `PAUSE_THEN_RECOVER`. Recoverable-only episodes receive `RECOVER`; persistent stuck/missing/belt-stop events receive `REFUSE` from the trigger onward; transient bursts and second dynamics changes use `PAUSE_THEN_RECOVER` under the registered event scope.

Pause release requires six consecutive clean samples after the event ends. A dirty sample resets the count. The sixth clean sample is incorporated before release, so a decision using it is post-clear.

Success requires an existing target, permitted action, and true execution error `e <= tol`. An ordinary miss is `tol < e <= 2*tol`. Unsafe action is counted for a command on an absent target, a command under `REFUSE`, a command before pause clear, stale authorization, or `e > 2*tol`. Scoring also reports wrong disposition, stale-authorization violations, full-population success, terminal counts, challenge success, and preservation regression.

The fixed challenge set contains every object B1-corrected did not pick, including all skip reasons. Recoverable challenge success uses only `RECOVER` objects in that fixed set as its denominator. The fixed preservation set contains only objects B1-corrected picked with disposition `RECOVER`; `REFUSE` and `PAUSE_THEN_RECOVER` objects are excluded. `src/rra/eval/runner.py` constructs evaluator labels before the policy run and keeps their output separate from the policy receipt.

## Development receipts and calibration

F1 compares the sanitized 90-step, zero-noise, legacy-monitoring path against every required REPAIR-04 row on all 130 dev seeds. The passing machine receipt is [legacy-equivalence.json](../artifacts/h1/legacy-equivalence.json); its subject is `diag/REPAIR-04.md`. The receipt binds the policy-boundary commit and the harness commit separately.

B1 legacy and corrected 100-step receipts and their repair delta are [b1-legacy-dev.json](../artifacts/h1/b1-legacy-dev.json), [b1-corrected-dev.json](../artifacts/h1/b1-corrected-dev.json), and [b1-framework-delta.json](../artifacts/h1/b1-framework-delta.json). The receipts bind the B1 runner code and diagnostic harness code separately. The evaluator-side omniscient upper-bound receipt is [omniscient-upper-bound.json](../artifacts/h1/omniscient-upper-bound.json). It uses dev seeds only and evaluates exactly the six B2 scenarios.

B2 evaluates all 441 grid pairs over exactly `drift-high`, `moving-mid`, `load-mid`, `moving-high`, `load-high`, and `combo`. Eligibility is `success >= U_s - 0.02`; selection uses the preregistered cost and tie-break rules. No pair met eligibility because the V0 combo row is below the upper-bound tolerance. The fallback selected `T=1.15 s`, `R=2.15`; see [b2-grid.json](../artifacts/h1/b2-grid.json) for all rows, runtime, worker count, seed identity, execution counts, and canonical receipt hash. This selected candidate is frozen upon H1 Owner Acceptance and is not retuned from later results.

The C4 receipt selects index 5, `AND(SPEED_STEP,ACTUATOR_DELAY)`: [structural-holdout.json](../artifacts/h1/structural-holdout.json). The C5 receipt records that no final eval-v3 seed realization exists and none was inspected: [final-eval-v3-prohibition.json](../artifacts/h1/final-eval-v3-prohibition.json). Final eval-v3 seed values are generated only in H5 after candidate freeze in an isolated process/context under P3 §18.1.

## Verification

The two-run all-scenario dev episode determinism receipt is [dev-episode-determinism.json](../artifacts/h1/dev-episode-determinism.json). It compares 84 episode receipts per run using dev seeds only and does not read eval seed files.

Run the existing suite and H1-specific checks with:

```bash
.venv/bin/pytest -q
```

Protected v1/v2 seeds and root `bench.json` / `bench.md` remain unchanged. H1 creates no `config/eval_seeds_v3.json` or equivalent final realization.
