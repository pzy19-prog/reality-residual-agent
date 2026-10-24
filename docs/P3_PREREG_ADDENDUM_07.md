# P3 Preregistration Addendum 07 — Corrections to Addendum 06 and Pre-freeze Clarifications

Status: **BUILD-WINDOW PROTOCOL AMENDMENT / PRE-REGISTRATION BEFORE EVAL-V3 GENERATION / NOT A RESULT**

Date: 2026-10-24

Trigger: A read-only review on 2026-10-24, together with the FRZ-2A and EVAL-PATH code reviews, found that Addendum 06 disagrees with owner ruling R9 on the request-template placeholder (R9 (a)), and that several run details were not registered. The same check found that the structural holdout has already been used in development (Section 5). Eval-v3 does not yet exist: `artifacts/h1/final-eval-v3-prohibition.json` records `final_eval_v3_seed_values_created=false` and `final_eval_v3_seed_values_inspected=false`, and `config/eval_seeds_v3.json` is absent. Under P3 Section 18.2, dated 2026-10-24, this addendum registers these items before the implementation-candidate freeze tag and before eval-v3 is generated. No development or evaluation result figure is a ground for this addendum.

This addendum does not move or rewrite p3-prereg and does not edit docs/P3_SYSTEM2_DESIGN.md or Addenda 01–06. Where it differs from them, it governs only the items listed below; Section 4.5 amends Addendum 04 Section 6.1 for the incomplete case only.

## 1. Corrections to Addendum 06

1.1 Owner ruling R9 (a). The request-template SHA-256 (Addendum 04 Section 5.4; Addendum 06 Section 4A R9) is computed on the finalized request after the evidence packet, which carries the context text (Section 2, R10), is replaced by the string `"<EVIDENCE_PACKET>"` and the System-2 summary by `"<S2_SUMMARY>"`. Any separate context-text field, if present, is likewise replaced. The hash covers the requested model constant, not the name returned by the service. Canonical JSON means `sort_keys=True`, separators `(",", ":")`, `ensure_ascii=False`, applied after finalization (including the six-decimal rounding of Addendum 05 Section 3.4).

1.2 The implementation-candidate freeze tag X of Addendum 06 Sections 1.2 and 2.3 is `impl-freeze-v3`.

1.3 The cache-key reference in Addendum 06 Section 3.3 is to Addendum 04 Section 1.3.

1.4 The development object referred to in Addendum 06 Section 4.5 is dev seed 88, target 5.

1.5 The seed file lists seeds in the order returned by `sample`, unsorted; list index i is that order (Addendum 06 Section 1.4).

1.6 The frozen context generator of Addendum 06 Section 1.5 is `src/rra/eval/context_v3.py`; text conditions are run in its `VARIANTS` order (`NO_TEXT_CONTEXT`, `HELPFUL_TEXT_CONTEXT`, `IRRELEVANT_TEXT_CONTEXT`, `MISLEADING_TEXT_CONTEXT`); every one of the 100 physical episodes is eligible.

## 2. Generator request content (owner rulings, 2026-10-24)

- R10: The frozen P3 Section 12 context text is carried inside the request as `evidence_packet.context = {text, content_sha256}`. It is the same text, from the same generator, with the same leakage validation as before. Only its position changes, from a separate channel to a sub-object of the packet. `context` is not a C1 field and adds no observable data. This changes only the position of the text relative to the description in docs/H1_EVAL_FOUNDATION.md line 17, where free-form text is a separate channel; the text, its generator, and its leakage validation are unchanged.
- R11: The generator request carries no seed identifier. `episode_id` is removed from the packet's `decision` section and from every row. In command feedback, `command_id` is rewritten from `"{seed}:{target_id}:{step}"` to `"{target_id}:{step}"`. The L3 export, the Zetaris path and their packet hashes keep the original form.
- R12: Keys outside the C1 field names that remain in the request are `schema`, `decision.{target_id, step, time, seq}`, row-level `seq`, feedback-row `step`, `context.{text, content_sha256}`, and the System-2 summary of R6. None of them carries a seed value or a hidden simulator parameter.
- R13: The per-response model record of R9 is the aggregate `served_models = {returned model name: response count}` in the B4 receipt. served_models counts every response served in a generation, including cache hits; in the scored replay it therefore counts every response.
- Feedback precedence (Addendum 06 Section 4.7): a feedback row precedes the decision when its `seq = target_id × episode_steps + step` is strictly less than the decision's `seq`.

## 3. Format-mode probe (Addendum 06 Section 3.2)

3.1 Probe set: requests are collected in the seed order of `artifacts/s2/diag-d1g.json`, then text-variant order, then decision order within the episode. A request is distinct when its finalized `json_object` payload has a SHA-256 not seen before. The first 10 distinct requests form the set.

3.2 A proposal is valid when the adapter returns no error and at least one item remains after unknown IDs are removed. A truncated response (`finish_reason = length`) counts as invalid.

3.3 The probe artifact records the request-template SHA-256 of each mode. If the request template of the selected mode in X differs from the one recorded by the probe, the probe is void and is repeated before X.

3.4 The probe and the development B4 cache are generated on the registered runner.

## 4. Live run, counting, interruption, and incomplete runs (Addendum 06 Sections 2.3, 3.3–3.5)

