# P3 Preregistration Addendum 01 — H1 Evaluation Freeze

This addendum materializes evaluation choices for the pre-window H1 foundation.

1. H1 is implemented before the hackathon build window.
2. H1 is declared pre-existing evaluation infrastructure.
3. H1 is not claimed as scored build-window implementation.
4. Policy-visible structured information is restricted to the C1 whitelists in `docs/H1_EVAL_FOUNDATION.md`: observation samples (`target_id`, `step`, `time`, `observed_x`, `observed_y`, `nominal_x`, `nominal_y`, `nominal_speed`); known config (`dt`, `tolerance`, `x_pick`, `y_pick`, `belt_speed`); and command feedback (`command_id`, `target_id`, `issued_time`, `execution_time`, `accepted`, `success`, `reason_code`).
5. `PAUSE_THEN_RECOVER` clears only after six consecutive clean samples.
6. The B2 development calibration set is exactly `drift-high`, `moving-mid`, `load-mid`, `moving-high`, `load-high`, and `combo`.
7. Structural holdout is selected by the deterministic C4 rule in `docs/H1_EVAL_FOUNDATION.md`, using the P3 preregistration SHA and the canonical composition list.
8. H1 must not generate final eval-v3 seed values.
9. Final eval-v3 seed realization is generated only during H5, after implementation-candidate freeze, under P3 §18.1, in an isolated process/context.
10. Simulator, controller, and evaluator use of true state remains legal and is explicitly separated from policy-visible inputs. Controller execution and evaluator scoring continue to use physical plant truth.

This addendum does not alter `docs/P3_SYSTEM2_DESIGN.md` or move/rewrite `p3-prereg`.
