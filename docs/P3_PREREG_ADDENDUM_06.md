# P3 Preregistration Addendum 06 — Eval-v3 Shape, Run Order, B4 Generator Configuration, and Pre-freeze Disclosures

Status: **BUILD-WINDOW PROTOCOL AMENDMENT / PRE-REGISTRATION BEFORE EVAL-V3 GENERATION / NOT A RESULT**

Date: 2026-10-24

Trigger: P3 Section 18.1 and `docs/EVAL_PROTOCOL.md` specify the handling order for eval-v3 but do not register its seed count, generation method, run commands, B4 generator format mode, or call cap. Several implementation decisions also remain to be registered before freeze (Q7). Eval-v3 does not yet exist: `artifacts/h1/final-eval-v3-prohibition.json` records `final_eval_v3_seed_values_created=false` and `final_eval_v3_seed_values_inspected=false`, and `config/eval_seeds_v3.json` is absent (Q2). Under P3 Section 18.2, dated 2026-10-24, this addendum records those items before eval-v3 generation.

This addendum does not move or rewrite `p3-prereg`, and does not alter `docs/P3_SYSTEM2_DESIGN.md` or Addenda 01–05. Where this addendum and earlier documents differ, this addendum governs only the items listed below.

## 1. Eval-v3 seed set

1.1 Eval-v3 consists of 100 seeds: 100 distinct integers drawn without replacement from `[10000, 2147483647)` with the operating-system CSPRNG (`secrets.SystemRandom().sample`). The range does not overlap dev (0–129), eval v1 (1000–1099), or eval v2 (2000–2099).

1.2 The seeds are generated once, by the repository script `scripts/gen_eval_v3_seeds.py` of the frozen implementation candidate, in a single process on the registered runner (Section 2.1), after the implementation-candidate freeze tag exists. The script writes `config/eval_seeds_v3.json` and prints only the seed count and the file's SHA-256; it refuses to run if the file already exists, if the working tree is not clean, or if `HEAD` is not the freeze-tag commit.

1.3 The seed file is committed alone, in one commit whose parent is the freeze-tag commit. No person or agent inspects the seed values before all registered baselines have been run; the values then appear in the result receipts.

1.4 Episode assignment follows the development runs: the seed at list index i is realized with case `i mod 19` (the 14 registered composition structures, then the 5 fault families). With 100 seeds, cases 0–4 have six physical episodes and cases 5–18 have five; per-case counts are reported.

1.5 Each physical episode is run under the four paired context conditions of P3 Section 12.2 with the frozen context generator used in development. B1, B1-legacy, B2, and B3 ignore text and are run once per physical episode.

## 2. Runner, rows, and run order

2.1 The registered runner (Addendum 05 Section 4) is the owner's local machine: x86_64, Intel Core i7-10750H, Python 3.12.3, NumPy 2.5.4, scipy-openblas 0.3.34.

2.2 Result rows: B1 (corrected), B2, B3, B4-strict, B4-tiebreak (primary), and B1-legacy (diagnostic), as in P3 Section 15. B2 uses the frozen pair T = 1.15, R = 2.15 read from `artifacts/h1/b2-grid.json`.

2.3 Order: (a) implementation-candidate freeze tag X; (b) seed commit Y with parent X (Section 1.3); (c) every row run exactly once from the commands of X; (d) result artifacts committed in one or more commits Z after Y. `git diff X..Z -- src/` is empty. EVAL_PROTOCOL rule 1 (“frozen in their own commit before the implementation they measure”) is read together with P3 Section 18.1: the seeds are frozen before any run of the implementation they measure, and the implementation candidate is frozen first.

2.4 Results are recorded as produced. No implementation, threshold, prompt, format mode, or seed change is made in response to eval-v3 results (P3 Section 18.1 item 7).

## 3. B4 generator configuration and call limits

3.1 The requested model is `NIM_MODEL` in X. The model identifier returned by the service is recorded per response.

3.2 Format mode selection (dev only, before X): on the probe set (the first 10 distinct B4 requests collected in seed order and text-variant order on the 33-seed development subset), each format mode (`json_object`, `json_schema`, `nvext_guided_json`) is sent once per request. The mode with the most valid proposals (non-empty items and no error under the adapter rules) is selected; ties are broken in the order `json_object`, `json_schema`, `nvext_guided_json`. The selected mode becomes the default in X, and the probe artifact is committed before X. Addendum 04 Section 6.2 applies regardless of the selected mode's probe score.

3.3 Live calls on eval-v3 go through the read-through cache keyed by the finalized request (Addendum 04 Section 4; Addendum 05 Section 3.4) and may be resumed after an interruption. HTTP 401 or 403 stops the run. At most 2,500 distinct live requests are made for eval-v3.

