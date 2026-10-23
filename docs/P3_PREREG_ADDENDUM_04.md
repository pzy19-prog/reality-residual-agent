# P3 Preregistration Addendum 04 — B4 Call Policy Registration

Status: **BUILD-WINDOW PROTOCOL AMENDMENT / PRE-REGISTRATION BEFORE EVAL-V3 GENERATION / NOT A RESULT**

Date: 2026-10-23

Trigger: P3 Sections 8.3 and 15 define the semantics of B4-strict and B4-tiebreak, but do not register (a) when the B4 hypothesis generator is called, (b) how B4-tiebreak handles an unusable proposal, or (c) how LLM calls are counted. These items were first fixed as implementation rulings before the first B4 development run (L5 implementation, PR #20); the fallback order was revised once after review of that development run. This addendum is written within the build window, after the 33-development-seed subset run. The eval-v3 seed values do not yet exist: `artifacts/h1/final-eval-v3-prohibition.json` records `final_eval_v3_seed_values_created=false` and `final_eval_v3_seed_values_inspected=false`, and `config/eval_seeds_v3.json` is absent. This addendum is not triggered by any eval-v3 result. Under P3 Section 18.2, dated 2026-10-23, this amendment records the B4 call, fallback, counting, and artifact-integrity rules before eval-v3 seed generation because the first development run exposed under-specified call behavior and proposal-format failures, and the reviewed implementation used a reduced evidence packet.

This addendum does not move or rewrite `p3-prereg`, and does not alter `docs/P3_SYSTEM2_DESIGN.md` or Addenda 01–03. Addendum 02 Section 2 is unchanged. Where this addendum and earlier documents differ, this addendum governs only the items listed below.

## 1. B4 call policy

1.1 The B4 hypothesis generator is called at a System-2 decision point if and only if the shared B3 evaluation at that point reports no fault evidence and the ambiguity-gate result is AMBIGUOUS (P3 Section 8.3, item 3). At every other decision point no LLM call is made, and both B4 variants take the B3 action unchanged.

1.2 Request content is governed by Addendum 03 Section 2 item 4 (the full whitelisted evidence packet) and P3 Section 12. This addendum does not narrow it. Free-form text context enters B4 requests only.

1.3 The request body is a deterministic function of the evidence packet and the text context. It does not contain the variant name. Where B4-strict and B4-tiebreak reach a decision point with identical evidence packet and text context, they issue the identical request and share one cached response. The cache key is the SHA-256 of the finalized provider payload.

1.4 LLM output never triggers or clears a fault latch and is never used for parameter fitting, verification, ambiguity gating, or authorization (Addendum 02 Section 6).

1.5 `llm_calls` for a (seed, variant) is the number of proposer requests served to that run, counting replay-cache hits and live calls alike. It is deterministic and part of the receipt. Live-call counts and wall-clock figures are operational cost and are excluded from receipt hashes.

## 2. B4-strict

2.1 At every decision point the B4-strict action equals the B3 action. The proposal is recorded only as a ranking.

2.2 Because B3 is exhaustive over the same 14 structures, ranking order cannot change the B3 result. Equality of B4-strict and B3 decision outcomes therefore holds by construction and is not an empirical finding. The P3 Section 20 test "exhaustive B3 matches both B4 variants" is decided on B4-tiebreak, and the B4-strict row is reported with this label.

## 3. B4-tiebreak selection

When Section 1.1 calls the generator, the following rules are evaluated in order and the first that applies decides:

1. The proposal is unusable (provider or HTTP error, timeout, replay-cache miss, non-JSON output, output not of the form {items: [...]}, schema-validation failure, or truncated output): fall back, `gate_reason = TIEBREAK_FALLBACK:PROVIDER_ERROR` or `TIEBREAK_FALLBACK:INVALID_PROPOSAL`.
2. Scanning proposal items in order, the first item whose ID is either a verifier-passing structure ID or a registered fault-hypothesis ID is a fault-hypothesis ID: fall back, `TIEBREAK_FALLBACK:FAULT_ID`.
3. The proposal contains any ID outside the registered ID set: fall back, `TIEBREAK_FALLBACK:UNKNOWN_ID`.
4. No proposed ID is a verifier-passing structure, including an empty list: fall back, `TIEBREAK_FALLBACK:NO_PROPOSED_PASSING_STRUCTURE`.
5. Otherwise let h be the first verifier-passing structure in proposal order and evaluate the common-action gate on {h} alone. If the result is UPDATE_MODEL_AND_REPLAN, adopt that action and action time, record `gate_reason = TEXT_TIEBREAK`, and pass the action through the unchanged authorization gate. Otherwise fall back with `TIEBREAK_FALLBACK:<common-action reason>`.

A fallback takes the B4-strict action (PAUSE_AND_REOBSERVE under P3 Section 8.3). Fallback reason codes are reporting labels only; every fallback takes the same action. Text can change an action only through rule 5.

## 4. Scored-artifact integrity

Registered B4 results, for development and for eval-v3, are generated by code from a frozen response cache with the network disabled. Live runs only populate the cache. The receipt must be recomputable from the artifact content by the code's own rule, and two consecutive generations must produce identical receipts. Manual post-processing of a scored B4 artifact is prohibited.

## 5. Disclosure: 2026-10-23 development run

5.1 The 386 cached responses of the development run (commit 92e2b89, `artifacts/llm_cache/`): 71 parse as {items: [...]}; 310 parse as JSON but not in the required shape (key names missing, for example `{": [{": "SENSOR_BIAS", ...`); 5 stopped at the token limit (finish_reason=length), 4 with truncated unparseable content and 1 with no content.

5.2 On that run most B4-tiebreak calls fell back as INVALID_PROPOSAL. Differences between B4-tiebreak and B4-strict or B3 on that run are dominated by format failure and are not evidence of a text-context effect.

5.3 That run sent a reduced evidence packet (observations limited to time, observed_x, nominal_x; feedback limited to issued_time, execution_time, accepted, success; no presence events; known configuration limited to dt and tolerance). This does not meet Addendum 03 Section 2 item 4 and is recorded as an implementation defect to be corrected before implementation-candidate freeze. Results of that run are not evidence about B4 under the registered packet.

5.4 Request format (prompt wording, response-format constraint, decoding settings, model identifier) is implementation and may change before implementation-candidate freeze. Such changes must not use eval-v3. B4 receipts record the model identifier and the SHA-256 of the request template.

## 6. Pre-registered reporting rule for eval-v3

6.1 For each B4 variant report: LLM calls; counts of valid proposals, INVALID_PROPOSAL, PROVIDER_ERROR, and truncated outputs; and the gate_reason distribution (TEXT_TIEBREAK and each TIEBREAK_FALLBACK reason).

6.2 If more than 50% of B4-tiebreak generator calls end in TIEBREAK_FALLBACK:INVALID_PROPOSAL or TIEBREAK_FALLBACK:PROVIDER_ERROR, B4-tiebreak results are reported as dominated by proposal-format or provider failure, and no text-context benefit or cost (H3; P3 Section 19 item 6) is claimed from them.

## 7. Added stop conditions (P3 Section 25)

Each of the following is an implementation defect, not a result:

- an LLM call at a decision point not selected by Section 1.1;
- a B4-strict action that differs from the B3 action;
- a B4-tiebreak action change not produced by Section 3 rule 5;
- a scored B4 artifact whose receipt cannot be recomputed from its content, or that was edited after generation.