4.1 Response handling during live calls (owner ruling R14, conforming to Addendum 04 Section 3 rule 1):

- HTTP 200 with a JSON body: the response is cached.
- Deterministic errors: HTTP 3xx, 400, 404, 409, 413, 422, and any other 4xx not listed below. An error record (status code, no credentials) is cached at once in place of a response.
- Transient errors: HTTP 1xx and 2xx other than 200, HTTP 408, 429, 5xx, timeouts, network errors, and HTTP 200 with a non-JSON body. The request is retried up to five attempts in total, with back-off and honouring Retry-After up to 60 s per wait. If it still fails, an error record is cached.
- An error record is final. Replay reproduces the same `PROVIDER_ERROR` fallback, which counts toward Addendum 04 Section 6.2.
- If ten consecutive requests end in error records, the run stops so that it can be resumed after an outage. Those error records are kept. Every error record, deterministic or transient, counts toward the ten. Consecutive means in order of completion across all worker threads, and any successful response resets the count. The count starts at zero in each process, including after a resume.
- HTTP 401 or 403: the run stops without caching. It may be resumed after the credential is corrected.

4.2 Counting: a distinct live request is a finalized-request SHA-256 for which at least one HTTP attempt was made. Each such SHA-256 is appended to `artifacts/eval_v3/live_ledger.jsonl` before its first attempt, and the ledger is never rewritten. Retries and resumptions of the same request do not add to the count. The cap of 2,500 applies to the number of distinct entries in the ledger. The cap is checked before a new entry is appended: when the ledger already holds 2,500 distinct entries, no new request is attempted and the run ends as incomplete. Error records count as live requests. An entry appended before a send that never happened, for example because of a crash, still counts, and a resumed run sends that request without a new entry. A run that finishes with at most 2,500 distinct entries is complete. A run is incomplete for the cap only when it would need a 2,501st distinct request.

4.3 Runs:

- B1, B1-legacy, B2, and B3 are each run once to completion. A run that crashed before writing its result file may be restarted, and the completed run is the result.
- For B4, one registered run consists of the live fill (resumable) followed by two replay generations. The first replay is the scored artifact, and the second must match it.

4.4 Deadline: the live fill is complete when the live command exits with status complete and every request of every (seed, text condition) pair has a cached response or error record. Completion must occur before 2026-10-27 06:00 UTC by the runner clock, as recorded in the receipt. If the fill is complete by then, the replay generations and the result commit may follow after that time. If it is not, live calls stop at that time. The start and completion times are recorded outside the hashed content of the receipt.

4.5 Incomplete B4 (owner ruling R15): if the cap is reached or the deadline passes, no B4 metrics are reported. The B4 rows report the status, the reason, the number of completed (seed, text condition) pairs, and the ledger count. They also report the Addendum 04 Section 6.1 counts that can be computed from the ledger and the cache: LLM calls, and responses classified by the adapter rules as valid, `INVALID_PROPOSAL`, `PROVIDER_ERROR`, or truncated. In this case, "LLM calls" means the number of distinct entries in the live ledger, and the classification uses only the cache records of ledger entries. Counts per B4 variant are not available and are reported as such. The `gate_reason` distribution is reported as "not available (incomplete)". For this case only, this amends Addendum 04 Section 6.1. The B1, B1-legacy, B2, and B3 rows are reported in full.

4.6 Seed visibility: no command output or log prints seed values. The seed file and the seed fields of result files are not opened before every row is complete or declared incomplete. All result artifacts are committed together after that point.

4.7 Artifact locations:

- result files: `artifacts/eval_v3/{b1b3,b2,b1-legacy,b4}.{json,md}`;
- live ledger: `artifacts/eval_v3/live_ledger.jsonl`;
- B4 responses: new files in the shared cache `artifacts/llm_cache/`.

All of these are committed in Z. No existing cache file may be modified or deleted.

## 5. Structural holdout disclosure (P3 Section 13.4)

5.1 The structural holdout `AND(SPEED_STEP,ACTUATOR_DELAY)` (H1 receipt) is composition index 9. The B3 development runs since commit `7ea70ce` (2026-10-22) assign cases by `index mod 19` over the 14 composition structures. The read-only diagnostics built on them do the same. Both therefore include dev seeds 9, 28, 47, 66, 85, 104, and 123 with this structure, contrary to P3 Section 13.4. None of the 33 seeds of the B4 development subset (artifacts/s2/diag-d1g.json) belongs to case 9, and no committed B4 development run used a case-9 seed.

5.2 Eval-v3 keeps the registered assignment. Case 9 results are reported separately, labelled as the structural holdout seen during development, and no claim of composition generalization to an unseen structure is made from eval-v3. This handling is owner ruling R16 (2026-10-24). Choosing a different holdout now would be a post hoc change and is not done.

5.3 Eval-v3 does not include the P3 Section 13.1 V0 known-family scenarios. These were covered by the frozen eval v2 run.

## 6. Added stop conditions (P3 Section 25)

Each of the following invalidates the affected eval-v3 rows until corrected under P3 Section 18.2:

- a generator request containing a seed value or an `episode_id` key;
- a modified or deleted existing cache file in a result commit;
- a missing or rewritten live ledger;
- a B4 scored artifact generated from a cache that lacks a response or error record for any request.
