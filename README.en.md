# Reality Residual Agent (RRA) V0

A deterministic 2D conveyor pick-and-place simulation and residual-compensation baseline. V0 makes no LLM, network, NIM, or Jev calls. Object positions come only from an explicit seed.

## Problem and goal

A fixed nominal model can miss picks under sensor bias, a linearly changing offset, a moving target, or a speed step. RRA records observed minus nominal position, classifies a sliding residual window, and compares bounded EWMA timing compensation with an uncompensated run on the same seeds. A residual above the fixed safety threshold stops further picks and emits `ESCALATE`.

## Architecture

```text
seeded 2D World → nominal ScriptedPlanner → ResidualMonitor → bounded Corrector
        ↑                    ↓                    ↓                 ↓
 perturbations          pick plan           residual receipt    Controller
                                                                     ↓
                                                     episode metrics + JSON receipt
```

The 2D state has conveyor-axis x and lateral y. The gripper remains fixed at `(x_pick, y_pick)`. V0 compensates pick timing; gripper position remains fixed. Speed, position, and pick-window limits are enforced by configuration and the Controller.

## Install and run

Python 3.11 is required.

```bash
python -m venv .venv
. .venv/bin/activate
pip install . pytest
rra run --scenario bias --seed 7 --compensation on
rra run --scenario bias --seed 7 --compensation off
rra bench
```

`rra run` writes a JSON receipt under `outputs/` and prints its path. `rra bench` uses eval seeds `100–129`, runs on/off for all five scenarios, and writes `bench.json` and `bench.md` in the current directory. Tune seeds are fixed at `0–9`, disjoint from eval seeds. Baseline parameters are declared scenario values; the program does not tune itself from eval results.

Docker:

```bash
docker build -t reality-residual-agent .
docker run --rm reality-residual-agent rra bench
```

The benchmark files are written inside the container at `/app/bench.json` and `/app/bench.md`. To retain them on the host:

```bash
docker run --rm -v "$PWD:/results" reality-residual-agent rra bench --output-dir /results
```

## Eval benchmark

Fixed eval seeds `100–129` (30 seeds per configuration). Success rate uses all generated objects as the denominator; objects not attempted after escalation count as failures. MAE is mean 2D position error over attempted picks. Values are from the offline smoke benchmark in `bench.json`. Formal `pytest` and Docker build were not verified because Python 3.11 Pydantic/pytest packages were unavailable in the execution environment.

| Scenario | Compensation off | Compensation on | Delta | Off MAE | On MAE | On escalations |
|---|---:|---:|---:|---:|---:|---:|
| bias | 0.000 | 1.000 | +1.000 | 0.453 | 0.051 | 0 |
| drift | 0.134 | 1.000 | +0.866 | 0.271 | 0.052 | 0 |
| moving | 0.000 | 0.847 | +0.847 | 0.596 | 0.105 | 0 |
| load | 0.000 | 0.714 | +0.714 | 0.633 | 0.140 | 0 |
| combo | 0.000 | 0.222 | +0.222 | 0.011 | 0.071 | 30 |

In combo, some picks happen before the combined residual crosses the fixed threshold. Once it escalates, the episode stops attempting picks. See [FAILURE_MODES.md](FAILURE_MODES.md).
