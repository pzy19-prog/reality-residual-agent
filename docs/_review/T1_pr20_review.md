# T1 review of PR #20 against Addendum 04 (read-only)

Reviewed: PR [pzy19-prog/reality-residual-agent#20](https://github.com/pzy19-prog/reality-residual-agent/pull/20), head `feat/l5b-b4`, base `feat/l5a-hygiene`.
Actual head sha at review time: `c852566db1e10d4e267eb32f3a8f3912d9685db7` (matches the expected `c852566`). Its parent is `92e2b89`, then `ab509d3` (L5a, the PR base).
Reviewed on 2026-10-23 in a cloud VM, Python 3.12.3 venv, numpy 2.5.4, pydantic 2.14.1, pytest 8.4.2.

Labels: **FACT** = observed, with the command or file:line. **UNKNOWN** = could not be determined here, with the reason.
This document states no pass/fail verdict on any result. Items that need that call are listed in the last section.
No existing file was modified. No secret was set or used. All run outputs were written to the session scratch directory, not the repo.

Note on where Addendum 04 lives: `docs/P3_PREREG_ADDENDUM_04.md` is **not** on `feat/l5b-b4` (it landed on `main` via PR #21 after this branch was cut). I read it with `git show origin/main:docs/P3_PREREG_ADDENDUM_04.md`. `git diff --name-only origin/feat/l5a-hygiene` lists no file under `docs/` or `config/`, so the PR touches no preregistration file, addendum or seed file.

## 0. Escalation check (BLOCKED criteria)

FACT: B1 and B3 receipt hashes are **not changed by this PR**. I ran the same episodes on the base tree (`git archive origin/feat/l5a-hygiene` into scratch) and on this head, and compared `receipt_sha256` for B1 (`run_episode(..., terminal_monitoring="corrected")`) and B3 (`system2_enabled=True`) on 12 dev seeds (0, 1, 2, 3, 20, 21, 22, 24, 40, 60, 88, 115).
```
cmp cmp_base.json cmp_head.json  -> identical   (printed B1_B3_HASHES_IDENTICAL)
```
Also, the diff of `src/rra/evidence/episode.py` only adds code gated on `s2_variant in ("B4_STRICT","B4_TIEBREAK")`, plus `chosen = b3.get("tiebreak_selected") or next(...)` (line 770), which reduces to the old expression when the key is absent. `tests/test_b4_episode.py::test_b3_default_and_explicit_variant_have_identical_receipt_hashes` covers the default-versus-explicit B3 case on seed 0 only.

FACT: no preregistration change is needed for the PR to comply, as far as the items below show; the gaps found in §5 are the implementation defect Addendum 04 §5.3 already records.

**FACT, related finding that needs owner attention (not caused by this PR):** the B3 receipt hashes stored in the committed artifacts do **not** reproduce in this VM, on either the base tree or this head. B1 hashes do reproduce.
```
seed:  b1 vs b3-dev.json | b3 vs b3-dev.json | b3 vs b4-dev.json(committed)
0       True              | False             | (seed not in subset)
1       True              | False             | False
2       True              | True              | True
3       True              | False             | False
20, 21, 22, 24, 40, 60, 88, 115: b1 True | b3 False | b3(b4-dev) False
```
- `artifacts/s2/b3-dev.json` (last touched by `ab509d3`, on `main`) and the committed `artifacts/s2/b4-dev.json` agree with each other (e.g. seed 21: `d9b04fd4…` in both), but differ from the value produced by the code here (`6f08b0bf…`).
- The committed artifacts record `runtime_versions` python 3.12.3, numpy 2.5.4, the same as this VM. pydantic version and CPU/BLAS are not recorded.
- Setting `OPENBLAS_NUM_THREADS`/`OMP_NUM_THREADS` to 1 or 4 did not change seed 21's hash.
- Cause: **UNKNOWN**. Candidates I could not test: a different machine/BLAS, a different code state when the artifacts were generated, or something else.
I did not treat this as the "B3/B1 hash changed because of this PR" stop condition, because base and head agree with each other. I am reporting it instead of drawing a conclusion. See §4 for the effect on `--replay`.

## 1. §1.1, §1.3, §1.5: call condition, request body, `llm_calls`

**§1.1 call condition.**
- FACT: `src/rra/evidence/episode.py:650-651`: the proposer is only reached when `s2_variant in ("B4_STRICT","B4_TIEBREAK") and not b3["faults"] and b3["gate_reason"] == "AMBIGUOUS"`. `b3` is the result of `run_b3(...)` at `episode.py:641`, which is the shared B3 evaluation. No other code path calls `proposer.propose` (`grep -n "proposer.propose" episode.py` -> only line 671).
- FACT: for `s2_variant="B3"` nothing in the new block runs, so no call is made (`episode.py:650`).
- FACT: `tests/test_b4_episode.py:51-54` asserts `proposer.calls == number of baseline decisions with no faults and gate_reason == "AMBIGUOUS"` (seed 0 only).
- FACT: if `proposer is None` the code does not call and records `error = "NO_PROPOSER"` (`episode.py:667-669`). For B4_TIEBREAK this yields `gate_reason = "TIEBREAK_FALLBACK:NO_PROPOSER"` (line 691), a label that Addendum 04 §3 does not list.

**§1.3 request body independent of variant name.**
- FACT: the call is `proposer.propose(evidence_packet, text_context)` (`episode.py:671`); the variant name is not passed. The request body is built in `src/rra/llm/adapter.py:67-82` from `evidence_packet` and `context_text` only. The cache key is `request_sha256(finalize_payload(body, settings))` (`src/rra/llm/providers.py:22-48,67-69`), i.e. SHA-256 of the finalized provider payload, as §1.3 says.
- FACT: strict and tiebreak share one `_MemoizedProposer` per (seed, text variant) task (`src/rra/eval/b4_dev.py:63-74,217-223`). Its own memo key is the JSON of `{evidence_packet, context_text}`, which is a separate layer above the payload-SHA cache.
- FACT: the packet sent differs from the one Addendum 03 §2 item 4 and §1.2 require (§5 below), so "request is a function of the registered packet" is not met in content, even though it is met in form.
- FACT (numbers from the committed `artifacts/s2/b4-dev.json`, 132 episodes): proposer invocations strict = 376, tiebreak = 378, requests served = 376. Per episode, served equals the strict invocations in 126 of 132 episodes. I did not trace the other 6; cause UNKNOWN.

**§1.5 `llm_calls`.**
- FACT: the implementation counts `requests_served`, incremented in `_ReadThroughProvider.complete` only after a successful replay hit or a successful live response (`b4_dev.py:40-44,48-52`). A replay-cache miss in replay-only mode, or a live failure, is not counted.
- FACT: the count is per task, i.e. per (seed, text variant), over strict and tiebreak together, because of the shared memo (`b4_dev.py:235-236,302`). In the metrics table `llm_calls` is the sum for `B4_STRICT` and a literal `0` for `B4_TIEBREAK` (`b4_dev.py:119-120`).
- FACT: `llm_calls` and `llm_requests_served` are in the receipt body and are **not** excluded from the hash (`b4_dev.py:326-327` excludes only `runtime_versions` and `operational_cost`). Live-call counts and elapsed time are in `operational_cost`, which is excluded. This matches the §1.5 sentence about excluding live-call counts and wall-clock figures.
- UNKNOWN: whether "the number of proposer requests served to that run" for a (seed, variant) means the per-variant number (each B4 variant separately) or the shared count the code records. Addendum 04 §1.3 says the variants share one cached response; the artifact does not record a per-variant count for B4_TIEBREAK. Listed for the owner.

## 2. §3 rules 1–5: order, implementation, test coverage

FACT: the order in `episode.py:689-722` is: `proposal_error` set -> `PROVIDER_ERROR`/`INVALID_PROPOSAL` (rule 1, lines 690-691) -> scan for the first fault-or-passing ID, fault first -> `FAULT_ID` (rule 2, lines 696-705) -> `receipt.unknown_ids` non-empty -> `UNKNOWN_ID` (rule 3, lines 706-707) -> no selected passing structure -> `NO_PROPOSED_PASSING_STRUCTURE` (rule 4, lines 708-709) -> `common_action([selected], ...)` and `UPDATE_MODEL_AND_REPLAN` -> `TEXT_TIEBREAK`, otherwise `TIEBREAK_FALLBACK:<reason>` (rule 5, lines 710-722). Order matches §3 rules 1 to 5.

Details of each rule against the code:
| rule | implementation detail | FACT/UNKNOWN |
|---|---|---|
| 1 | The exception type name decides the label: `ValueError`, `TypeError`, `ValidationError`, `JSONDecodeError` -> `INVALID_PROPOSAL`; any other exception name -> `PROVIDER_ERROR` (`episode.py:676-681`). The adapter converts `ValueError, TypeError, JSONDecodeError, ValidationError, RuntimeError, OSError` into `Proposal.error = "<Type>: <msg>"` (`adapter.py:107-108`). `ReplayCacheMiss` subclasses `FileNotFoundError` (`providers.py:51`), so it is caught as `OSError` and labelled `PROVIDER_ERROR`. | FACT |
| 1, truncated output | The code does not read `finish_reason`. Truncation is detected only if the content fails to parse. I classified all 386 cached responses offline through `HypothesisProposer` with a stub provider: 310 `ValueError`, 71 valid, and the 5 `finish_reason=length` records give 4 `JSONDecodeError` + 1 `ValueError`, i.e. all five are `INVALID_PROPOSAL`; none of the 5 parses. A truncated response that still parsed as `{items:[...]}` would be accepted. | FACT for the cache; UNKNOWN for future responses |
| 2 | Loop over `ranked_ids`; breaks on the first ID that is a `FaultHypothesis` value (6 values in `src/rra/s2/dsl.py:11-17`) or a passing structure. Unknown IDs were already removed from `items` by the adapter (`adapter.py:99-101`), so the scan is over registered IDs only. | FACT |
| 3 | Uses `proposal.receipt["unknown_ids"]`, which the adapter fills. It is evaluated after rule 2, as the addendum orders them. | FACT |
| 4 | `selected is None` after the scan, including an empty list. | FACT |
| 5 | `common_action([selected], current_time, dt, horizon, tolerance, error=prediction_error)` (`episode.py:711-715`); on `UPDATE_MODEL_AND_REPLAN` the action and time are adopted and the existing authorization path still runs (`episode.py:770` onward; `test_b4_episode.py:57-78` checks authorization ids). Otherwise the label is `TIEBREAK_FALLBACK:<tie_reason>`. With one row, `common_action` can only return `NO_SAFE_ACTION` as the non-update reason (`src/rra/s2/verifier.py:33-44`). | FACT |
| fallback action | On any fallback `b3["action"]` is not modified, so the B3/strict action (PAUSE_AND_REOBSERVE) stands; only `gate_reason` changes. | FACT |

Coverage by `tests/test_b4_episode.py` (5 tests, all passed in §8):
| test (line) | what it exercises |
|---|---|
| `test_b4_strict_preserves_b3_decisions_and_records_proposal_rank` (39) | §1.1 call count and §2.1 strict==B3 decisions, seed 0 |
| `test_b4_tiebreak_authorizations_still_pass_through_authorize` (57) | rule 5 positive path (`TEXT_TIEBREAK` exists, seed 21) and that its authorization comes from `authorize` |
| `test_b4_tiebreak_falls_back_when_proposal_contains_fault_id` (81) | rule 2 |
| `test_b4_tiebreak_falls_back_when_proposal_contains_unknown_id` (103) | rule 3 (injects `receipt.unknown_ids` directly, not via the adapter) |
| `test_b3_default_and_explicit_variant_have_identical_receipt_hashes` (124) | B3 unchanged when `s2_variant="B3"`, seed 0 |

FACT, not covered by any test in the PR: rule 1 (provider error and invalid proposal at episode level), rule 4 (`NO_PROPOSED_PASSING_STRUCTURE`), the rule 5 fallback branch (`TIEBREAK_FALLBACK:<common-action reason>`, e.g. `NO_SAFE_ACTION`), the 2-before-3 ordering when both a fault ID and an unknown ID are present, `NO_PROPOSER`, and §1.3/§1.5 behaviour in `b4_dev.py` (`grep -rn "b4_dev\|_MemoizedProposer" tests` returns nothing outside `test_b4_episode.py`, which does not import it). The committed artifact does contain rule-1 and rule-5 fallbacks in its metrics (`INVALID_PROPOSAL`, `PROVIDER_ERROR`, `NO_SAFE_ACTION`), so those paths ran in the dev run without a unit test.

## 3. §2 B4-strict equals B3 by construction

- FACT: `s2_variant` appears at `episode.py:61, 121, 650, 689, 1085` only (`grep -n s2_variant`). Inside the B4 block, the strict branch does `s2_proposal_rank.append(...)` and nothing else; every mutation of `b3` (`gate_reason`, `action`, `action_time`, `tiebreak_selected`) is under `if s2_variant == "B4_TIEBREAK":` (line 689).
- FACT: the one other thing the strict branch can do is `raise SystemExit` on HTTP 401/403 from a live provider (`episode.py:672-674`); that stops the run and does not change an action.
- FACT: the receipt gets `s2_variant` and `system2_proposal_rank` keys for B4 (`episode.py:1085-1087`); `system2_decisions` is built from the same `b3` fields as for B3.
- FACT (empirical, committed artifact): `B4_STRICT_decisions_sha256 == B3_decisions_sha256` in 132 of 132 episodes. In my replay run (see §4) the same equality holds, 132 of 132, although that run's B3 values differ from the committed ones.
- Test: `test_b4_strict_preserves_b3_decisions_and_records_proposal_rank` checks seed 0 only; `b4_dev.py:224-225` raises `AssertionError("B-1 mismatch ...")` if strict decisions differ from B3 within the run.

## 4. §4 scored-artifact integrity

Commands (Python 3.12 venv, no key variables set; `env | grep -c -E "NVIDIA|ZETARIS"` printed 0; outputs in the session scratch dir):
```
PYTHONPATH=src python -m rra.cli s2-b4-dev --replay --subset --output-dir $S/out/sub1     # run A
PYTHONPATH=src python -m rra.cli s2-b4-dev --replay --subset --output-dir $S/out/sub2     # run B
PYTHONPATH=src python -m rra.cli s2-b4-dev --replay           --output-dir $S/out/full1   # the command as written in the task, run A
PYTHONPATH=src python -m rra.cli s2-b4-dev --replay           --output-dir $S/out/full2   # run B
```
Why both: the committed `artifacts/s2/b4-dev.json` has `"subset": true`, 33 seeds (`seed_identity.path = artifacts/s2/diag-d1g.json`). The command without `--subset` runs all 130 dev seeds, so its hash cannot equal the committed one. I ran the subset form as the like-for-like comparison and the full form as instructed.

FACT, subset form (both runs completed, ~13 min each, exit 0):
| item | value |
|---|---|
| `receipt_sha256` run A | `39e3a9e3f8e2a30dde0dceb087241cf736db70a4be2f1b70927eb2d2d5cd866d` |
| `receipt_sha256` run B | `39e3a9e3f8e2a30dde0dceb087241cf736db70a4be2f1b70927eb2d2d5cd866d` |
| A == B | **yes** |
| committed `artifacts/s2/b4-dev.json` `receipt_sha256` | `b23231e1e0ea2fb95c3f52ad19bdb8e37068aa87e0c8aa2e2212dd11862231a6` |
| replay == committed | **no** |
| `llm_calls`, replay vs committed | 62 vs 376 |
| tiebreak-side proposal errors, replay vs committed | `PROVIDER_ERROR` 316, `INVALID_PROPOSAL` 44, no error 16 vs `INVALID_PROPOSAL` 309, no error 64, `PROVIDER_ERROR` 5 |
| `N_amb` | 116 vs 116 (equal) |
| `B3_receipt_sha256` equal per episode | no (see §0); only the episodes whose B3 hash matched agree |
| `strict_receipt_sha256` equal per episode | 12 of 132 |

- FACT: `--replay` did **not** fail on cache misses. A miss is caught in the adapter as an `OSError` and becomes a `PROVIDER_ERROR` proposal, then `TIEBREAK_FALLBACK:PROVIDER_ERROR` (`adapter.py:107-108`, `episode.py:676-691`). The run exits 0 and writes a receipt. I did not bypass this.
- FACT: in the committed artifact, `operational_cost.live_llm_calls = 0` and `llm_calls = 376`, i.e. the committed run itself was served entirely from the cache.
- FACT: `artifacts/llm_cache/` has 386 records at this head (`ls | wc -l`); 384 were added by this PR (`git diff --stat origin/feat/l5a-hygiene -- artifacts/llm_cache`). The committed run served 376 of them; the replay run served 62.
- FACT: for one episode (seed 21, `NO_TEXT_CONTEXT`, B4_STRICT) replaying against the cache gave 0 hits and 6 misses; the finalized payload differs in `messages` (the evidence-packet content), not in model or settings. I did not establish why the packet values differ (a first nearest-record comparison I tried matched records loosely, so I do not rely on it).
- UNKNOWN: why the packets produced here differ from those that were cached. This is consistent with the B3 hash difference in §0 (the packet includes B3 `passing` rmse values) but I did not show the link.
- FACT (recompute rule): recomputing the hash from the committed JSON content, using `hash_input = all keys except runtime_versions, operational_cost, receipt_sha256`, gives `b23231e1…` = the stored value, so the stored receipt is consistent with its own content. This is not the same as regenerating it (the first check passes; the second does not reproduce in this VM).

FACT, full form as written in the task (no `--subset`; both runs completed, ~52-53 min each, exit 0):
| item | value |
|---|---|
| `receipt_sha256` run A | `349cee4f3d393a5cb5cdabfed3d3fad9063436f2f41bd98a0f101c61ca5e8674` |
| `receipt_sha256` run B | `349cee4f3d393a5cb5cdabfed3d3fad9063436f2f41bd98a0f101c61ca5e8674` |
| A == B | **yes** |
| equal to committed `b23231e1…` | no, and not expected: 130 seeds / 520 episodes (`subset: false`) against the committed 33 seeds / 132 episodes |
| `llm_calls` | 62 (same figure as the subset run; the cache only covers subset seeds) |
| `N_amb` | 374 |
| tiebreak-side proposal errors | `PROVIDER_ERROR` 1148, `INVALID_PROPOSAL` 44, no error 16 |
| strict decisions sha == B3 decisions sha (same run) | 520 of 520 |
FACT: so for seeds outside the 33-seed subset, every generator call is a cache miss and becomes `PROVIDER_ERROR`; the run still exits 0.


## 5. Evidence packet versus Addendum 03 §2 item 4

Requirement text (Addendum 03 §2 item 4, quoting PR #5 draft §4.4): "The LLM receives the full whitelisted evidence packet for the episode." The whitelist is the C1 list in Addendum 01 item 4 (`docs/P3_PREREG_ADDENDUM_01.md:8`), implemented as the dataclasses in `src/rra/evidence/policy.py:10-47`.

Packet built at `src/rra/evidence/episode.py:652-668` (plus `text_context` as `context_text`). Field-by-field:
| whitelist group | whitelisted fields | in packet | **missing** |
|---|---|---|---|
| observation samples | `target_id`, `step`, `time`, `observed_x`, `observed_y`, `nominal_x`, `nominal_y`, `nominal_speed` | `time`, `observed_x`, `nominal_x` | `target_id`, `step`, `observed_y`, `nominal_y`, `nominal_speed` |
| target presence events | `target_id`, `step`, `time`, `target_observed` | none | all four fields (the whole group) |
| known config | `dt`, `tolerance`, `x_pick`, `y_pick`, `belt_speed` | `dt`, `tolerance` | `x_pick`, `y_pick`, `belt_speed` |
| command feedback | `command_id`, `target_id`, `issued_time`, `execution_time`, `accepted`, `success`, `reason_code` | `issued_time`, `execution_time`, `accepted`, `success` | `command_id`, `target_id`, `reason_code` |

FACT, additional content in the packet that is not in the C1 whitelist lists: `passing` (per passing structure: `structure_id`, `rmse`, `n_usable`, derived from the B3 verifier), `current_time`, `horizon` (`episode.py:652-667`). I make no statement on whether these are acceptable; Addendum 04 §1.2 says the request content is governed by Addendum 03 §2 item 4 and P3 §12.
FACT: the free-form text context is delivered separately as `context_text`, only for B4 requests (`adapter.py:78-81`; `b4_dev.py:218-223`).
FACT: Addendum 04 §5.3 describes the dev run's packet as reduced in exactly these fields and calls it "an implementation defect to be corrected before implementation-candidate freeze"; the packet at `c852566` is still that reduced form. I confirmed this by reading the code, not by inspecting a stored request: the cached requests contain the same `observations` keys (`time`, `observed_x`, `nominal_x`).

## 6. §5.4 model identifier and request-template SHA-256 in receipts

- FACT: the committed `artifacts/s2/b4-dev.json` top-level keys are `schema_version, subset, seed_identity, episode_count, text_variants, N_amb, estimated_llm_calls, serial_parallel_check, llm_requests_served, llm_calls, metrics, episodes, runtime_versions, operational_cost, receipt_sha256`. A recursive key walk found no key containing `model`, `template` or `prompt`. **The B4 receipt does not record a model identifier or a request-template SHA-256.**
- FACT: `src/rra/eval/b4_dev.py` imports `NIM_MODEL` (line 22) but uses it only to construct `ReplayProvider` (line 31); it is not written into `body` (lines 304-325).
- FACT: the model identifier does exist in the cache records. All 386 `request.model` values are `nvidia/nemotron-3.5-super-vl-120b-a12b`; all 386 `response.model` values are `private/nvidia/nemotron-3.5-super-120b-a12b`. The system prompt text is a single variant across all 386 records. The cache key (file name) is the SHA-256 of the whole finalized payload, which includes the evidence packet, so it is not a template-only hash.
- UNKNOWN: what "SHA-256 of the request template" is meant to hash (system prompt only, or the whole request with the packet slots empty). No code computes one.
- FACT (model name comparison, recorded only): `NIM_MODEL` at `src/rra/llm/providers.py:14` is `nvidia/nemotron-3.5-super-vl-120b-a12b`. `decisions.md:31` records the server-returned model name as `private/nvidia/nemotron-3.5-super-120b-a12b`. The strings differ (`private/` prefix; `-vl-` segment). The 386 cached responses carry the `private/…` form, matching `decisions.md`.

## 7. `operational_cost.historical_live_run` and the missing report

- FACT: `b4_dev.py:315-324` writes `operational_cost.historical_live_run = {"source_commit": "92e2b89", "live_llm_calls": 376, "note": "transcribed from REPORT_D3_L5B.md"}`. The same text is in the committed artifact (`artifacts/s2/b4-dev.json:13129`).
- FACT: `operational_cost` is excluded from the hash: `hash_input = {k: v for k, v in body.items() if k not in ("runtime_versions", "operational_cost")}` (`b4_dev.py:326-327`). Check: I changed `historical_live_run.live_llm_calls` to 999 and `elapsed_seconds` to 1 on an in-memory copy of the committed JSON and recomputed; the hash was unchanged (`True`).
- FACT: `REPORT_D3_L5B.md` is not in the repository: `git ls-tree -r --name-only HEAD | grep -i report` returns nothing, and `git log --all -- REPORT_D3_L5B.md REPORT_D1.md` returns no commit. The only mentions are the two lines above (`git grep REPORT_D3_L5B HEAD`).
- FACT: the transcribed `376` equals the committed artifact's `llm_calls` (376), but the artifact's own `live_llm_calls` is 0. §5.1 of Addendum 04 gives 386 cached responses for commit 92e2b89 and does not give a live-call figure. I could not check the 376 against a source.

## 8. Full test suite on this branch

Command (repo root, Python 3.12.3 venv): `python -m pytest -q -p no:cacheprovider -rs`
```
192 passed, 4 skipped in 274.87s (0:04:34)
SKIPPED tests/test_meterless_bridge.py:219/240/249  needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED tests/test_packet_sources.py:48             Zetaris live checks are opt-in
```
FACT: 0 failed. Compared with the T0 audit's main run (187 passed, 4 skipped), the extra 5 passes are the 5 tests in `tests/test_b4_episode.py`. `git status --short` was empty after the runs.

## Items for the owner to decide (no verdicts stated here)

1. B3 receipt hashes stored in `artifacts/s2/b3-dev.json` and `artifacts/s2/b4-dev.json` do not reproduce in this VM on either the base tree or this head, while B1 hashes do (§0). Whether that is an environment difference, a stale artifact, or something else.
2. Whether a `--replay` run that silently turns cache misses into `PROVIDER_ERROR` fallbacks (exit 0, new receipt) is compatible with Addendum 04 §4 and §3 rule 1, which lists "replay-cache miss" among unusable proposals (§4).
3. Whether the committed subset artifact (`b23231e1…`) should be considered reproducible given that two consecutive replays here agree with each other (`39e3a9e3…`) but not with it.
4. Whether the reduced evidence packet (§5) is acceptable at this stage given Addendum 04 §5.3.
5. What per-variant `llm_calls` means for B4_TIEBREAK given the shared memo, and whether the unregistered `TIEBREAK_FALLBACK:NO_PROPOSER` and `TIEBREAK_FALLBACK:NO_SAFE_ACTION` labels are acceptable (§1).
6. Whether the missing model identifier and request-template SHA-256 in the receipt (§6) and the missing `REPORT_D3_L5B.md` (§7) need action before freeze.
7. Whether the untested rules listed in §2 need tests before freeze.
