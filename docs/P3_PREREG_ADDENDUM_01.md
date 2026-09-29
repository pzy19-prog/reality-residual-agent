# P3 Preregistration Addendum 01 — H1 Evaluation Freeze

This addendum materializes evaluation choices for the pre-window H1 foundation.

1. H1 is implemented before the hackathon build window.
2. H1 is declared pre-existing evaluation infrastructure.
3. H1 is not claimed as scored build-window implementation.
4. Policy-visible structured information is restricted to the C1 whitelists in `docs/H1_EVAL_FOUNDATION.md`: observation samples (`target_id`, `step`, `time`, `observed_x`, `observed_y`, `nominal_x`, `nominal_y`, `nominal_speed`); target presence events (`target_id`, `step`, `time`, `target_observed`); known config (`dt`, `tolerance`, `x_pick`, `y_pick`, `belt_speed`); and command feedback (`command_id`, `target_id`, `issued_time`, `execution_time`, `accepted`, `success`, `reason_code`).
5. `PAUSE_THEN_RECOVER` clears only after six consecutive clean samples.
6. The B2 development calibration set is exactly `drift-high`, `moving-mid`, `load-mid`, `moving-high`, `load-high`, and `combo`.
7. Structural holdout is selected by the deterministic C4 rule in `docs/H1_EVAL_FOUNDATION.md`, using the P3 preregistration SHA and the canonical composition list.
8. H1 must not generate final eval-v3 seed values.
9. Final eval-v3 seed realization is generated only during H5, after implementation-candidate freeze, under P3 §18.1, in an isolated process/context.
10. Simulator, controller, and evaluator use of true state remains legal and is explicitly separated from policy-visible inputs. Controller execution and evaluator scoring continue to use physical plant truth.

This addendum does not alter `docs/P3_SYSTEM2_DESIGN.md` or move/rewrite `p3-prereg`.

## OBJECT_MISSING observable evidence repair

The policy receives the registered observable target-presence event for every expected sample opportunity. A detector observation emits `target_observed=true`; no detector observation emits `target_observed=false`. Event silence is never used to infer absence. For `OBJECT_MISSING`, positional `PolicyObservationSample` records stop after the target is no longer observed, while false presence events continue at every expected sample opportunity. The event contains only `target_id`, `step`, `time`, and `target_observed`. Hidden `target_present` remains evaluator-only and is not part of any policy-visible schema. This additive evidence-channel repair does not change fault distributions, B2 calibration, or evaluator difficulty.
