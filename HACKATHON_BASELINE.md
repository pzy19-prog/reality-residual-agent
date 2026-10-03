# Open Agent Hackathon 2026 — declared pre-existing components

Everything reachable from `v0-baseline` (`546e82aefd4e07bf304d79c63dcffe6dd4b7c4ee`) is pre-existing V0 work. The P3 design, CI/tool settings and H1 evaluation foundation listed below were also committed before the build window and are declared pre-existing. None is claimed as scored build-window implementation.

The planned window opens at 2026-10-15 00:00 UTC (08:00 Asia/Shanghai). Eligibility is determined by current organizer rules and declarations, **not** merely by whether a commit follows `v0-baseline`. The September 28 rules snapshot is historical; see [current rules review](docs/HACKATHON_RULES_REVIEW_20261004.md) for verified changes and remaining eligibility questions.

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

## Additional declared pre-window work

These components are pre-existing even when their commits follow `v0-baseline`:

| Component | Declaration and evidence |
|---|---|
| P3 design / preregistration | [P3_SYSTEM2_DESIGN.md](docs/P3_SYSTEM2_DESIGN.md), `p3-prereg` at `024ea2e3e66b91f5a2157a66c073493e7107e109`; design only, no System-2 implementation |
| CI and repository tool settings | `.github/workflows/ci.yml` and `.claude/settings.json`; pytest and dev benchmark determinism |
| H1 evaluation foundation | `prewindow/h1-eval-foundation` head `01716bfba693674d79a316bf312ce74e0289077f`, merged in `b0288da5cf7a924ce9b47b0ea9f7d6248f5f6bd0`; [foundation](docs/H1_EVAL_FOUNDATION.md), [addendum](docs/P3_PREREG_ADDENDUM_01.md) and `artifacts/h1/` |

H1 includes the sanitized policy boundary and target-presence channel, corrected terminal monitoring, v3 world/scoring/text framework, legacy-equivalence and omniscient dev receipts, B2 grid calibration, structural holdout selection and dev determinism checks. These include code and framework changes; H1 is **not** described as behavior-neutral CI tooling.

H1 does not implement System-2, LLM/NIM integration, B3/B4 runtime, recovery authorization or the final eval-v3 seed realization. Its B2 fallback is frozen at `T=1.15 s`, `R=2.15`; the structural holdout is `AND(SPEED_STEP,ACTUATOR_DELAY)`.

## Final pre-window accounting

A new `pre-hackathon-freeze` tag is planned after accepted documentation and readiness checks; **it has not been created by this update**. Do not move the existing baseline or preregistration tags.

Declare all components committed before the actual build opening, including this documentation update and any later permitted pre-window work. An independent generic API compatibility experiment remains a readiness experiment, not RRA sponsor integration or scored implementation. The final submission must distinguish pre-existing components from new in-window work and verify that the selected track accepts the declaration.

See [readiness and execution plan](docs/PREWINDOW_READINESS.md) for remaining gates and the build-window sequence.

## Baseline result (blind eval v2, 100 seeds, compensation on)

| Scenario | Success | Coverage | Precision | Escalations |
|---|---:|---:|---:|---:|
| nominal | 1.000 | 1.000 | 1.000 | 0 |
| moving-mid | 0.849 | 0.882 | 0.963 | 1 |
| load-mid | 0.656 | 0.679 | 0.966 | 18 |
| combo | 0.007 | 0.008 | 0.900 | 100 |

Full table: `bench.md`; raw artifact: `bench.json` (commit `2418406`, implementation `c66b4bf`).
