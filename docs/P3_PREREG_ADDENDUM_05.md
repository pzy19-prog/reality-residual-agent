# P3 Preregistration Addendum 05 — Re-observation Hold, Replay Abort, and Determinism Scope

Status: **BUILD-WINDOW PROTOCOL AMENDMENT / PRE-REGISTRATION BEFORE EVAL-V3 GENERATION / NOT A RESULT**

Date: 2026-10-24

Trigger: This addendum is written within the build window, after development-set diagnostics and before eval-v3 seed values exist: `artifacts/h1/final-eval-v3-prohibition.json` records `final_eval_v3_seed_values_created=false` and `final_eval_v3_seed_values_inspected=false`, and `config/eval_seeds_v3.json` is absent (Q2). Two read-only diagnostics on 2026-10-23 identified three issues. First, the implementation does not actively re-observe after `PAUSE_AND_REOBSERVE`: `src/rra/evidence/episode.py:626-628` invokes System-2 only on a new escalation rising edge or an infeasible condition not previously attempted; `src/rra/evidence/episode.py:832-834` makes `system2_next_retry` only a lower bound (Q4). The fast layer records the target as `escalated`, a terminal state, in the same step in which System 2 returns `PAUSE_AND_REOBSERVE` (`src/rra/evidence/episode.py:37` and `:835-842`), so System 2 effectively has one decision per target. Second, in replay mode, a cache miss is converted to a proposal error and silently falls back while the run still exits with status 0: `src/rra/llm/adapter.py:106` catches `OSError`, including `ReplayCacheMiss` (Q5). Third, on another machine with the same Python and NumPy versions, 115 of 130 per-seed B3 receipt hashes differed, while metrics and the decisions checked were the same; the cause was last-bit floating-point differences and a tie flip in the fitting grid. This addendum is not triggered by any eval-v3 result. Under P3 Section 18.2, dated 2026-10-24, it registers these protocol clarifications before eval-v3 generation because the diagnostics exposed re-observation, replay-abort, and cross-machine determinism-scope behavior that must be fixed or bounded before scored evaluation.

This addendum does not move or rewrite `p3-prereg`, and does not alter `docs/P3_SYSTEM2_DESIGN.md` or Addenda 01–04. Where this addendum and earlier documents differ, this addendum governs only the items listed below.

## 1. Re-observation hold

1.1 When a target reaches a fast-layer escalation and the System-2 decision for that target in that step is PAUSE_AND_REOBSERVE, the target enters a re-observation hold instead of being recorded as escalated in that step. The existing safe stop applies during the hold: the fast layer issues no commands, and the held target receives no fast-layer command.

1.2 During the hold, the same System-2 path is evaluated again for the target at the first observation at or after 0.5 s of simulation time following the previous evaluation, using all observations accumulated by then. A new escalation event is not required.

1.3 If System 2 authorizes the target, the existing authorization path applies. The safe stop is cleared only when no target remains in a hold and no fault latch is set.

1.4 The hold ends with the target recorded as escalated, with the reason suffix `;REOBSERVE_EXHAUSTED`, at the earliest of: a fault latch; the point after which an authorized command could no longer execute inside the target's pick window; any other terminal outcome becoming due; or the end of the episode.

1.5 Sections 1.1 to 1.4 apply identically to B3, B4-strict, and B4-tiebreak. B1 and B2 are unchanged. A target whose System-2 decision is HUMAN_ESCALATION, or that is latched, is handled as before.

1.6 This implements the existing pause/re-observe semantics of P3 Section 8.3 ("PAUSE_AND_REOBSERVE, then human escalation if additional structured evidence does not resolve it") and the requirement that a structure verified on fewer than six usable observations must be re-observed. It does not change the verifier threshold, the common-action gate, the authorization gate, the DSL, the evaluator, the terminal states, scoring, or any denominator.

## 2. Parameter-grid ties

When the deterministic fitter selects a grid value (speed-step time or actuator delay), objective values within 1e-12 × max(1, |minimum|) of the minimum are ties, and the smallest grid value among them is selected. Grids, thresholds, and the objective are unchanged.

## 3. Replay and generator configuration

3.1 When a scored B4 artifact is generated in replay mode, a replay-cache miss aborts the run with a non-zero exit. It is not a proposal fallback. Addendum 04 Section 3 rule 1 applies to replay-cache misses only outside replay generation; in a live run a cache miss leads to a live call.

3.2 Running B4-strict or B4-tiebreak without a configured hypothesis generator is a configuration error and aborts the run. It is not a fallback.

3.3 `llm_calls` (Addendum 04 Section 1.5) is counted per (seed, text variant) over both B4 variants together, because the variants share one memoized request per identical evidence packet and text context. Proposer invocations by B4-strict and by B4-tiebreak are additionally reported separately.

3.4 Floating-point values in the B4 request are serialized rounded to 6 decimal places, so that the request body and its cache key do not depend on last-digit floating-point differences between machines.

## 4. Determinism scope

4.1 Receipt hashes are bit-reproducible on the registered runner. Each receipt records the runner's Python and NumPy versions, machine architecture, CPU model, and BLAS library outside the hashed content.

4.2 Bit-identical receipt hashes across different machines are not claimed. A cross-machine reproduction is reported at the level of decisions and metrics, with any per-seed receipt difference listed.

4.3 Every registered eval-v3 artifact is generated on one runner, and that runner's recorded platform is reported with the results.

## 5. Added stop conditions (P3 Section 25)

Each of the following is an implementation defect, not a result:

- a target in a re-observation hold that is not re-evaluated as required by Section 1.2;
- a target left without a terminal outcome at the end of an episode;
- a scored B4 artifact generated in replay mode that contains a replay-cache-miss fallback;
- a B4 run that proceeds without a configured hypothesis generator.
