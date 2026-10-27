# Tested development demonstration

This is a fresh, deterministic development demonstration from release base `87a3124a9a337a525efdf3d5390905df9803114f`, not a registered score. It uses the real Meterless bridge pinned at `1742dec56a66e58eef9dda2d2b865823758ca8cd`; it makes no NIM/model call and does not write repository artifacts. Node was `v22.22.1`, bridge `tsx v4.23.0`, Python `3.12.3`, and NumPy `2.5.4`.

## Run it

Install Python dependencies as in the main README. The setup script checks out the pinned Meterless vendor and installs the bridge dependencies:

```bash
bash scripts/setup_meterless.sh
```

Choose an output directory outside the checkout and persist only explicit development seeds. `persist` does not write the tracked sponsor artifact; do not add `--artifact` to `verify`.

```bash
EV=/tmp/rra-meterless-demo
mkdir -p "$EV"
PY=.venv/bin/python
"$PY" scripts/l6_persist_and_replay.py persist --run-tag release-demo --seeds 0 1 2 14 --workers 2 --out-root "$EV/store"
"$PY" scripts/l6_persist_and_replay.py verify --run-tag release-demo --workers 2 --out-root "$EV/store"
for ep in ep-000 ep-001 ep-002 ep-014; do
  "$PY" scripts/l6_persist_and_replay.py trail --run-tag release-demo --episode "$ep" --out-root "$EV/store"
  "$PY" scripts/l6_persist_and_replay.py replay --run-tag release-demo --episode "$ep" --out-root "$EV/store"
done
```

The demonstrated run used `/home/mxfclaw/reality-residual-agent-worktrees/_reports/RELEASE_DOCS_EVIDENCE/meterless` as `$EV/store`. All four episodes verified: `all_ok=true`, 0 round-trip mismatches, 0 cross-episode reads, 4/4 negative cross-episode reads refused, 4/4 state+ledger copies identical, and 0 hidden-key hits. For each episode, `decisions_match=true` and `receipt_match=true`; decision counts were 12, 15, 12, and 14. Complete stdout/stderr records are in `/home/mxfclaw/reality-residual-agent-worktrees/_reports/RELEASE_DOCS_EVIDENCE/meterless-persist.log`, `meterless-verify.log`, and the adjacent `trail-*` / `replay-*` files. The export `/home/mxfclaw/reality-residual-agent-worktrees/_reports/RELEASE_DOCS_EVIDENCE/demo_excerpt.json` contains a compact real trace for `ep-014`, including recorded observation times/values, S2 decisions and reasons, bounded verifier evidence, replay hashes, and actual terminal outcomes.

For `ep-014` (development seed 14), the receipt reports 7 attempted picks and 7 successes, 1 escalation, and terminal counts of 7 picked and 5 escalated. These terminal counts are receipt fields and are not a percentage or formal score. The trace includes `NO_VERIFIED_HYPOTHESIS` decisions where only three observations were available and candidate fits failed the six-observation minimum; the demo preserves that refusal behavior instead of tuning the episode.

## Docker development smoke

The Docker image is a Python-only one-episode smoke. The default command is equivalent to:

```bash
docker run --rm rra-dev-smoke
```

It writes `/tmp/rra-demo/bias-seed7-on.json` inside the container. The tested image ran Python 3.12.13 and NumPy 2.5.4; its receipt reported attempted=12, successes=12, and escalations=0. The image does contain the `rra.eval.final_v3` module copied with `src`, but lacks Git metadata, scored eval-v3 artifacts, the Meterless/Node bridge, optional sponsor services, and model credentials. Those missing pieces mean this smoke image does not support formal replay and is not the registered eval runner image.
