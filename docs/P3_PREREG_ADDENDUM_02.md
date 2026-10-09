# P3 Preregistration Addendum 02 — Schedule Change and Sponsor-Integration Boundary

Status: **PRE-WINDOW DESIGN AMENDMENT / NOT SCORED WORK**

Dated: 2026-10-09. This addendum is design-only and predates the build window.

This addendum does not alter `docs/P3_SYSTEM2_DESIGN.md` or move/rewrite `p3-prereg`. It applies on top of `docs/P3_PREREG_ADDENDUM_01.md`. Where this addendum and the P3 document differ, this addendum governs only the items listed in Sections 1, 3, 6, 7 and 8 below.

## 0. Reason for amendment

The organizer changed the event after P3 was preregistered: the build window moved by one week, the track list changed, and the sponsor-technology requirements changed. Source: the public event page and the participant workspace as captured on 2026-10-09 (see `docs/HACKATHON_RULES.md` once refreshed).

This amendment is triggered by those external changes only. It is not triggered by any evaluation result. Final eval-v3 seeds have not been generated, and no System-2 implementation exists.

## 1. Schedule supersession

The build window is now **2026-10-22 00:00 UTC through 2026-10-27 23:45 UTC**.

Every reference to `2026-10-15 00:00 UTC` as the build-window boundary in P3 (header, Section 21, Section 28) and in Addendum 01 is read as `2026-10-22 00:00 UTC`. Every reference to `2026-10-20 23:45 UTC` as the submission deadline is read as `2026-10-27 23:45 UTC`.

No System-2 implementation begins before `2026-10-22 00:00 UTC`.

## 2. What does not change

The following remain exactly as preregistered in P3 and Addendum 01:

- scenario and fault families, parameter distributions, trigger-time rules;
- the four DSL primitives and the 14-structure recoverable model space;
- observation noise `σ = 0.015`, the six-observation minimum, and `RMSE <= 0.030`;
- the common-action / ambiguity gate;
- B1, B2, B3, B4-strict, B4-tiebreak, and the B2 tuning rule;
- the C1 policy-visible whitelists, text template families, pairing rules, and leakage restrictions;
- fixed challenge and preservation sets, outcome severity, and the `unsafe_action == 0` criterion;
- eval-v3 seed handling under P3 Section 18.1;
- every success criterion and failure interpretation in P3 Sections 19 and 20.

## 3. Sponsor-technology placement

Principle: **sponsor technology is substrate, never authority.** It may store, retrieve, and carry evidence. It may not fit parameters, verify hypotheses, or authorize actions.

| Technology | Role in the System-2 path | Never does |
|---|---|---|
| NVIDIA Nemotron | B4 hypothesis generator: proposes DSL structures with rationale and evidence references (P3 Section 4, unchanged) | numeric parameter estimation, verification, authorization, actuator control |
| Meterless World Model | episode-scoped evidence graph: policy-visible observations, events, text context, and the hypothesis → verification → authorization → outcome links | hold simulator ground truth or evaluator labels |
| Meterless H-MEM | the episode-local memory of P3 Section 11 | cross-episode learning |
| Zetaris | retrieval path for the fragmented operational context of P3 Section 12 (maintenance work orders, MES events, shift notes) | supply labels, scenario names, or hidden parameters |
| Cursor | build-window authoring tool | any runtime role |

### 3.1 NVIDIA Nemotron

Role unchanged from P3. The model provider stays replaceable behind an adapter. Meterless is a context layer and not a model gateway, so the adapter calls the model endpoint directly.

### 3.2 Meterless World Model

- One namespace per episode, in-process storage. No state survives the episode.
- Ingests only data on the C1 policy-visible whitelists (Addendum 01, item 4) and the registered text context for that episode's context condition.
- Records each hypothesis, fit, verifier result, authorization, and outcome as entities and relationships with provenance, so that every explanation statement required by P3 Section 16 ("Explanation fidelity") resolves to a stored evidence record.

### 3.3 Meterless H-MEM

- Implements the store list of P3 Section 11: confirmed hypothesis, fitted parameters, evidence used, verifier score, authorization scope, subsequent outcomes, and invalidation.
- One instance per episode with no persistence directory.
- Every record's required `source` field carries the receipt evidence ID.
- The optional miner hook is not used. No model call is made by the memory layer.

