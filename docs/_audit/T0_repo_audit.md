# T0 repo audit (read-only)

Audit of `pzy19-prog/reality-residual-agent`, taken from a fresh clone in a cloud VM on 2026-10-23.
Labels: **FACT** = observed here, with the command and an output summary. **UNKNOWN** = not observable here, with the reason.
No existing file was modified. No secret was used, requested or printed. Nothing that needs a key was called.

Environment: Linux, system Python 3.13.17 (also 3.11 and 3.12 interpreters), Node 22 and `docker` binaries present, `gh` working through the session proxy.
`GH_TOKEN` in the environment was invalid at first. GitHub API access worked only after the session attached the repo (`add_repo`). GraphQL is blocked, so `gh pr list` fails and REST (`gh api`) was used.

## 1. Branches, HEAD, tags

FACT: default branch is `main`, HEAD is `54f5006923b5b08f11a94b5610f26c4342a402cf` ("Merge pull request #21 from pzy19-prog/docs/prereg-addendum-04").
```
$ git symbolic-ref refs/remotes/origin/HEAD   -> refs/remotes/origin/main
$ git rev-parse HEAD (at clone)               -> 54f5006923b5b08f11a94b5610f26c4342a402cf
```

FACT: four tags, all annotated. Commit shas are the peeled ones.
```
$ for t in $(git tag -l); do git rev-parse $t^{commit}; ...; done
v0-baseline       -> 546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee  2026-09-28 "docs: V0 failure modes, baseline declaration and eval protocol"   (tag object 11c4595…)
rra-v0-freeze-01  -> 86ea1bae98508bf17261ff4168769cd74b63bd08  2026-09-28 "docs: record RRA V0 freeze v2"                                    (tag object b5bbaa1…)
p3-prereg         -> 024ea2e3e66b91f5a2157a66c073493e7107e109  2026-09-28 "docs: close final P3 preregistration findings"                    (tag object a7c640b…)
pre-window-freeze -> 3b56637681551f21c6b4c253be6def59389d1051  2026-10-19 "Merge pull request #11 from pzy19-prog/docs/spike-notes-fix-20261019"  (tag object 7dccc25…)
```
FACT: tag messages (`git tag -l --format='%(refname:short): %(contents:subject)'`):
- `v0-baseline`: "V0 pre-hackathon baseline (declared pre-existing components)"
- `rra-v0-freeze-01`: "RRA V0 freeze 01"
- `p3-prereg`: "P3 System-2 design & eval preregistration (pre-hackathon, NOT SCORED); architecture review PASS @ 024ea2e"
- `pre-window-freeze`: "Declared pre-existing work boundary per HACKATHON_BASELINE.md; build window opens 2026-10-22T00:00:00Z"

FACT: the pre-hackathon V0 baseline tag is `v0-baseline` -> `546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee`. `HACKATHON_BASELINE.md` is the declaration file. `rra-v0-freeze-01` is a different tag. That reading comes from the tag name and message, not from a statement in the repo that names `v0-baseline` as "the" V0 tag.

FACT: remote branches other than `main`, ahead and behind `origin/main`:
```
$ git rev-list --count origin/main..<b>  /  <b>..origin/main
origin/feat/l5b-b4                                 ahead=2  behind=3   (tip c852566; open PR #20)
origin/docs/hackathon-prewindow-readiness-20261004 ahead=1  behind=60  (tip c69b735 "docs: declare H1 and prepare hackathon readiness gates"; PR #3 closed unmerged)
origin/docs/fix-stale-window-dates                 ahead=0  behind=51  (tip e8e9b63)
origin/docs/prereg-addendum-04                     ahead=0  behind=1   (tip 3319655; merged via PR #21)
origin/feat/l5a-hygiene                            ahead=0  behind=3   (tip ab509d3; merged via PR #19)
$ git branch -r --merged main -> origin/docs/fix-stale-window-dates, origin/docs/prereg-addendum-04, origin/feat/l5a-hygiene (plus main, HEAD)
```
So **unmerged remote branches**, with their lead over `main`:
- `feat/l5b-b4`: 2 commits ("Add B4 strict and tiebreak dev runner" 92e2b89; "Fix B4 artifact receipts and D4 fallback" c852566).
- `docs/hackathon-prewindow-readiness-20261004`: 1 commit (c69b735).

