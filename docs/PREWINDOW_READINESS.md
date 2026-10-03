# RRA pre-window readiness and build-window execution

Updated: 2026-10-04 (Asia/Shanghai)  
Status: **PLAN / NOT AN IMPLEMENTATION RECEIPT**  
Verified repository subject: `b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0`  
Tree: `b09e503a86817524325f6993785f7387cd0e1493`  
Parents: `38f8ce139bf90de659a192f4456821dcff0db4a8`, `01716bfba693674d79a316bf312ce74e0289077f`.

## Verified progress

| Component | Status and evidence |
|---|---|
| V0 and REPAIR-04 | Present on the verified main; see [REPAIR-04](../diag/REPAIR-04.md) |
| P3 preregistration | Existing `p3-prereg` design and [P3_SYSTEM2_DESIGN.md](P3_SYSTEM2_DESIGN.md); remains frozen |
| H1 foundation | Merged through `01716bf`; see [H1_EVAL_FOUNDATION.md](H1_EVAL_FOUNDATION.md) and [Addendum 01](P3_PREREG_ADDENDUM_01.md) |
| H1 B2 choice | Frozen fallback `T=1.15 s`, `R=2.15`; see [grid receipt](../artifacts/h1/b2-grid.json) |
| Structural holdout | `AND(SPEED_STEP,ACTUATOR_DELAY)`; see [holdout receipt](../artifacts/h1/structural-holdout.json) |
| Main CI | [Run 36594617566](https://github.com/pzy19-prog/reality-residual-agent/actions/runs/36594617566): 61 passed in 86.42 s; dev benchmark two-run comparison passed |
| System-2 / RRA NIM adapter / B3 / B4 | Not present in the verified main; reserved for the build window |
| Final eval-v3 seed realization | Absent from the verified main; H1 [prohibition receipt](../artifacts/h1/final-eval-v3-prohibition.json) is historical evidence |
| Independent NIM preflight | **UNVERIFIED**: no completion receipt available in this review; a task prompt or prior key-storage claim is not a successful preflight |

Repository evidence does not prove the state of any local worktree, secret store or unsynced preflight directory.

## Work before the build window

| Priority | Work | Completion evidence |
|---|---|---|
| P0 | Resolve current rule uncertainties | Expanded current rules or HackOS instructions covering the questions in [rules review](HACKATHON_RULES_REVIEW_20261004.md) |
| P0 | Restore local development environment | Separate recovery session: Cursor + WSL + dedicated worktree; compare local and remote state before synchronization; inspect unsynced changes; dependency/test/dev-smoke receipt |
| P1 | Independent NIM compatibility check | Separate directory/context, authentication, JSON/schema behavior, 20-request stability, latency, long-input behavior, observed 429/5xx/timeout handling and rate/credit constraints |
| P1 | Complete pre-existing declaration | [HACKATHON_BASELINE.md](../HACKATHON_BASELINE.md) includes V0, P3 design, CI and H1 |
| P1 | Final pre-window freeze | After documentation review and accepted readiness checks, fresh-read main and create a new `pre-hackathon-freeze` tag on the accepted commit |
| P2 | Prepare demo and submission outline | Storyboard and checklist only; implementation, final recording and eval remain build-window work |

The independent NIM experiment uses generic compatibility fixtures. It must not read/modify RRA or pre-build the adapter, EvidencePacket, hypothesis generator, fitter/verifier, authorization gate or recovery loop. Record observed errors honestly; absence of a 429/5xx is not proof of handling. Do not deliberately exhaust credits. No keys or credential-store exports enter the repository.

The freeze tag is **pending**. Do not move `v0-baseline` or `p3-prereg`. Any change after the new freeze and before the build window must still be declared as pre-existing and requires an explicit accounting update; tag distance alone never proves eligibility.

## Build-window sequence

All stages below are planned. Start only after the official opening and owner build authorization, with exact-subject architecture review/acceptance confirmed. The current planning window is 2026-10-15 08:00 through 2026-10-21 07:45 Asia/Shanghai; fresh-check organizer changes before starting.

| Stage | Deliverable | Acceptance gate |
|---|---|---|
| H2 | Shared deterministic fitter, verifier, ambiguity gate and bounded authorization/revocation; exhaustive B3 | Dev-only behavior checks; minimum six usable observations and RMSE <= 0.030; no hidden truth in policy inputs; no bypass of controller speed/x/y limits; scoped expiry and stale-authorization rejection; B3 covers all 14 registered structures without an artificial budget cap |
| H3 | Replaceable model adapter and B4-strict/B4-tiebreak | Same fitter/verifier/action machinery as B3; schema validation; bounded model requests; malformed/failed/timeout responses cannot grant recovery; text never becomes unchecked action authority |
| H4 | Integrated dev validation and minimal visual demo | Report B1/B2/B3/B4 comparisons, misleading-context and refusal/pause paths, fixed challenge/preservation populations, unsafe actions, regressions and wall-clock latency; keep B2 and holdout frozen |
| H5 | Candidate freeze followed by final blind evaluation | Under P3 §18.1: freeze the accepted implementation, then generate final eval-v3 seeds in an isolated process/context; record subject, seeds and results; no tuning from final outcomes |
| H6 | Submission package | New-work declaration, reproducible deployment/container, final results, failure modes and demo; verify current form requirements and submit before the official deadline |

CLI interfaces for H2–H6 do not exist yet. Define concrete acceptance commands in each bounded implementation task after inspecting the then-current code; do not present proposed commands as executable today.

If a failure after final eval requires implementation changes, retain the failed subject/results and obtain a dated protocol disposition before any rerun. Do not silently recycle evaluated seeds as a new blind result.

## Minimum demo storyboard

1. Show the conveyor task, intended user and existing fast-layer boundary.
2. Show observable residuals plus operational text, with no simulator truth.
3. Show multiple hypotheses and a deterministic rejection.
4. Show evidence-bound authorization, bounded command and successful recovery.
5. Show a missing target, invalidating fault or misleading context where recovery is refused or paused.
6. Show the evidence → hypothesis → verification → authorization/disposition receipt and baseline comparison.

Aim for at most three minutes under the historical requirement, pending current-rule verification. Do not fabricate results or present a replay as a live model call.

## Scope and handoff

Protect the end-to-end recovery/refusal loop, deterministic verification, authorization boundary, B2/B3 comparisons, final evaluation and minimal demo. Cut broad UI polish, complex memory, cross-episode learning and extra primitives first.

This documentation work does not recover the user's local environment, run NIM requests, select a track in HackOS, create a freeze tag, authorize pre-window System-2, or submit the project.
