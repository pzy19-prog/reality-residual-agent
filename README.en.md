# Reality Residual Agent (RRA)

A deterministic 2D conveyor pick simulation with two layers on top of it:

| Layer | Contents | Calls an LLM / network |
|---|---|---|
| **V0 baseline** | Rule-based fast layer: residual monitoring, bounded compensation, controller, escalation (`ESCALATE`). Explicit seeds determine object placement; [`config/scenarios.json`](config/scenarios.json) defines the benchmark suite. V0 itself makes no LLM, network, NIM, or Jev calls. | No |
| **System-2 layer** | Recovery decisions after a fast-layer escalation: candidate hypotheses, a verifier, controller authorization (B1-corrected / B3 / B4 variants). B4 hypotheses come from an LLM (NVIDIA NIM); `artifacts/llm_cache` supports offline replay. | Only B4 without `--replay` |
| **Sponsor integrations** | Meterless (decision-trail persistence and replay), Zetaris (data-source path, opt-in), NVIDIA NIM (B4 hypothesis generation). See [Sponsor technologies](#sponsor-technologies). | Depends on the path |

Status:

- Eval v2 is frozen and was run once (results at the end). **Eval v3 seeds have not been generated, and there are no eval v3 results.** Protocol: [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md) and [docs/P3_PREREG_ADDENDUM_06.md](docs/P3_PREREG_ADDENDUM_06.md).
- Numbers labelled **dev** come from dev seeds `0–129` and name their source file; dev numbers are for iteration, not evaluation results.
- Passages marked `[pending FRZ-2A merge — to be checked]` or `[pending EVAL-PATH merge — to be checked]` are placeholders for code that is not merged yet; no parameters or outputs are given for them.

## Problem and architecture (V0 baseline)

A fixed nominal model produces pick errors under sensor offset, time-varying offset, moving targets, or speed steps. RRA records observed − nominal-predicted residuals, classifies them over a sliding window, splits them into sensor offset and motion lead, applies bounded timing compensation with a feasibility check, and compares against a no-compensation baseline on the same seeds; objects whose correction is infeasible are skipped explicitly (`correction_infeasible`). A residual above a fixed threshold stops picking and raises `ESCALATE`.

```text
seeded 2D World → nominal ScriptedPlanner → ResidualMonitor → bounded Corrector
        ↑                    ↓                    ↓                 ↓
 perturbations          pick plan           residual receipt    Controller
                                                                     ↓
                                                     episode metrics + JSON receipt
```

The 2D state has x along the conveyor and lateral y; the gripper is fixed at `(x_pick, y_pick)`. V0 compensation acts on pick time; the gripper position stays fixed. Speeds, positions and pick windows are bounded by configuration and the controller.

## System-2 layer

After a fast-layer escalation (for example in combo), V0 can only stop (see [FAILURE_MODES.md](FAILURE_MODES.md)). The System-2 layer enumerates or proposes candidate hypotheses at the escalation point, a verifier checks them, and the controller authorizes before any command changes. Design: [docs/P3_SYSTEM2_DESIGN.md](docs/P3_SYSTEM2_DESIGN.md); preregistration addenda: `docs/P3_PREREG_ADDENDUM_*.md`.

| Variant | Entry point | Notes |
|---|---|---|
| B1-corrected | comparison arm inside `rra s2-b3-dev` | Fast layer only, with corrected terminal monitoring |
| B3 | `rra s2-b3-dev` | Enumerates all 14 DSL structures at every fast-layer escalation; `LLM calls: 0` |
| B4 | `rra s2-b4-dev` | Hypotheses come from an LLM; `--replay` reads only `artifacts/llm_cache`; `--subset` uses the registered 33-seed dev subset (`artifacts/s2/diag-d1g.json`) |

FRZ-2A changes (evidence-packet completion, §3.4 rounding, prompt v2, receipt fields): `[pending FRZ-2A merge — to be checked]`.

Committed **dev** results (`artifacts/s2/b3-dev.md`, 130 dev seeds): recoverable challenge success 0.1084 (84/775), wrong disposition 588, miss 97, unsafe action 7 (all fast layer command), preservation regression 0/582. B4 dev results: `artifacts/s2/b4-dev.json`. These are dev numbers, not eval results.

## Dependencies

| Dependency | Used for | Needed when |
|---|---|---|
| Python 3.12 | All Python code; `rra` exits with `RRA requires Python 3.12` on other versions | Always |
| `requirements.txt`: `numpy==2.5.4`, `pydantic>=2.6,<3`, `pytest>=8,<9` | Simulation, data models, tests | Always |
| git, Node 22, npm | Meterless bridge (TypeScript, `bridges/meterless`); Meterless is pinned to commit `1742dec56a66e58eef9dda2d2b865823758ca8cd` | Meterless path only |
| Docker | Container run; `scripts/l3_zetaris_up.sh` | Docker / Zetaris paths only |
| `NVIDIA_API_KEY` | NVIDIA NIM (endpoint `https://integrate.api.nvidia.com/v1`, see `src/rra/llm/providers.py`) | Live LLM calls only |
| `ZETARIS_TOKEN` and a running Zetaris stack (default `http://localhost:8888/api/v1.0`) | Zetaris path | Zetaris path only (opt-in) |

Python 3.12 can come from your system package manager, `pyenv` or `uv`. If `python3` points at another version, create the virtual environment with `python3.12` explicitly and run `rra` with the virtual environment's Python (the `rra` shebang is `#!/usr/bin/env python3`).

## Install and run (V0)

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on
.venv/bin/python ./rra run --scenario bias --seed 7 --compensation off
```

`rra run` writes a JSON receipt under `outputs/` and prints its path.

`rra bench` runs nominal, low/mid/high levels of the four disturbances, and combo, each with compensation on and off, and writes `bench.json` and `bench.md` to `--output-dir` (default: the current directory).

> **Notes**
> - Running `rra bench` at the repository root overwrites the committed `bench.md` and `bench.json` (the frozen eval v2 results). Run it in a temporary directory or pass `--output-dir <dir>`.
> - Without `RRA_SEED_FILE`, `rra bench` reads the frozen eval v2 seeds `2000–2099`; that set has been used once, do not use it for iteration.
> - Iterate on dev seeds `0–129` only, and give `RRA_SEED_FILE` as an absolute path.

```bash
# Dev-seed bench into a temporary directory (about 6 minutes on a 4-core cloud VM in T8)
RRA_SEED_FILE="$PWD/config/dev_seeds.json" .venv/bin/python ./rra bench --output-dir /tmp/rra-dev
```

Evaluation protocol: [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md).

## Reproduce without keys

None of these commands needs `NVIDIA_API_KEY` or `ZETARIS_TOKEN`. They were run on a cloud VM (4 cores, Python 3.12, Node 22); timings are orders of magnitude only, and some ran concurrently with other commands. Details: [docs/_review/T8_repro_check.md](docs/_review/T8_repro_check.md) and [docs/_review/T10_changes.md](docs/_review/T10_changes.md).

| Command (repo root, `.venv` created) | What it does | Measured |
|---|---|---|
| `.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on` | One V0 run | exit 0, about 0.4 s |
| `RRA_SEED_FILE="$PWD/config/dev_seeds.json" .venv/bin/python ./rra bench --output-dir /tmp/rra-dev` | V0 dev bench | exit 0, about 6 min |
| `.venv/bin/python -m pytest -q` | Full test suite | exit 0, `200 passed, 4 skipped in 257.31s` (4 skips: 3 Meterless live, 1 Zetaris live) |
| `.venv/bin/python ./rra s2-b3-dev --output-dir /tmp/rra-s2` | Paired B1-corrected vs B3 on dev seeds | exit 0, 104 s and 122 s in the container (two runs) |
| `.venv/bin/python ./rra s2-b4-dev --replay --subset --output-dir /tmp/rra-s2` | B4 offline replay on the 33-seed dev subset | on `520b7cf` (T8): exit 0, about 11 min; on `349d1e6` (in the container): exit 1 after about 100 s with `ReplayCacheMiss` (see below) |
| `bash scripts/setup_meterless.sh` | Install the pinned local Meterless bridge | exit 0, about 4 s (needs GitHub and npm access) |
| `RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest -q tests/test_meterless_bridge.py` | Meterless bridge tests (Meterless installed first) | `25 passed` |
| `scripts/l6_persist_and_replay.py persist\|verify\|trail\|replay …` | Meterless persistence and replay, see [Sponsor technologies](#sponsor-technologies) | exit 0, a few seconds each |

On `349d1e6`, `--replay --subset` exits with `ReplayCacheMiss: artifacts/llm_cache/566dfc84….json`: none of the 386 cache files in the repository matches that request. `src/` differs between `520b7cf` and `349d1e6`; the cause of the missing entry was not investigated.

A full `rra s2-b4-dev --replay` (no `--subset`) was terminated by an external time limit after 28 minutes in T8; it produced no output and did not finish.

## System-2 / B3 / B4 usage (dev seeds)

```bash
# B3 (no LLM calls): writes b3-dev.json / b3-dev.md
.venv/bin/python ./rra s2-b3-dev --output-dir /tmp/rra-s2

# B4 offline subset replay: reads only artifacts/llm_cache, writes b4-dev.json
.venv/bin/python ./rra s2-b4-dev --replay --subset --output-dir /tmp/rra-s2
```

- **Point `--output-dir` at a temporary directory.** The default is `artifacts/s2`, which overwrites the committed `b3-dev.*` and `b4-dev.json`.
- `--replay` reads only `artifacts/llm_cache` and needs no key; without `--replay`, B4 constructs `NvidiaNimProvider`, which raises `RuntimeError` when `NVIDIA_API_KEY` is missing.
- `--nproc N` sets the number of B4 worker processes.
- Both commands use dev seeds only and do not read eval seeds.

The `rra eval-v3` subcommand and its seed-generation script: `[pending EVAL-PATH merge — to be checked]`.

## Sponsor technologies

### Meterless (local bridge, no key)

System-2 decision records are written to a Meterless store through `src/rra/sponsor/meterless.py` and `bridges/meterless` (Node 22 + TypeScript), then read back in a fresh process, replayed, and compared by hash. Needs git, Node 22 and npm:

```bash
bash scripts/setup_meterless.sh                 # pinned commit 1742dec…; vendor/ and node_modules/ are gitignored
RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest -q tests/test_meterless_bridge.py

OUT=/tmp/rra-l6
.venv/bin/python scripts/l6_persist_and_replay.py persist --run-tag demo --out-root $OUT --seeds 0 1 2
.venv/bin/python scripts/l6_persist_and_replay.py verify  --run-tag demo --out-root $OUT --seeds 0 1 2
.venv/bin/python scripts/l6_persist_and_replay.py trail   --run-tag demo --out-root $OUT --episode ep-001
.venv/bin/python scripts/l6_persist_and_replay.py replay  --run-tag demo --out-root $OUT --episode ep-001
```

`verify` without `--artifact` writes no repository file; the `run` subcommand and `verify --artifact` rewrite the committed `artifacts/sponsor/meterless-persistence.json`. `scripts/l6_b4_meterless_replay.py` replays 20 episodes from the B4 cache and writes an updated JSON; choose the destination with `--output <path>` (default `outputs/l6/meterless-persistence.json`; rewriting the committed file requires `--output artifacts/sponsor/meterless-persistence.json`). The script exits 0 on `520b7cf` (about 74 s); on `349d1e6` it exits 1 part-way with `ReplayCacheMiss`, and the pre-change script behaves the same on that commit; the cause was not investigated.

### Zetaris (opt-in, external service)

The Zetaris path needs `ZETARIS_TOKEN` (`ZetarisClient` raises `ZETARIS_TOKEN is required` without it), a Zetaris stack at `http://localhost:8888/api/v1.0`, and, for `scripts/l3_zetaris_up.sh`: local Docker, a Docker network named `zetaris_default`, the `postgres:16-alpine` and `python:3.12-alpine` images, and `outputs/l3/sources` (generated by `scripts/l3_export_sources.py`). The live part of `tests/test_packet_sources.py` is skipped by default. These commands are outside the keyless reproduction above and were not run outside those prerequisites. Committed records: `artifacts/sponsor/zetaris-*.json`.

### NVIDIA NIM (needs `NVIDIA_API_KEY`)

B4 hypothesis generation uses NVIDIA NIM (`src/rra/llm/providers.py`, endpoint `https://integrate.api.nvidia.com/v1`; requests are cached by content hash in `artifacts/llm_cache`). `scripts/nemotron_smoke.py` makes one live call with retries and needs the key. With the cache present, `--replay` is fully offline.

### Cursor

[所有者填写：Cursor 使用方式（Rule 6.4）]

## Docker

The image contains `src/`, `config/`, `tests/`, `scripts/`, `bridges/` (without the Meterless vendor tree and `node_modules`), `pyproject.toml`, `rra`, and the files B4 replay needs: `artifacts/llm_cache` and `artifacts/s2/diag-d1g.json`. The default `CMD` is `rra bench` on dev seeds, writing to `/tmp/rra-out` inside the container.

```bash
docker build -t reality-residual-agent .

# Default command: dev-seed bench (RRA_SEED_FILE=/app/config/dev_seeds.json is set in the image)
docker run --rm reality-residual-agent

# Keep the output on the host
docker run --rm -v "$PWD/out:/results" reality-residual-agent rra bench --output-dir /results

docker run --rm reality-residual-agent rra run --scenario bias --seed 7 --compensation on
docker run --rm reality-residual-agent python -m pytest -q
docker run --rm reality-residual-agent rra s2-b3-dev --output-dir /tmp/o
docker run --rm reality-residual-agent rra s2-b4-dev --replay --subset --output-dir /tmp/o
```

`python -m pytest -q` inside the image was measured at `195 passed, 5 skipped, 4 failed`: all 4 failures are `FileNotFoundError: 'git'` because the image has no `git` executable (those tests call `git rev-parse` / `git ls-files`); the same tests in a checkout with git are covered above.

Run outside the image: Meterless (needs Node and `scripts/setup_meterless.sh`), `scripts/l6_*`, the Zetaris path, and the full `artifacts/` tree (about 155 MB, mostly diagnostic JSON). The image has no `.git`, so the receipt `git_sha` is `unknown`. To label the result's `seed_role`, `rra bench` reads `config/eval_seeds_v2.json` and compares it with the seed set in use, so that file is still in the image; the seed set the default command uses is the dev seeds.

Measured image size, command timings and exit codes: [docs/_review/T10_changes.md](docs/_review/T10_changes.md).

## Eval v3 status

- Seeds are **not generated**; there are no results. `config/eval_seeds_v3.json` does not exist; `artifacts/h1/final-eval-v3-prohibition.json` records the generation and inspection status.
- Protocol, run order and the B4 call cap: [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md) and [docs/P3_PREREG_ADDENDUM_06.md](docs/P3_PREREG_ADDENDUM_06.md).
- Generation and run commands: `[pending EVAL-PATH merge — to be checked]`.

## Known limitations

- V0 fast-layer failure modes (correction envelope, hard escalation, boundary admissions, model limits) are in [FAILURE_MODES.md](FAILURE_MODES.md). The simulator is idealized (no sensor noise, actuator dynamics, occlusion or collisions); results say nothing about hardware.
- System-2 dev metrics are given above and in `artifacts/s2/b3-dev.md` and `artifacts/s2/b4-dev.json`.
- The Docker image does not include the Meterless or Zetaris paths (see [Docker](#docker)).
- The Meterless, Zetaris and NVIDIA paths have external dependencies (see [Dependencies](#dependencies)); only the local Meterless bridge and `--replay` need no key.
- On `349d1e6`, `rra s2-b4-dev --replay --subset` and `scripts/l6_b4_meterless_replay.py` exit with `ReplayCacheMiss` (see above); B4 offline replay was not reproducible on that commit.
- A full single-process `rra s2-b4-dev --replay` ran over 28 minutes without finishing in T8; a dev `rra bench` takes about 6 minutes.

## Metric definitions

- **Success rate** = successful picks / all generated objects (12 per seed and configuration). A pick succeeds only when the controller accepts the command and the pick window is met. Objects not attempted after escalation remain in the denominator as failures. Rejected attempts are not successes.
- **MAE** = sum of pick-window errors over all attempted picks / number of attempts. Each error is `max(2D Euclidean position error, |actual time − command time| × command speed)`, in world-distance units. Successful and failed attempts both count. Objects never attempted after escalation add no error sample. MAE is 0 only when there are no attempts in the whole group.
- **Escalations** = escalations first triggered in an episode plus escalations caused by controller rejections; a residual exceeding the limit counts once per episode.

The former `0.011` combo MAE with 0 success came from the old aggregation: most episodes escalated without any pick, their episode MAE was recorded as 0 and entered the episode mean, while the few attempted picks all failed, so success (over all generated objects) stayed 0. That MAE aggregation was a bug; the benchmark now weights MAE by the number of actual attempts, and unattempted objects affect only the success-rate denominator.

### Frozen eval v2 results

These results use the 100 frozen eval seeds `2000–2099` at code version `c66b4bf`; each configuration × seed runs 12 objects, with compensation on and off on identical seeds. Full coverage, precision and terminal-state counts: [`bench.md`](bench.md) and [`bench.json`](bench.json). They are results for the V0 baseline and do not include the System-2 layer.

| Scenario | Parameter | off success | on success | Δ | off MAE | on MAE | off escalations | on escalations |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| nominal | — | 1.000 | 1.000 | +0.000 | 0.050 | 0.050 | 0 | 0 |
| bias-low | `position_bias=0.08` | 1.000 | 1.000 | +0.000 | 0.093 | 0.050 | 0 | 0 |
| bias-mid | `position_bias=0.25` | 0.000 | 1.000 | +1.000 | 0.255 | 0.050 | 100 | 0 |
| bias-high | `position_bias=0.45` | 0.000 | 1.000 | +1.000 | 0.453 | 0.050 | 100 | 0 |
| drift-low | `drift_per_second=0.008` | 1.000 | 1.000 | +0.000 | 0.070 | 0.050 | 0 | 0 |
| drift-mid | `drift_per_second=0.045` | 0.049 | 1.000 | +0.951 | 0.273 | 0.051 | 100 | 0 |
| drift-high | `drift_per_second=0.09` | 0.000 | 0.981 | +0.981 | 0.534 | 0.076 | 100 | 0 |
| moving-low | `moving_speed_delta=0.02` | 0.977 | 1.000 | +0.023 | 0.129 | 0.051 | 0 | 0 |
| moving-mid | `moving_speed_delta=0.10` | 0.000 | 0.849 | +0.849 | 0.593 | 0.087 | 100 | 1 |
| moving-high | `moving_speed_delta=0.18` | 0.000 | 0.010 | +0.010 | 0.968 | 0.154 | 100 | 100 |
| load-low | `load_speed_delta=0.04` | 0.664 | 1.000 | +0.336 | 0.166 | 0.051 | 18 | 0 |
| load-mid | `load_speed_delta=0.16` | 0.000 | 0.656 | +0.656 | 0.627 | 0.081 | 100 | 18 |
| load-high | `load_speed_delta=0.28` | 0.000 | 0.023 | +0.023 | 0.877 | 0.094 | 100 | 100 |
| combo | existing defaults | 0.000 | 0.008 | +0.008 | 0.315 | 0.154 | 100 | 100 |

Result files: [`bench.json`](bench.json), [`bench.md`](bench.md). All combo escalations in the rule-based fast layer are the core V0 failure mode; the System-2 layer targets recovery decisions in that state, see [FAILURE_MODES.md](FAILURE_MODES.md).
