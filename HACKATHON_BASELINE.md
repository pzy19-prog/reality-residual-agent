# Open Agent Hackathon 2026 — declared pre-existing components (V0)

Per rules 4.2 and 5.2, everything reachable from tag `v0-baseline` is pre-existing work, committed before the build window (2026-10-15T00:00Z), and is **not** submitted for judging. Hackathon work consists only of commits after that tag, excluding the pre-window infrastructure listed below.

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

## Pre-window infrastructure committed after the tag

These commits land after `v0-baseline` but before the build window opens. They are tooling only, change no agent behaviour or results, and are **not** submitted for judging:

- CI workflow `.github/workflows/ci.yml`: pytest plus a dev-seed bench determinism check.
- Repository tool settings `.claude/settings.json`.

## Baseline result (blind eval v2, 100 seeds, compensation on)

| Scenario | Success | Coverage | Precision | Escalations |
|---|---:|---:|---:|---:|
| nominal | 1.000 | 1.000 | 1.000 | 0 |
| moving-mid | 0.849 | 0.882 | 0.963 | 1 |
| load-mid | 0.656 | 0.679 | 0.966 | 18 |
| combo | 0.007 | 0.008 | 0.900 | 100 |

Full table: `bench.md`; raw artifact: `bench.json` (commit `2418406`, implementation `c66b4bf`).