3.4 The scored B4 artifact is generated afterwards in replay mode from the filled cache, twice, with identical receipts (Addendum 04 Section 4; Addendum 05 Section 3.1).

3.5 If the cap in Section 3.3 is reached, or the live run cannot be completed by 2026-10-27 06:00 UTC, the B4 rows are reported as incomplete with the number of completed (seed, text condition) pairs. No B4 benefit or cost is claimed from an incomplete run. The B1, B1-legacy, B2, and B3 rows are reported in full.

## 4. Implementation decisions registered before freeze

These were fixed during development and are not triggered by any eval-v3 result.

4.1 A hard-fault latch is set even when the fault evidence window is empty (commit `71ce80d`, from review of fail-closed behavior).

4.2 The L3 equivalence receipt resolves `base_git_sha` at run time (commit `afa2aa6`).

4.3 Grid ties (Addendum 05 Section 2) in a two-dimensional fit select the lexicographically smallest (tau, delay) pair.

4.4 Re-observation hold (Addendum 05 Section 1): the hold is entered only on the fast-layer `ESCALATE` path; `PAUSE_AND_REOBSERVE` decisions triggered by an infeasible correction or by episode-level outcome escalation do not enter a hold. A target that already has a terminal outcome does not enter a hold. The re-evaluation due test uses a 1e-9 s tolerance. The pick-window end is the nominal plan arrival time plus dt/2 and is checked at re-evaluation samples.

4.5 When a held target is authorized and no hold and no fault latch remain, the safe stop is cleared, including a safe stop set earlier for another reason (one development object). This reading of Addendum 05 Section 1.3 is retained and disclosed.

4.6 The episode-level safe stop, which prevents commands for the rest of an episode after an escalation or latch, is unchanged by Addendum 05 and this addendum.

4.7 The B4 request carries the canonical evidence packet built by the same function used in L3, with the following scope (owner ruling R7): observations and presence events of the current target with all C1 fields; all command feedback in the episode that precedes the decision (no later feedback); and `known_config` restricted to the five C1 fields (`dt`, `tolerance`, `x_pick`, `y_pick`, `belt_speed`). The L3 export tables additionally carry `episode_steps` and `object_count`, which L3 uses for storage and sequence numbering. These two fields are not C1 fields and are not sent to the generator. Restricting `known_config` to C1 does not remove evidence in the sense of Addendum 03 Section 2 item 4. Rows keep the L3 bookkeeping keys `episode_id` and `seq`, and feedback rows also keep `step`. The request also carries a derived System-2 summary that contains exactly the items of owner ruling R6: the passing structures (`structure_id`, `rmse`, `n_usable`), `current_time`, and `horizon`. This corrects the reduced packet disclosed in Addendum 04 Section 5.3.

## 4A. Owner interpretive rulings (2026-10-24)

These rulings interpret existing clauses before eval-v3 generation. They change no threshold, gate, scoring rule, or denominator, and none is triggered by an eval-v3 result.

- R1: Re-observation hold entry is limited to the fast-layer `ESCALATE` path (Section 4.4).
- R2: The safe-stop reading of Addendum 05 Section 1.3 is retained and disclosed (Section 4.5).
- R3: The episode-level safe stop is outside this freeze and is disclosed as a failure mode (Section 4.6).
- R4: Registered runner (Section 2.1).
- R5: Addendum 05 Section 3.4 is implemented on the registered runner, and the B4 cache is rebuilt live there.
- R6: The B4 request keeps the passing structures (`structure_id`, `rmse`, `n_usable`), `current_time`, and `horizon`. B4-tiebreak selects among verifier-passing structures and cannot do so without them.
- R7: Scope of "the full whitelisted evidence packet for the episode" (Addendum 03 Section 2 item 4), as stated in Section 4.7.
- R8: Two-dimensional grid ties under Addendum 05 Section 2 select the lexicographically smallest (tau, delay) pair (Section 4.3).
- R9: The request-template SHA-256 of Addendum 04 Section 5.4 is the SHA-256 of the canonical JSON of the finalized request in which the evidence packet and the System-2 summary are replaced by fixed placeholders; it covers the system prompt, model name, generation parameters, response-format settings, and chat-template arguments. The model identifier recorded per response is the name returned by the service; the requested code constant is recorded separately.

## 5. Added stop conditions (P3 Section 25)

Each of the following invalidates the affected eval-v3 rows until corrected under P3 Section 18.2:

- a seed file created before the freeze tag, or committed together with any other change;
- any `src/` change between X and a result commit;
- seed values inspected before all rows are run;
- a scored B4 artifact whose two replay generations differ, or that contains a replay-cache-miss fallback;
- more than 2,500 distinct live eval-v3 requests.
