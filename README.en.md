# Reality Residual Agent (RRA) V0

A deterministic 2D conveyor pick simulation and residual-compensation baseline. V0 makes no LLM, network, NIM, or Jev calls. Explicit seeds determine object placement; [`config/scenarios.json`](config/scenarios.json) defines the benchmark suite.

## Install and run

Requires Python 3.11.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python ./rra run --scenario bias --seed 7 --compensation on
.venv/bin/python ./rra bench
```

You can also activate the virtual environment first, then run `./rra ...` or `rra ...`. Use the virtual environment's Python so the `rra` script's `#!/usr/bin/env python3` shebang does not select the system Python.

`rra bench` defaults to the frozen eval seeds `2000–2099` and runs nominal, low/mid/high levels of bias, drift, moving-target, and load disturbances, plus combo. Development uses seeds `0–129`. A development smoke run can select them with `RRA_SEED_FILE=config/dev_seeds.json .venv/bin/python ./rra bench`.

Evaluation protocol: [docs/EVAL_PROTOCOL.md](docs/EVAL_PROTOCOL.md).

Docker smoke:

```bash
docker build -t reality-residual-agent .
docker run --rm -e RRA_SEED_FILE=/app/config/dev_seeds.json reality-residual-agent rra bench
```

## Metric definitions

- **Success rate** = successful picks / all generated objects (12 per seed and configuration). A pick succeeds only when the controller accepts the command and the pick window is met. Objects not attempted after escalation remain in the denominator as failures. Rejected attempts are not successes.
- **MAE** = sum of pick-window errors over all attempted picks / number of attempts. Each error is `max(2D Euclidean position error, |actual time − command time| × command speed)`, in world-distance units. Successful and failed attempts both count. Objects never attempted after escalation add no error sample. MAE is 0 only when there are no attempts in the whole group.
- **Escalations** count residual safety escalations (once per episode) and controller rejections.

The former `0.011` combo MAE with 0 success was a benchmark aggregation bug: the old mean of episode MAEs included 0 for episodes with no attempts, even though the few attempted picks all failed. Success still used all generated objects as its denominator. The benchmark now computes MAE from the global error sum divided by global attempts.

The frozen v2 blind evaluation uses 100 seeds (`2000–2099`) at code version `c66b4bf`. Nominal success was 1.000 with both compensation modes; combo success was 0.000 off and 0.008 on, with 100 escalations in each mode. The complete scenario table is in the Chinese README; raw results are in `bench.json` and `bench.md`. Combo fast-layer fail-closed behavior is a known failure mode described in [FAILURE_MODES.md](FAILURE_MODES.md).
