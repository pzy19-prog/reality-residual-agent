# Reality Residual Agent

Reality Residual Agent (RRA) is a deterministic 2D conveyor pick simulation for robotics developers studying how model error becomes action risk and when a controller should stop and escalate. It is a research simulator, not a deployed industrial controller. Explicit seeds drive each episode; disturbances, observations, and actions are recorded in receipts for replay and audit.

## Architecture

The fast residual layer compares observations with nominal motion predictions and corrects pick timing within bounded limits. It stops and escalates outside those limits. System 2 B3 performs deterministic hypothesis search over a constrained candidate space. Optional B4 uses NVIDIA NIM to rank proposals and break ties, but proposals pass whitelist, fitter, verifier, and explicit authorization checks before execution. Unverified proposals cannot become control actions. Under A04 §2, STRICT equals B3 by construction; this is not new evidence of model benefit.

Zetaris provides an evidence view. Meterless persists decisions per episode, refuses cross-episode reads, and supports replay from a stored manifest. See the evidence and boundaries below. The quickstart requires no secret, NIM, or online service.

## Quick development smoke

Requires Python 3.12. [`requirements.txt`](requirements.txt) pins NumPy 2.5.4 and allows Pydantic `>=2.6,<3` and pytest `>=8,<9`. Install the Python application dependencies, then run one deterministic development episode. Use an explicit output directory to keep the receipt outside the repository:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p /tmp/rra-demo
PYTHONPATH=src .venv/bin/python ./rra run --scenario bias --seed 7 --compensation on --output-dir /tmp/rra-demo
```

Measured with Python 3.12.3 and NumPy 2.5.4: the command exited successfully and wrote `bias-seed7-on.json`, with attempted=12, successes=12, escalations=0. This single-episode smoke makes no model call and is not a formal evaluation.

Meterless is an optional development integration and requires Node 22. See the [demo runbook](docs/DEMO_RUNBOOK.md) to install the pinned bridge and run a real persistence demonstration. A live Zetaris environment is also optional and requires user-provided service configuration; this documentation does not require credentials. The recorded Zetaris receipt is prior integration evidence, not a new query.

The Docker image is limited to the same Python-only development smoke:

```bash
docker build -t rra-dev-smoke .
docker run --rm rra-dev-smoke
```

It uses the Python 3.12 slim family; this build ran Python 3.12.13 and NumPy 2.5.4. The image contains the `rra.eval.final_v3` module copied with `src`, but lacks `.git` metadata, the scored eval-v3 artifacts, and optional sponsor runtime, so it does not support formal replay. It is not a sponsor-stack image.

## Formal eval-v3 results

These numbers come from the registered 100-seed results and their static audit. They are **not new scores from this smoke or the Meterless dev demo**. The denominator is 614 recoverable challenges. Unsafe values are action counts, not episode percentages.

| Condition | Challenge recovery | Unsafe actions | Interpretation |
|---|---:|---:|---|
| B2 | 104 / 614 | 47 | Broader-envelope static baseline in the same formal comparison |
| B3 | 41 / 614 | 15 | All 15 are fast-layer actions; S2-authorized unsafe actions: 0 (159 authorization events) |
| B4 STRICT (each of four text conditions) | 41 / 614 | 15 | Equal to B3 by construction, not independent model-benefit evidence |
| B4 TIEBREAK (each of four text conditions) | 39 / 614 | 58–59 | Each condition has 15 fast-layer and 43–44 S2-authorized unsafe actions; recovery did not improve |

Results, receipt fields, and audit: [B2](artifacts/eval_v3/b2.md) / [B2 JSON](artifacts/eval_v3/b2.json), [B3](artifacts/eval_v3/b1b3.md) / [B3 JSON](artifacts/eval_v3/b1b3.json), [B4](artifacts/eval_v3/b4.md) / [B4 JSON](artifacts/eval_v3/b4.json), [per-condition response and reporting audit](artifacts/eval_v3/reporting_audit.md) / [machine-readable audit](artifacts/eval_v3/reporting_audit.json). The audit documents STRICT=B3 as a design construction. TIEBREAK recovered 39 and had 58–59 unsafe actions; the evidence does not support a model-improves-recovery or zero-overall-risk claim.

The counts above map to receipt fields as follows: B2 uses `challenge_success_count`; B3 uses `recoverable_challenge_success_count`. Both use `recoverable_challenge_count` as the denominator. Source splits for B3/B4 are in `unsafe_action_by_source` and `unsafe_by_source`; the reporting audit contains the STRICT/TIEBREAK response categories and gate counts. Action counts are not episode rates.

Call statistics use different units and phases. The original live fill in `b4_live.json` records 1,519 provider `llm_calls` and 1,523 `distinct_live_requests`. The scored replay in `b4.json` records 1,519 `llm_calls`, **0 new live requests during scored replay** (`distinct_live_requests=0`), and 1,523 `cache_provenance.ledger` records. The replay zero does not mean the model was unused: it reuses the earlier recorded fill. Across the four text conditions there were 2,700 proposer invocations (1,352 STRICT, 1,348 TIEBREAK). These counters are separate units and should not all be called HTTP calls. A shared-provider `llm_calls=0` field on TIEBREAK rows also does not mean the model was unused.

Recorded Zetaris equivalence evidence is in [`zetaris-equivalence.json`](artifacts/sponsor/zetaris-equivalence.json): base `18041e5`, T3/T4 mismatches both 0, and T8 receipt bytes identical is true. This is a saved prior receipt, not a live query in this release task.

## Reproduction and scope

Formal offline reproduction should use the original scored result commit `dce9e802b024943cb21b8cdb621bdad34187dd73`; implementation freeze tag `impl-freeze-v3` points to `2365a220`. These are different commits. The unchanged guard on the maintained branch rejects later maintenance paths; do not substitute current main for the original result commit. See [eval-v3 reproduction](docs/REPRODUCING_EVAL_V3.md) for isolated worktree, virtual environment, and offline commands. Those commands are for future reproduction and were not rerun for this documentation task. Bitwise reproducibility applies only to the registered runner; portability across machines does not promise identical hashes.

The declared pre-existing work boundary is recorded in [`HACKATHON_BASELINE.md`](HACKATHON_BASELINE.md) and `pre-window-freeze^{commit}` (`3b56637681551f21c6b4c253be6def59389d1051`). H1 implementation before that boundary is also pre-existing work; later commits should not all be described as work newly built during the event. Cursor is optional and this README makes no claim that it was used.

Historical pointer: [older eval-v2 benchmark report](bench.md). It is not the current headline result.
