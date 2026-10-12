# P3 Preregistration Addendum 03 — 2026-10-12 Recovery of PR #5 Integration Invariants

Status: **PRE-HACKATHON DESIGN AMENDMENT / PRE-REGISTRATION / NOT SCORED WORK**

Date: 2026-10-12

Trigger: the 2026-10-11 rewrite of Addendum 02 did not carry forward some clauses from the 2026-10-09 draft opened as PR #5 and later closed as superseded by PR #7. This addendum registers the applicable recovered clauses before the build window starts. It is not triggered by any evaluation outcome.

This addendum does not move or rewrite `p3-prereg`, and does not alter `docs/P3_SYSTEM2_DESIGN.md` text. It applies on top of Addenda 01 and 02. Where this addendum and P3 or an earlier addendum differ, this addendum governs only the items listed below.

## 1. Official build window

The official build window is **2026-10-22 00:00 UTC through 2026-10-27 23:45 UTC**. References to 2026-10-15 or 2026-10-20 as current build-window or submission-boundary dates are void. This section controls wherever those dates appear in earlier documents.

Source: PR #5 draft §1:

> Every reference to `2026-10-15 00:00 UTC` as the build-window boundary in P3 (header, Section 21, Section 28) and in Addendum 01 is read as `2026-10-22 00:00 UTC`. Every reference to `2026-10-20 23:45 UTC` as the submission deadline is read as `2026-10-27 23:45 UTC`.

Date edits made to docs/P3_SYSTEM2_DESIGN.md and docs/H1_EVAL_FOUNDATION.md by PR #9 were reverted; this section governs those dates.

## 2. Integration invariants

The following clauses from PR #5 draft §4.1, §4.3, §4.4, §4.5, §4.6, and §4.7 are incorporated verbatim from `pr5-only-content.md`. They are added to the stop conditions of P3 Section 25. Violating any of them is an implementation defect, not a result.

Source: PR #5 draft §4.1:

> 1. **Shared substrate.** B3 and both B4 variants use the identical World Model, H-MEM, and bridge path. The only difference remains that B3 ignores free-form text.

Source: PR #5 draft §4.3:

> 3. **Canonical numeric evidence.** The fitter, verifier, ambiguity gate, and authorization gate read numeric evidence from the canonical policy-visible evidence packet. They never depend on retrieval ranking, relevance scores, or embeddings.

Source: PR #5 draft §4.4:

> 4. **No retrieval filtering of model input.** The LLM receives the full whitelisted evidence packet for the episode. Retrieval may not remove evidence from it.

Source: PR #5 draft §4.5:

> 5. **Deterministic provenance.** Provenance timestamps use simulation time. Wall-clock time and substrate-generated identifiers are excluded from decision logic and from determinism-checked receipt fields.

Source: PR #5 draft §4.6:

> 6. **Not in the fast layer.** No sponsor-substrate call occurs inside the System-1 loop. Calls happen only after escalation, while the simulator is frozen under P3 Section 16, and their latency is reported inside production pause seconds.

Source: PR #5 draft §4.7:

> 7. **No silent context downgrade.** The text context delivered to the policy must match the frozen generated context for that episode and condition by content hash. On mismatch or retrieval failure the episode run is aborted and re-run. It is never silently scored as `NO_TEXT_CONTEXT`.

## 3. Evaluation-mode disclosure

As registered in Addendum 02 Section 4.4 (line 85), all registered evaluation runs and baselines B1–B4 use the local reference loader. Evaluation results and submission materials must disclose that evaluation mode. The Zetaris path is exercised in the demo and equivalence receipt; registered evaluation does not use live Zetaris retrieval.

## 4. Explicit exclusions

### 4.1 Tinkerer fallback

Tinkerer is not a fallback track for avoiding the required sponsor integration. Addendum 02 Section 3 states that Tinkerer is no longer a sponsor-integration fallback because rule 5.1 applies to every submission.

### 4.2 Live Zetaris retrieval

All registered evaluation runs and baselines B1–B4 use the reference loader under Addendum 02 Section 4.4. Live Zetaris retrieval is used for the demo and equivalence receipt, not registered evaluation.

### 4.3 Substrate-off equivalence (PR #5 draft §4.2)

Not registered. The equivalence receipt as defined in Addendum 02 governs.
