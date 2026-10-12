# P3 Preregistration Addendum 03 — 2026-10-12 Recovery of PR #5 Integration Invariants

Status: **PRE-HACKATHON DESIGN AMENDMENT / PRE-REGISTRATION / NOT SCORED WORK**

Date: 2026-10-12

Trigger: the 2026-10-11 rewrite of Addendum 02 did not carry forward some clauses from the 2026-10-09 draft opened as PR #5 and later closed as superseded by PR #7. This addendum registers the applicable recovered clauses before the build window starts. It is not triggered by any evaluation outcome.

This addendum does not move or rewrite `p3-prereg`, and does not alter `docs/P3_SYSTEM2_DESIGN.md` text. It applies on top of Addenda 01 and 02. Where this addendum and P3 or an earlier addendum differ, this addendum governs only the items listed below.

## 1. Official build window

The official build window is **2026-10-22 00:00 UTC through 2026-10-27 23:45 UTC**. References to 2026-10-15 or 2026-10-20 as current build-window or submission-boundary dates are void. This section controls wherever those dates appear in earlier documents.

## 2. Integration invariants

The following clauses are incorporated verbatim from PR #5 draft §4.5 and §4.7. They are added to the stop conditions of P3 Section 25. Violating either is an implementation defect, not a result.

Source: PR #5 draft §4.5:

> 5. **Deterministic provenance.** Provenance timestamps use simulation time. Wall-clock time and substrate-generated identifiers are excluded from decision logic and from determinism-checked receipt fields.

Source: PR #5 draft §4.7:

> 7. **No silent context downgrade.** The text context delivered to the policy must match the frozen generated context for that episode and condition by content hash. On mismatch or retrieval failure the episode run is aborted and re-run. It is never silently scored as `NO_TEXT_CONTEXT`.

## 3. Evaluation-mode disclosure

As registered in Addendum 02 Section 4.4 (line 85), all registered evaluation runs and baselines B1–B4 use the local reference loader. Evaluation results and submission materials must disclose that evaluation mode. The Zetaris path is exercised in the demo and equivalence receipt; registered evaluation does not use live Zetaris retrieval.

## 4. Explicit exclusions

### 4.1 Tinkerer fallback

Tinkerer is not a fallback track for avoiding the required sponsor integration. Addendum 02 Section 3 states that Tinkerer is no longer a sponsor-integration fallback because rule 5.1 applies to every submission.

### 4.2 Pending live Zetaris evaluation

There is no pending decision about using live Zetaris retrieval for registered evaluation. Addendum 02 Section 4.4 registers the reference loader for all registered evaluation runs and baselines B1–B4; the Zetaris path is used for the demo and equivalence receipt.
