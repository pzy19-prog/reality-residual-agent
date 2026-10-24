# HANDOFF — how to continue this project if the current sessions stop

Written 2026-10-24 17:40 Beijing (09:40 UTC) by the cloud coordination session, for any agent (e.g. Codex in the
owner's WSL) that has to take over. **Read this file, then issue #26 from the newest comment backwards, before doing
anything.** This file is a map; the registered documents (`docs/P3_*`) and the owner rulings are the authority.

> 中文摘要：截止 2026-10-28 07:45（北京时间）。冻结前还剩：PR #28（EVAL-PATH-R1）复审并合并、PR #29（A07）合并、
> FRZ-2B（探针选格式 + dev 子集 live），然后打 tag `impl-freeze-v3`、在 i7 上隔离生成 100 个 eval-v3 种子、跑 B1–B3、
> B4 live（上限 2500，10-27 06:00 UTC 截止）、两次 replay、一次性提交结果，最后补赞助方回执和提交材料。
> 任何时候不得查看 eval-v3 种子值、不得修改已登记文件、不得在 i7 以外生成注册产物。

## 0. Deadline and where things live

| Item | Value |
|---|---|
| Build window ends | **2026-10-27 23:45 UTC** (2026-10-28 07:45 Beijing) — `docs/HACKATHON_RULES.md` |
| B4 live fill must complete by | **2026-10-27 06:00 UTC**, runner clock (A06 §3.5, A07 §4.4) |
| Track | 03 Reasoning Architecture |
| Repository | `pzy19-prog/reality-residual-agent` (public — never commit keys or eval-v3 seed values before results) |
| Coordination log | issue #26 "control ↔ cloud coordination" — every ruling and hand-off since 2026-10-24 13:40 |
| Registered runner | owner's machine only: x86_64, Intel i7-10750H, Python 3.12.3, NumPy 2.5.4, scipy-openblas 0.3.34 (A06 §2.1, R4) |
| Secrets | `NVIDIA_API_KEY`, `ZETARIS_TOKEN` exist only in the owner's local environment |

## 1. State at the time of writing

| Piece | State | Head / commit |
|---|---|---|
| `main` | FRZ-1 (#24), A06 (#25), FRZ-2A (#27) merged | `edd54c0` |
| PR #28 EVAL-PATH (`feat/eval-v3-path`) | EVAL-PATH-R1 pushed (`ce8b8a7` merge of `main`, `ae95d8f` guard + ledger, `6ae04b8` error records + stop after 10, `e4de964` live times + incomplete ledger). **Review owned by the local control session** (cloud review stopped). Check it against A07 §4 incl. the 18:20 clarifications (M-1 counter = live outcomes in this process only; M-3 `b4_live.json` / `b4.json` / out-of-repo second replay + `b4_replay_check.json`; M-4 count classes) and the T9b guard bypasses | `e4de964` |
| PR #29 A07 (`docs/prereg-addendum-07`) | A07-R1/R2/R3 done; cloud T12 third re-review: **no must-fix items left**; local review PASS; waits for CI then the owner's merge | `4d3ee79` |
| FRZ-2B (probe + dev live) | not started — needs #28 and #29 merged | — |
| Freeze tag `impl-freeze-v3` | not created | — |
| `config/eval_seeds_v3.json` | **must not exist yet** (`artifacts/h1/final-eval-v3-prohibition.json` flags all `false`) | — |

Check the live state first: `git ls-remote origin main 'refs/pull/*/head'`, then read issue #26 after the newest
`[cloud → local]` / `[local → cloud]` comment that you have not seen.

## 2. Remaining steps, in order

Each step lists its precondition and how to check it. Do not skip ahead; most later steps are irreversible.

1. **EVAL-PATH-R1 on PR #28** (local card; scope in issue #26, 17:45 and 18:00 messages):
   - M0 merge `main` (conflicts in `src/rra/cli.py`, `src/rra/eval/b4_dev.py`);
   - M1 guard: tracked, working-tree and untracked changes after the tag only in the seed file, `artifacts/eval_v3/**`,
     `artifacts/llm_cache/**`; cache: new files only. Also close the guard bypasses listed in the T9b report §2.2;
   - M2 ledger `artifacts/eval_v3/live_ledger.jsonl`: append + fsync before the first attempt, under the same lock as
     the thread pool; cap checked before the append (A07 §4.2);
   - M3 response handling per A07 §4.1 (R14);
   - M4 incomplete-case counts (A07 §4.5, R15); M5 `--deadline-utc`; M6 `--format-mode` + spec fields; M7 no seed in
     any output (test with a 9-digit seed).
   - Check: full pytest; dev equivalence 130/130 vs `s2-b3-dev`; B3 receipt `bfda4d10…` on the registered runner;
     T9b test drafts (report appendix) pass; the A07 §6 stop conditions are testable.
2. **Merge #28, then #29** (owner merges). A07 must be on `main` before the tag.
3. **FRZ-2B** on the registered runner (A06 §3.2, A07 §3); the owner must unlock `NVIDIA_API_KEY` locally. Probe the three format modes on the first 10 distinct
   requests of the 33-seed dev subset, select by the registered rule, write the selected mode into the frozen code,
   rebuild the dev B4 cache live, regenerate `artifacts/s2/b4-dev.json`. If the selected mode's request template
   differs from the probe's recorded template SHA, the probe is void and repeated (A07 §3.3).
   **Run the dev B4 live rebuild on the 33-seed subset (`artifacts/s2/diag-d1g.json`) only.** It contains no case-9
   seed; a full 130-seed dev B4 run would send the structural holdout (dev seeds 9, 28, 47, 66, 85, 104, 123) to the
   generator and falsify A07 §5.1 (T12 M-5).
4. **Pre-freeze checklist**: `docs/_review/T6_prefreeze_check.md` on `cloud/t6-prefreeze-check` §2 (C-01…C-16) on
   the candidate commit; every item measured on the registered runner. Then the owner creates tag `impl-freeze-v3`.
5. **Seed generation** (A06 §1.1–1.3): `scripts/gen_eval_v3_seeds.py` at HEAD == tag with a clean tree, one process
   on the registered runner. It prints only the count and a SHA-256. Commit the seed file **alone**, parent = tag.
   **Nobody opens the file or prints its values** until every row is complete or declared incomplete (A07 §4.6).
6. **Rows** from the tag's commands (A06 §2.2–2.3, A07 §4.3): `rra eval-v3` b1b3, b2, b1-legacy, then b4 live
   (resumable), then b4 replay twice with identical receipts. Exact flags: `rra eval-v3 --help` at the tag.
   401/403 → stop, fix the credential, resume. Ten consecutive error records → stop, wait out the outage, resume.
7. **Commit all results together** (`artifacts/eval_v3/*`, new `artifacts/llm_cache/*` files, the ledger) after every
   row is complete or declared incomplete. No existing cache file may change (A07 §4.7, §6).
8. **Sponsor receipts on the frozen candidate**: Zetaris 20-episode equivalence (local Zetaris + `ZETARIS_TOKEN`),
   Meterless persistence/replay (`scripts/setup_meterless.sh`, `scripts/l6_persist_and_replay.py`).
   Known blocker (local, 2026-10-24 18:10): the Zetaris ops container `rra-l3-ops` exits because its mount source
   (the deleted `l3-zetaris` worktree) is gone; a small OPS fix is needed before the Zetaris receipt.
9. **Submission** (by 10-27 23:45 UTC): fill results into the deck and documents; merge the post-freeze docs branches;
   record the 1–4 min video; fill the form. See §5.

## 3. Hard rules (any one violated invalidates eval rows)

- Never create, open, print, infer or tune on eval-v3 seed values before results; never run the seed script except
  in step 5. Development uses `config/dev_seeds.json` (0–129) only.
- Registered files are never edited; changes go into a new dated addendum (project rule; P3 §18.2).
- No implementation, threshold, prompt, format-mode or seed change after seeing any eval-v3 result (A06 §2.4).
- Generator requests contain no seed and no `episode_id` (R11; A07 §6). `command_id` in the generator view is
  `"{target_id}:{step}"`.
- All registered artifacts are produced on the registered runner only.
- Commit identity: author and committer `Xifeng Ming <274782819+pzy19-prog@users.noreply.github.com>`; no
  co-author or tool attribution lines. Only the owner merges PRs and creates tags.
- When in doubt, stop and ask the owner; record the question and answer in issue #26.

## 4. Owner rulings index (all 2026-10-24)

| Ruling | Subject | Registered in |
|---|---|---|
| R1 | Re-observation hold entry only on the fast-layer `ESCALATE` path | A06 §4.4, §4A |
| R2 | Safe-stop reading of A05 §1.3 kept; object 88/5 disclosed | A06 §4.5; A07 §1.4 |
| R3 | Episode-level safe stop out of scope; disclosed as a failure mode | A06 §4.6 |
| R4 | Registered runner = owner's i7 | A06 §2.1 |
| R5 | A05 §3.4 implemented on the runner; B4 cache rebuilt live there | A06 §4A |
| R6 | B4 request keeps `passing[]`, `current_time`, `horizon` | A06 §4A |
| R7 | Packet scope: current-target observations/presence (all C1 fields), episode feedback before the decision, 5 C1 config fields | A06 §4.7 |
| R8 | 2-D grid ties: lexicographically smallest (tau, delay) | A06 §4.3 |
| R9 (a) | Request-template SHA excludes packet, context text, `s2_summary` | A06 §4A; A07 §1.1 |
| R10 | Context text travels in `evidence_packet.context`; H1:17 cited | A07 §2 |
| R11 | No seed identifiers in generator requests | A07 §2, §6 |
| R12 | Remaining non-C1 keys registered one by one | A07 §2 |
| R13 | `served_models` aggregate, including cache hits | A07 §2 |
| R14 | Response handling conforms to A04 rule 1 (5 attempts, final error record, stop after 10 consecutive) | A07 §4.1 |
| R15 | Incomplete B4: no metrics; A04 §6.1 counts from ledger + cache | A07 §4.5 |
| R16 | Structural holdout seen in dev: disclose, report case 9 separately, no generalization claim | A07 §5 |
| — | Freeze tag `impl-freeze-v3`; 100 seeds; B4 cap 2,500; NIM budget approved | A06 §1, §3.3; A07 §1.2 |

## 5. Where the reviews and drafts are

All on `cloud/*` branches (read with `git show origin/<branch>:<path>`); none is merged.

| Branch | File | Use |
|---|---|---|
| `cloud/t1-pr20-review` | `docs/_review/T1_pr20_review.md` | PR #20 review (B4 dev, history) |
| `cloud/t3-failure-funnel` | `docs/_diag/T3_failure_funnel.md` | B3 dev failure funnel |
| `cloud/t4-frz1-review` | `docs/_review/T4_frz1_review.md` | A05 clause audit; why 84/775; B4 cache impact |
| `cloud/t6-prefreeze-check` | `docs/_review/T6_prefreeze_check.md` | **pre-freeze checklist C-01…C-16**, packet audits, phases 1–3 on FRZ-2A |
| `cloud/t8-repro-check` | `docs/_review/T8_repro_check.md` | judge-view reproduction, README gaps |
| `cloud/t9a-a06-review` | `docs/_review/T9a_a06_review.md` | A06 review (M/S items) |
| `cloud/t9b-evalpath-review` | `docs/_review/T9b_evalpath_review.md` | **EVAL-PATH review: X1/X2, guard bypasses (§2.2), test drafts.** Written on `52bdd47` (local commit `2d6b2ce`); pushed only if the owner approved it in the T9b session — check `git ls-remote` |
| `cloud/t12-a07-review` | `docs/_review/T12_a07_review.md` | A07 review and re-reviews |
| `cloud/t10-readme-docker` | README ×2, Dockerfile, `scripts/l6_b4_meterless_replay.py` | **post-freeze** docs/build changes (3 separable commits; the script commit only after results) |
| `cloud/t11-submission-v4` | `docs/submission/DRAFT_SUBMISSION_v4.md`, `FAILURE_MODES_DRAFT_v2.md`, `DECLARATIONS_TEMPLATE.md` | submission drafts; add R10–R16 and S-8 before use |
| `cloud/t5-submission-refresh` | `docs/submission/DECK_OUTLINE.md`, `VIDEO_SCRIPT.md` | deck outline, 3-minute video script |

The slide deck (13 slides, English) is a private claude.ai artifact owned by the owner; only the results slide is
empty. Fill it from `artifacts/eval_v3/*` after step 7, reporting case 9 separately (R16) and any incomplete B4 per R15.

## 6. Things that are not in GitHub

- Local control-session cards and reviews: a snapshot is on branch `local/control-docs` @ `6803118` (56 files,
  pushed 2026-10-24 18:01). Later changes live in the owner's WSL worktree until pushed again.
- Uncommitted local work: run `git status` / `git stash list` in the owner's worktree before starting.
- From 2026-10-24 ~18:00 Beijing the cloud coordination session is **on standby to save quota**: its watcher and
  hourly check are off. The local control session is primary. The owner can call the cloud session for a specific
  review or for the deck/submission documents. Cloud reports stay on the branches above.