### 3.4 Zetaris

- Holds only the registered template-generated text and policy-visible structured events. The static leakage check of P3 Section 12.2 applies to everything loaded into Zetaris.
- B1, B2, and B3 do not consume free-form text and are unaffected.
- Access and interface details are not yet published by the organizer. If the published interface forces a change to anything in Section 2, that change requires a further dated addendum before implementation.

### 3.5 Integration form

The Meterless reference implementations are used unmodified through one long-lived local TypeScript bridge process speaking line-delimited JSON over standard input/output. Python remains the host process.

A pre-window compatibility probe (`probe.py`, `bridge.ts`, about 65 lines, kept outside this repository) was run on 2026-10-09 under P3 Section 21. If any of it is reused, it is declared pre-existing work.

## 4. Integration invariants

These are added to the stop conditions of P3 Section 25. Violating any of them is an implementation defect, not a result.

1. **Shared substrate.** B3 and both B4 variants use the identical World Model, H-MEM, and bridge path. The only difference remains that B3 ignores free-form text.
2. **Substrate-off equivalence.** For B1, B2, and B3, per-object dispositions, issued commands, and verifier receipts are identical with the sponsor substrate enabled and with a plain in-process Python store in its place.
3. **Canonical numeric evidence.** The fitter, verifier, ambiguity gate, and authorization gate read numeric evidence from the canonical policy-visible evidence packet. They never depend on retrieval ranking, relevance scores, or embeddings.
4. **No retrieval filtering of model input.** The LLM receives the full whitelisted evidence packet for the episode. Retrieval may not remove evidence from it.
5. **Deterministic provenance.** Provenance timestamps use simulation time. Wall-clock time and substrate-generated identifiers are excluded from decision logic and from determinism-checked receipt fields.
6. **Not in the fast layer.** No sponsor-substrate call occurs inside the System-1 loop. Calls happen only after escalation, while the simulator is frozen under P3 Section 16, and their latency is reported inside production pause seconds.
7. **No silent context downgrade.** The text context delivered to the policy must match the frozen generated context for that episode and condition by content hash. On mismatch or retrieval failure the episode run is aborted and re-run. It is never silently scored as `NO_TEXT_CONTEXT`.
8. **Disclosed eval mode.** Whether final eval-v3 uses live Zetaris retrieval or a recorded snapshot of it is decided before eval-v3 generation and stated in the result report.

## 5. Cross-episode learning

Cross-episode learning remains out of scope (P3 Sections 11 and 24). Any cross-episode memory demonstration is exploratory, sits outside the registered comparison, and must be labelled as such wherever it is shown.

## 6. Execution roles (amends P3 Section 26)

- Build-window implementation is authored in **Cursor**.
- **Luna / Codex**: verification, evaluation runs, and independent checks during the window.
- ChatGPT, Claude, and Owner roles are unchanged.

## 7. Primary-track decision (amends P3 Section 22)

- The event now has three tracks plus a bonus track. "Connected Agent Context" is now "Solving Fragmented Intelligence". "Autonomous Agent" no longer exists.
- Default design target remains **Reasoning Architecture**.
- The bonus track is now "Wildcard [Tinkerer]" and requires Zetaris and Meterless integration. The default design already includes both, so the Tinkerer fallback stays available.
- Whether one project may be entered as two submissions on different tracks is an open organizer question.
- Track selection remains an owner decision before submission.

## 8. Next gate (amends P3 Section 28)

```text
P3_DESIGN_FROZEN / PREREGISTERED
-> ADDENDUM_02 OWNER DISPOSITION
-> pre-window-freeze tag on the last pre-window main commit
-> WAIT FOR 2026-10-22 00:00 UTC
-> HACKATHON IMPLEMENTATION
```

## 9. Open items

- Organizer confirmation of which rules document is binding, and whether Zetaris, Meterless, and Cursor are mandatory on the main tracks.
- Zetaris, Cursor, and Nemotron access steps (announced by the organizer as "before 22 October").
- Full challenge statement for Reasoning Architecture, not yet visible in the workspace.
- `metadata.json` schema, not yet published.
