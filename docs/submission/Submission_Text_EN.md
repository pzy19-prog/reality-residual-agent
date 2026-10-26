# Project description

**Reality Residual Agent (RRA)** is a 2D conveyor simulation and evidence-constrained recovery agent for automation and robotics experimentation. A fast residual layer handles immediate discrepancies. B3 exhaustively searches a bounded recovery DSL. B4 Nemotron proposes or ranks candidate structures; deterministic fitting and counterfactual verification feed a common-action gate and explicit bounded authorization. A receipt records the result. The language model does not control actuators or replace verification.

In the development trace, four displayed fit checks are the first four of fourteen candidates. The update proceeds because a common safe action exists across passing checks; at `AMBIGUOUS`, no common safe action spans the passing checks, so the policy pauses. This does not mean a unique causal model is always required. `SENSOR_STUCK` names the development scenario; `BELT_STOP_OR_MOTION_LOSS` is the recorded policy fault label.

In the registered 100-episode comparison, B2 recovered 104 of 614 recoverable challenges with 47 unsafe events. B3 recovered 41/614 with 15 unsafe events, all from the fast layer; S2-authorized unsafe events were 0, while B3 issued 159 authorizations. B4 STRICT equals B3 by construction under registered A04 §2. B4 TIEBREAK recovered 39/614 and recorded 58–59 unsafe events across four text conditions, including 43–44 S2-authorized unsafe events. TIEBREAK showed no measured recovery gain. Unsafe values are event counts, not episode rates.

This is a bounded research prototype in 2D simulation. Case 9 was seen during development, so no unseen-composition generalization is claimed. The results do not establish physical deployment, production customers, measured business ROI, or broad safe-agent guarantees.

# Integration explanation

**NVIDIA Nemotron** proposes or ranks candidate structures within B4. It is upstream of deterministic fitting, counterfactual verification, the common-action gate, and bounded authorization. Stronger ranking or valid JSON does not establish safer actions or recovery gain.

**Zetaris** federates the evidence sources used to assemble a common whitelisted C1 packet. A PostgreSQL telemetry source exposes `observation_samples`, `presence_events`, and `command_feedback`. Two read-only REST sources expose `known_config` and `ops_context`. The `scripts/l3_equivalence.py` path assembles the packet through Zetaris and compares it with the local reference loader. A recorded receipt reports zero T3 anchor mismatches, zero T3 authorization mismatches, zero T4 mismatches, and byte-identical T8 reference receipts. This is recorded validation, not a new live query. Registered eval-v3 used the local reference loader.

**Meterless** is used through the pinned local H-MEM reference implementation (`1742dec56a66e58eef9dda2d2b865823758ca8cd`), not a hosted cloud service. The persistence wrapper stores completed episode runs and manifests, scopes reads to the current episode, and replays the stored manifest for comparison. Existing fresh development evidence records four episodes, four replay matches, zero cross-episode reads, and all checks passing. The `ep-014` trace records a 14-decision replay with a matching receipt. These are development integration checks, not registered eval-v3 outcomes.

Cursor is optional under the current requirements. No actual-use claim is made.