FACT: `feat/l5b-b4` is based on `feat/l5a-hygiene` (PR #20 base). `git diff --stat main origin/feat/l5b-b4` reports 393 files changed, 14424 insertions(+), 72 deletions(-). The diff is against main's tip, not the branch's merge-base, so the count includes later main changes.
That diff includes: `src/rra/eval/b4_dev.py`, `scripts/l6_b4_meterless_replay.py`, `tests/test_b4_episode.py`, `artifacts/s2/b4-dev.json`, and removal of `docs/P3_PREREG_ADDENDUM_04.md` (an artifact of the comparison, because Addendum 04 landed on `main` later).

## 2. Pull requests (GitHub REST API)

FACT: reachable via `gh api repos/pzy19-prog/reality-residual-agent/pulls?...` (after `add_repo`). Before that, the same call returned HTTP 403 "GitHub access to this repository is not enabled for this session".

Open PRs (`pulls?state=open`): exactly one.
- #20 "L5b: B4-strict/tiebreak + dev run", head `feat/l5b-b4`, base `feat/l5a-hygiene`, not draft, created 2026-10-23T10:18:48Z.

Latest 10 merged PRs (`pulls?state=closed&per_page=100`, filter `merged_at != null`, sort by `merged_at` descending):
| PR | title | head branch | merged (UTC) | merge sha |
|---|---|---|---|---|
| #21 | docs: P3 preregistration addendum 04 (B4 call policy) | docs/prereg-addendum-04 | 2026-10-23T12:56:50Z | 54f5006 |
| #19 | L5a: hygiene + replay key + structure IDs | feat/l5a-hygiene | 2026-10-23T11:39:04Z | 2ff7a6b |
| #18 | L3: Zetaris two-source evidence path + equivalence receipt (A02 §4) | feat/l3-zetaris | 2026-10-23T04:13:29Z | d54faa7 |
| #17 | L6: Meterless S2 run persistence and replay bridge (A02 §5) | feat/l6-meterless | 2026-10-23T04:13:15Z | 90054ca |
| #16 | fix: wire preregistered S2 entry points (correction_infeasible, outcome escalation) | feat/s2-triggers | 2026-10-23T03:07:56Z | 2a3b52d |
| #15 | fix: S2 compliance fixes and failure funnel diagnostics (dev) | feat/s2-fix | 2026-10-22T17:01:41Z | 198ab6a |
| #12 | feat: System-2 deterministic core + B3 (dev) | feat/s2-core | 2026-10-22T16:10:03Z | cbc1f8a |
| #13 | feat: v3 text context families + Nemotron proposer adapter | feat/llm-context | 2026-10-22T15:24:46Z | 345b6f9 |
| #14 | chore: cursor rules and dev workflow record | chore/cursor-rules | 2026-10-22T14:44:08Z | 1ec5761 |
| #11 | docs: correct evidence labels in spike notes | docs/spike-notes-fix-20261019 | 2026-10-19T14:38:27Z | 3b56637 |

FACT: closed without merge: #5 "docs: record P3 schedule change addendum", #3 "docs: declare H1 pre-existing work and prepare hackathon readiness", #2 "test: cloud identity check". 20 closed PRs in total on the first page (limit 100).

FACT: CI status (`gh api repos/.../actions/runs`). Of the latest 100 runs, 84 succeeded and 12 failed.
- The newest failures are on `main` at `54f5006` and on `feat/l5b-b4`. Jobs `test` and `determinism` both fail at step **"Install dependencies"** (run 39957209613 for `main`).
- Same pattern at `ab509d3` (run 39906430278). At `bb8eb49` (2026-10-22), the `test` job failed at "Run tests" instead; `determinism` passed. The reason is UNKNOWN (job logs were not read).
- Cause of the install failure (inferred from files, not from the CI log): see §3, the `numpy==2.5.4` pin.

## 3. Test framework, command, results

FACT: framework is **pytest**. Evidence:
```
$ cat pyproject.toml   -> [tool.pytest.ini_options] testpaths = ["tests"]  pythonpath = ["src"]
$ cat requirements.txt -> numpy==2.5.4 / pydantic>=2.6,<3 / pytest>=8,<9
$ grep tests/ -> bare `assert`, `pytest.mark.skipif`, `monkeypatch`, `capsys` fixtures
$ ls tests/test_*.py | wc -l -> 26 test files, plus tests/_fake_meterless_bridge.py
```
CI (`.github/workflows/ci.yml`): `pip install -r requirements.txt pytest`, then `pytest -q`, on Python **3.11**.

FACT (version conflict in the repo): `numpy==2.5.4` requires Python >= 3.12; `README.md:21` says "需要 Python 3.11"; `rra` (the CLI wrapper) exits unless the interpreter is 3.11; CI uses 3.11; `tests/test_evidence.py:29` asserts `runtime_versions["python"].startswith("3.12.")`.
```
$ python3.11 -m venv v && v/bin/pip install -r requirements.txt
ERROR: Could not find a version that satisfies the requirement numpy==2.5.4 ... 2.5.4 Requires-Python >=3.12
```
- The pin was introduced in `ab509d3` (was `numpy>=1.26,<3`): `git log -S'numpy==2.5.4' -- requirements.txt`.
- CI runs have failed at "Install dependencies" since that commit (see §2).
- So **the repo's documented Python (3.11) cannot install its own requirements**. The test suite and bench only pass on Python 3.12.

FACT: test commands run here (repo root, `-p no:cacheprovider`):
| interpreter | command | result |
|---|---|---|
| 3.13.17, numpy 2.5.4, pydantic 2.13.5, pytest 8.4.2 | `python -m pytest -q -p no:cacheprovider` | **1 failed, 186 passed, 4 skipped** in 258 s (a second run gave the same: 277 s) |
| 3.12.3 (venv), numpy 2.5.4, pydantic 2.14.1, pytest 8.4.2 | `python -m pytest -q -p no:cacheprovider -rs` | **187 passed, 4 skipped, 0 failed** in 281 s |
| 3.11 | not runnable | install fails (above) |

The one failure on 3.13 is `tests/test_evidence.py::test_runtime_versions_are_receipted_but_excluded_from_receipt_hash`, `assert receipt["runtime_versions"]["python"].startswith("3.12.")`. It fails because the interpreter is 3.13.

FACT: the 4 skips (`-rs`):
```
SKIPPED tests/test_meterless_bridge.py:219  needs Node, scripts/setup_meterless.sh and RRA_METERLESS_LIVE=1
SKIPPED tests/test_meterless_bridge.py:240  (same)
SKIPPED tests/test_meterless_bridge.py:249  (same)
SKIPPED tests/test_packet_sources.py:48     Zetaris live checks are opt-in   (needs RRA_ZETARIS_LIVE=1)
```
`git status --short` was empty after the test and bench runs. The working tree stayed clean (`__pycache__` is ignored).

## 4. Bench

FACT: entry points, from `src/rra/cli.py` on `main`:
- `./rra bench [--output-dir D]`: runs the config in `config/scenarios.json` with seeds from `RRA_SEED_FILE`, default `config/eval_seeds_v2.json`. Those are the frozen blind eval v2 seeds (2000–2099; `decisions.md:23`). **I did not run it with the default seeds.**
- `./rra run --scenario {bias,drift,moving,load,combo} --seed N --compensation {on,off}`.
- `./rra s2-b3-dev [--output-dir D]`: B3 dev run, default output `artifacts/s2`. **Not run here**, so its pass/fail status is UNKNOWN. Running it with the default output dir would overwrite tracked files.
- CI determinism job: runs `RRA_SEED_FILE=config/dev_seeds.json python ./rra bench --output-dir A` twice and diffs `bench.json`.

FACT: determinism check reproduced. The `./rra` wrapper refuses non-3.11 interpreters, so I called the same code through the module: `PYTHONPATH=src python3.12 -m rra.cli bench` with dev seeds, output in a scratch dir.
```
$ RRA_SEED_FILE=config/dev_seeds.json venv3.12/bin/python -m rra.cli bench --output-dir $S/b1   # 130 dev seeds (0..129), ~7m14s wall
$ RRA_SEED_FILE=config/dev_seeds.json venv3.12/bin/python -m rra.cli bench --output-dir $S/b2
$ diff -u $S/b1/bench.json $S/b2/bench.json  -> no diff  (printed DETERMINISTIC_IDENTICAL)
sha256(b1/bench.json) = 0f7a5a3b84f91fe9ed57a4d99f1d186ae41e44c5d5c5806bfe72675acc4b721b   ("git_sha": "54f5006923b5b08f11a94b5610f26c4342a402cf")
```
`bench.md` rows (fragment, dev seeds, "off" vs "on" success rate): nominal 1.000/1.000, bias-mid 0.000/1.000, drift-high 0.000/0.987, moving-mid 0.000/0.818, moving-high 0.000/0.008.
This is the deterministic check the CI `determinism` job performs; the CI job itself currently fails earlier, at dependency install.

FACT: dependency on keys or services:
- `rra bench`, `rra run`, `rra s2-b3-dev`: `grep -rn -E "NVIDIA|ZETARIS|urlopen|environ"` over `src/rra/{evidence,sim,eval,s2,fast,controller,planner}` and `cli.py` on `main` matches only `RRA_SEED_FILE` (`cli.py:117`). Offline.
- `scripts/nemotron_smoke.py`, `scripts/nemotron_reasoning_probe.py`: call `NvidiaNimProvider` and need `NVIDIA_API_KEY` and network.
- `scripts/l3_*.py`, `scripts/l3_zetaris_up.sh`: need `ZETARIS_TOKEN`, a Zetaris server at `http://localhost:8888`, and docker (containers `rra-l3-pg`, `rra-l3-ops`).
- `scripts/l6_persist_and_replay.py`, `scripts/setup_meterless.sh`: need Node and the `bridges/meterless` bridge (npm install). Not exercised here.
- Replay paths (`ReplayProvider`, `artifacts/llm_cache/`) are offline.
- On `feat/l5b-b4` only (not on `main`): `rra s2-b4-dev [--subset] [--replay] [--nproc N]` (`git diff main origin/feat/l5b-b4 -- src/rra/cli.py`). `b4_dev.py` builds a read-through provider that tries `ReplayProvider` first and constructs `NvidiaNimProvider` unless `--replay` is set; `--replay` is described as "run offline from artifacts/llm_cache". Not run here.

## 5. Preregistration files

FACT: from `git ls-files` and `git log -1 -- <file>`:
| file | last commit touching it | date |
|---|---|---|
| `docs/P3_SYSTEM2_DESIGN.md` | aa70055 "docs: complete P3 preregistration addendum 03" | 2026-10-12 |
| `docs/P3_PREREG_ADDENDUM_01.md` | 01716bf "H1 repair: expose registered target-not-observed event" | 2026-09-29 |
| `docs/P3_PREREG_ADDENDUM_02.md` | fe3452e "docs: add preregistration addendum 02" | 2026-10-11 |
| `docs/P3_PREREG_ADDENDUM_03.md` | aa70055 "docs: complete P3 preregistration addendum 03" | 2026-10-12 |
| `docs/P3_PREREG_ADDENDUM_04.md` | 3319655 "docs: add P3 preregistration addendum 04" | 2026-10-23 |
| `docs/EVAL_PROTOCOL.md` | dfecbb7 "H1-10 complete regression and pre-window closeout" | 2026-09-29 |
| `docs/H1_EVAL_FOUNDATION.md` | aa70055 | 2026-10-12 |
| `docs/ACCEPTANCE.md` | 86ea1ba "docs: record RRA V0 freeze v2" | 2026-09-28 |
| `docs/HACKATHON_RULES.md` | 3a7d034 "Refresh hackathon rules snapshot and build window" | 2026-10-11 |
| `HACKATHON_BASELINE.md` | 3f0b441 "Align V0 declaration with current rules" | 2026-10-11 |
| `FAILURE_MODES.md` | 546e82a | 2026-09-28 |
| `config/v3_contracts.json` | 01716bf | 2026-09-29 |
| `config/dev_seeds.json` | b025bd4 "RRA-V0-REPAIR-01: expand and audit benchmark" | 2026-09-27 |
| `config/eval_seeds.json` | 6377fa6 "freeze blind eval seeds" | 2026-09-27 |
| `config/eval_seeds_v2.json` | ff1ac91 "freeze blind eval v2 seeds (2000-2099)" | 2026-09-28 |
| `config/scenarios.json` | b025bd4 | 2026-09-27 |
| `artifacts/h1/final-eval-v3-prohibition.json` | 532818c "H1-09 materialize holdout and seed prohibition receipts" | 2026-09-29 |
| `decisions.md` | 5661032 "merge: sync main into feat/s2-core" | 2026-10-23 |

FACT: against the `p3-prereg` tag (024ea2e): `git diff --stat p3-prereg main -- docs/P3_SYSTEM2_DESIGN.md docs/P3_PREREG_ADDENDUM_0[123].md` shows only the three addendum files as new (+279 lines); `P3_SYSTEM2_DESIGN.md` has no diff. The tag's tree contains `docs/P3_SYSTEM2_DESIGN.md` but none of the addenda (`git ls-tree -r p3-prereg`). 81 commits lie between `p3-prereg` and `main`.
FACT: `docs/P3_PREREG_ADDENDUM_04.md` (line 7) says "The eval-v3 seed values do not yet exist" and points to `artifacts/h1/final-eval-v3-prohibition.json`.
UNKNOWN: whether any prereg file was edited in a way that is not visible in these file-level logs (content-level review not done).

## 6. Zetaris / Meterless / NVIDIA-Nemotron references

FACT (`grep -rli 'zetaris\|meterless\|nemotron\|nvidia'`, excluding `.git` and `artifacts/`):
- Code: `src/rra/llm/providers.py` (NVIDIA NIM + replay), `src/rra/sponsor/zetaris.py`, `src/rra/sponsor/meterless.py`.
- Bridge: `bridges/meterless/{bridge.ts,README.md,package.json,package-lock.json}`.
- Scripts: `scripts/nemotron_smoke.py`, `scripts/nemotron_reasoning_probe.py`, `scripts/l3_equivalence.py`, `scripts/l3_export_sources.py`, `scripts/l3_secret_audit.py`, `scripts/l3_source_server.py`, `scripts/l3_zetaris_up.sh`, `scripts/l6_persist_and_replay.py`, `scripts/setup_meterless.sh`.
- Tests: `tests/test_llm_adapter.py`, `tests/test_nemotron_smoke.py`, `tests/test_packet_sources.py`, `tests/test_meterless_bridge.py`, `tests/_fake_meterless_bridge.py`.
- Docs/config: `HACKATHON_BASELINE.md`, `docs/HACKATHON_RULES.md`, `docs/H1_EVAL_FOUNDATION.md`, `docs/P3_SYSTEM2_DESIGN.md`, `docs/P3_PREREG_ADDENDUM_02.md`, `docs/P3_PREREG_ADDENDUM_03.md`, `docs/SPIKE_NOTES_20261019.md`, `decisions.md`, `.cursor/rules/rra.mdc`.
- Artifacts: `artifacts/sponsor/{zetaris-equivalence,zetaris-whitelist,meterless-persistence}.json`, `artifacts/llm_cache/*.json` (2 files).

FACT: behaviour without secrets or local services (run in this VM; `NVIDIA_API_KEY`, `ZETARIS_TOKEN`, `RRA_*_LIVE` all unset):
```
$ python -c "NvidiaNimProvider()"       -> RuntimeError: NVIDIA_API_KEY is required
$ python -c "ZetarisClient().query(..)" -> ZetarisError: ZETARIS_TOKEN is required
$ python -c "meterless.bridge_available()" -> False
```
- NIM provider: constructor raises without a key. Default endpoint `https://integrate.api.nvidia.com/v1`, model `nvidia/nemotron-3.5-super-vl-120b-a12b` (`providers.py:13-14`). **Not runnable without a key.** The replay provider and the unit tests that use fakes or replay (`test_llm_adapter.py`, `test_nemotron_smoke.py`) ran and passed in §3.
- Zetaris client: needs `ZETARIS_TOKEN` and `http://localhost:8888/api/v1.0` (`zetaris.py:16,19`). **Not runnable without both.** Its unit tests pass offline; the live test is skipped (`RRA_ZETARIS_LIVE`).
- Meterless: `bridge_available()` is False here. Unit tests use `tests/_fake_meterless_bridge.py` and pass. The 3 live tests are skipped (need Node, `scripts/setup_meterless.sh`, `RRA_METERLESS_LIVE=1`). Node 22 is installed in this VM, but I did not run `setup_meterless.sh`; whether the npm registry install works from here is UNKNOWN.
- Committed receipts (`artifacts/sponsor/*.json`, `artifacts/llm_cache/*.json`) are inputs that were generated elsewhere. Their provenance was not re-verified here.

## 7. Open items and TODOs in the docs (verbatim, with file:line)

A search for `TODO|FIXME|待办|未完成|尚未|[ ]|not yet|未接入` over `*.md *.py *.sh *.ts *.mdc` (excluding `.git`, `artifacts/`) found the following. It is not a guarantee of completeness for prose that uses other wording.
1. `decisions.md:32`: "B3 尚未接入 runner，详见 REPORT_D1.md 卡点。" `REPORT_D1.md` does not exist in the repo (`ls REPORT_D1.md` -> No such file). PR #12 and #15 later added B3 work, so the line may be stale; not verified.
2. `docs/P3_SYSTEM2_DESIGN.md:45`: "**Evidence status:** these measurements are currently a design input supplied from a sandbox run. They are not yet repository-authoritative evidence. Before they are cited as project evidence or submission evidence, the measurement method and receipt must be reproduced or materialized in-repository without touching the frozen V0 eval results."
3. `docs/DEV_WORKFLOW.md:7-9`: the PR column reads "待定" for `s2-core`, `llm-context` and `cursor-rules`. PRs #12, #13 and #14 correspond by title and are merged.
4. `docs/P3_PREREG_ADDENDUM_02.md:119`: "UNKNOWN: which Meterless component or interface (open specification / reference implementation, or a Gaia / Swarms / Relay application) is integrable from Linux/WSL. This is resolved by the §8 compatibility spike. If only a Windows-hosted component is integrable, persistence runs through a host-side adapter; §5.2–§5.4 still apply unchanged."
5. `docs/P3_PREREG_ADDENDUM_02.md:143-145`: "**Zetaris**: access path (sponsor credits vs. 30-day Z-Cloud trial); whether Z-Cloud can reach the registered sources. …" / "**Meterless**: the integrable interface on Linux/WSL (§5.5)." / "**NVIDIA NIM**: as in P3 §21."
6. `docs/P3_PREREG_ADDENDUM_02.md:149`: "Unless sponsor access is provided, the Zetaris trial is started no earlier than 2026-10-20 so that it covers judging through results (2026-11-06)."
7. `docs/SPIKE_NOTES_20261019.md:13`: "[UNKNOWN] Registering a local Postgres container as a source; the JDBC path (port 10000 is exposed); the §4.3 SHA-256 equivalence against the reference loader; throughput and latency; any hackathon-specific limits."
8. `docs/SPIKE_NOTES_20261019.md:20`: "[UNKNOWN] The per-minute and daily rate limits."
9. `docs/SPIKE_NOTES_20261019.md:33`: "[UNKNOWN] Which Meterless component the organizers mean and what minimum "integration" they expect; to be asked at the 2026-10-21 onboarding call."
10. `docs/P3_PREREG_ADDENDUM_04.md:7`: "…The eval-v3 seed values do not yet exist: `artifacts/h1/final-eval-v3-prohibition.json` records `final_eval_v3_seed_values_created=false` …" (the line continues past what was excerpted here).
11. `docs/P3_PREREG_ADDENDUM_02.md:33`: "Not a quotation: the 2026-09-28 snapshot's "up to 30 bonus points" text is NOT FOUND ON PAGE in the 2026-10-11 snapshot." `docs/HACKATHON_RULES.md` (rule 6.4 row, Rule 6.4 column) also contains "NOT FOUND ON PAGE".

Items 6–9 may have been resolved after those dates; the repo does not record this (`git log` was not mined for it). Treat their current status as UNKNOWN.

## 8. Candidate work that needs no secrets and no local service (list only, no ranking)

Each candidate is something this VM can do offline; none has been started.
- A. Make the Python/numpy pin consistent (`requirements.txt` vs CI 3.11 vs `rra` wrapper vs README vs `tests/test_evidence.py:29`). This touches dependencies and CI, so it is outside this task's scope.
- B. Review of open PR #20 (`feat/l5b-b4`, 2 commits ahead of `feat/l5a-hygiene`), including the new `src/rra/eval/b4_dev.py` and `tests/test_b4_episode.py`, by running its tests on Python 3.12.
- C. Re-run `rra bench` determinism and `rra s2-b3-dev` (with a scratch `--output-dir`) on dev seeds as a baseline against the committed `artifacts/s2/b3-dev.json`.
- D. Reproduce, in-repo, the sandbox measurements flagged at `docs/P3_SYSTEM2_DESIGN.md:45`.
- E. Replay-only checks: verify `artifacts/llm_cache/*.json` keys against `request_sha256`, and on `feat/l5b-b4` run `rra s2-b4-dev --replay` (offline by its help text).
- F. Diagnose the failure funnel using the committed `artifacts/s2/diag-*.json` and `diag/*.md` (hard-case analysis from existing data).
- G. Documentation upkeep: fill the "待定" PR column in `docs/DEV_WORKFLOW.md`; reconcile the missing `REPORT_D1.md` reference in `decisions.md:32`.
- H. Branch hygiene report: list of stale branches (`docs/fix-stale-window-dates` is fully merged; `docs/hackathon-prewindow-readiness-20261004` is unmerged and its PR #3 was closed).
- I. Fetch and read the CI job logs for the failed runs (`gh api .../actions/runs/<id>/jobs` returned job-level data; step logs were not fetched) to confirm the install-failure cause and the 2026-10-22 `Run tests` failure at `bb8eb49`.
- J. Check whether `scripts/setup_meterless.sh` and the fake-bridge path work in this VM (Node 22 is installed; npm registry access untested).

## Method notes

- Clone: `git clone https://github.com/pzy19-prog/reality-residual-agent.git` (full history, not shallow: `git rev-parse --is-shallow-repository` -> false).
- Dependencies were installed with `pip install -r requirements.txt` into the VM's system Python 3.13 (not part of the repo), plus venvs for 3.11 (failed) and 3.12 under the session scratchpad. No repository file was changed by these.
- Git author and committer for this audit commit: `Xifeng Ming <274782819+pzy19-prog@users.noreply.github.com>`.
