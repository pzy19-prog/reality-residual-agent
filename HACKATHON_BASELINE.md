# Open Agent Hackathon 2026 — declared pre-existing components

## Judging boundary

Tag `v0-baseline` remains the immutable original V0 snapshot, at commit `546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee`. The V0 component description below is tied to that snapshot. Additional work was committed after `v0-baseline` and before the hackathon build window (2026-10-15T00:00:00Z), as listed in [Pre-window work committed after `v0-baseline`](#pre-window-work-committed-after-v0-baseline). That later work does not change what was present in the original V0 snapshot.

At the time this text is committed, the tag `pre-window-freeze` does not exist. After this declaration is merged to `main`, and before 2026-10-15T00:00:00Z, the `main` commit containing the merged declaration will be tagged `pre-window-freeze`. This file cannot record that tag's commit hash; `git rev-parse "pre-window-freeze^{commit}"` resolves it once the tag exists. Everything reachable from `pre-window-freeze` is declared pre-existing work and will not be presented as hackathon-window work. The work this project presents as built during the window is the range `pre-window-freeze..<submission commit>`. Commits after `v0-baseline` are therefore not all hackathon-window work. This file is the repository-side record of the declaration; it does not by itself establish eligibility or how the organizers will judge the submission.

## Declared components

- Seeded 2D conveyor world with nominal, bias, drift, moving-target, load-step and combo scenarios (`config/scenarios.json`), with a horizon validator.
- Nominal scripted pick planner.
- Residual monitor with heuristic disturbance classifier.
- Corrector: sensor-offset / motion-lead separation, bounded time correction (±0.5 s), feasibility check (`correction_infeasible`), fixed fail-closed residual threshold.
- Deterministic controller with speed, position and pick-window limits.
- Episode runner with one terminal state per object and outcome escalation (3 consecutive failures).
- JSON receipts, same-seed on/off benchmark, dev/eval harness and blind-eval protocol (`docs/EVAL_PROTOCOL.md`).
- CLI, Dockerfile, tests, documentation, and the rules snapshot `docs/HACKATHON_RULES.md`.

V0 contains **no LLM integration** and no sponsor (NVIDIA / Zetaris) technology.

## Pre-window infrastructure committed after `v0-baseline`

These separately identifiable commits land after `v0-baseline` but before the build window opens. They change repository CI and tool settings, are tooling/configuration only, change no agent behaviour or results, and are **not** submitted for judging:

The three commits are `90821fc55d7581a156c68ec3cadc135738ff4ab6`, `a1287c3386044c4723a68378e870090eca87f032` (which also edited this file), and merge `38f8ce139bf90de659a192f4456821dcff0db4a8`.

- CI workflow `.github/workflows/ci.yml`: pytest plus a dev-seed bench determinism check.
- Repository tool settings `.claude/settings.json`.

## Pre-window work committed after `v0-baseline`

The 25 commits in `546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee..b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0` fall into three groups: 3 CI/settings commits (previous section), 4 P3 preregistration commits, and 18 H1 commits. All 25 have committer timestamps before the 2026-10-15T00:00:00Z build-window boundary. Their inclusion here records pre-window work; it does not redefine the contents of `v0-baseline`.

### P3 preregistration

Four commits, `879dab82ab24344e0ece9a868f0a5466388203b9` through `024ea2e3e66b91f5a2157a66c073493e7107e109`, update `docs/P3_SYSTEM2_DESIGN.md`. The document records a System-2 design and evaluation preregistration, including intended architecture, benchmark families, metrics, and failure criteria. The changed paths in these four commits are documentation only; no `src/rra/` runtime or agent implementation paths change. These commits predate the build window and are pre-existing work, not hackathon-window work.

### H1 evaluation foundation

Eighteen commits, `095ea10b3ad3b1a2d7b81c841c7cd7bacfed3f79` through `b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0`, add and repair the H1 evaluation foundation before the build window. The changed paths cover `src/rra/` evaluation, evidence, and simulation code; tests; `artifacts/h1/`; `config/v3_contracts.json`; and `docs/EVAL_PROTOCOL.md`, `docs/H1_EVAL_FOUNDATION.md`, and `docs/P3_PREREG_ADDENDUM_01.md`.

The changed paths under `src/rra/` are:

- `src/rra/eval/__init__.py`
- `src/rra/eval/b2_grid.py`
- `src/rra/eval/dev_diagnostics.py`
- `src/rra/eval/framework.py`
- `src/rra/eval/holdout.py`
- `src/rra/eval/legacy_anchor.py`
- `src/rra/eval/omniscient.py`
- `src/rra/eval/pause.py`
- `src/rra/eval/runner.py`
- `src/rra/eval/scenarios.py`
- `src/rra/eval/scoring.py`
- `src/rra/eval/text_context.py`
- `src/rra/evidence/episode.py` (modified; present at `v0-baseline`)
- `src/rra/evidence/policy.py`
- `src/rra/sim/v3_world.py`
- `src/rra/sim/world.py` (modified; present at `v0-baseline`)

The H1 artifact directory contains `b1-corrected-dev.json`, `b1-framework-delta.json`, `b1-legacy-dev.json`, `b2-grid.json`, `dev-episode-determinism.json`, `final-eval-v3-prohibition.json`, `legacy-equivalence.json`, `omniscient-upper-bound.json`, and `structural-holdout.json`.

H1 changes runtime/source implementation under `src/rra/`; it is not accurately described as tooling only. At the top level, `bench.json` and `bench.md` have the same Git blob contents at the peeled `v0-baseline` commit and at the end of H1 (`b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0`). This file comparison does not establish whether runtime behavior changed. H1 predates the build window and is pre-existing work, not hackathon-window work.

## Baseline result at `v0-baseline` (blind eval v2, 100 seeds, compensation on)

| Scenario | Success | Coverage | Precision | Escalations |
|---|---:|---:|---:|---:|
| nominal | 1.000 | 1.000 | 1.000 | 0 |
| moving-mid | 0.849 | 0.882 | 0.963 | 1 |
| load-mid | 0.656 | 0.679 | 0.966 | 18 |
| combo | 0.007 | 0.008 | 0.900 | 100 |

Full table: `bench.md`; raw artifact: `bench.json` (commit `2418406`, implementation `c66b4bf`).
