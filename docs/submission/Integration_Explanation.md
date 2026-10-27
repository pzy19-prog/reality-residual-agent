# Sponsor technology and integration roles

## Zetaris: governed evidence federation

The L3 evidence path serves three policy telemetry tables from PostgreSQL: `observation_samples`, `presence_events`, and `command_feedback`. A local read-only REST row server supplies `known_config` and `ops_context`. Zetaris registers the PostgreSQL source and the two REST tables, then federates the selected fields into the shared C1 evidence packet. `src/rra/evidence/sources.py` defines the whitelist; `scripts/l3_zetaris_up.sh` shows source registration and `scripts/l3_equivalence.py` shows packet assembly and comparison with the local reference loader.

The recorded integration receipt is the validation result: T3 anchor mismatches 0, T3 authorization mismatches 0, T4 mismatches 0, and the two T8 reference receipts are byte-identical. The demo labels this as recorded evidence. It does not show a simulated live query. Registered eval-v3 results used the local reference loader rather than live Zetaris retrieval.

## Meterless: local H-MEM persistence and replay

The Python wrapper calls a JSON-lines bridge. The bridge imports the pinned Meterless `engines/hmem/reference/src/index.ts` implementation at commit `1742dec56a66e58eef9dda2d2b865823758ca8cd`. After an episode completes, it persists a run record and manifest. H-MEM records are tagged with the episode ID; reads are scoped to the current episode and cross-episode reads are refused. Replay reads the stored manifest and checks that decisions and the receipt reproduce.

This uses the open local reference implementation, not a hosted Meterless cloud service. The existing fresh development log records 4 episodes, 4 replay matches, 0 cross-episode reads, and `all_ok=true`. The fresh `ep-014` excerpt records 14 persisted decisions and matching manifest/replay receipt hashes. These are development integration checks, not registered eval-v3 score rows. No check was rerun for this repair.

## NVIDIA Nemotron

Nemotron proposes or ranks candidate structures within B4. Deterministic fitting and counterfactual verification evaluate candidates; a common-action gate and explicit bounded authorization decide whether an action proceeds. The model is not an actuator controller. TIEBREAK shows no measured recovery gain.

## Technical stack and source evidence

Python 3.12.3 and NumPy 2.5.4 run the agent and local evidence builder. The Meterless bridge is TypeScript under Node 22. The Zetaris source fixtures use PostgreSQL and a read-only REST server. The technical claim sources and exact artifact fields are listed in `Evidence_Source_Index.md` and bundled in `data/`.

Cursor is optional under the current requirements; no usage claim is made.
