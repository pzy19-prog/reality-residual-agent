# Meterless bridge (L6)

Persists System-2 episode runs into the [Meterless](https://github.com/meterless/Meterless) H-MEM reference
implementation and reads them back. Python talks to `bridge.ts` over stdin/stdout JSON lines; the bridge
imports `engines/hmem/reference/src/index.ts` from a pinned vendor checkout and runs under `tsx`.

## Setup

```bash
scripts/setup_meterless.sh
```

Idempotent. Clones Meterless into `bridges/meterless/vendor/Meterless`, checks out
`1742dec56a66e58eef9dda2d2b865823758ca8cd`, refuses a dirty or mismatched tree, then runs
`npm ci --ignore-scripts` (only `tsx`, version-locked). `vendor/` and `node_modules/` are gitignored; vendor
files are never modified. Needs Node 22.

## Protocol

One JSON object per line in, one per line out. Responses are `{"ok": true, ...}` or
`{"ok": false, "code": ..., "message": ...}`.

| request | fields | response |
|---|---|---|
| `open` | `store_dir`, `clock_start_ms`, optional `run_tag`, `actor` | `records` |
| `put` | `episode_id`, `kind` (`run`\|`manifest`), `content` | `memory_id`, `timestamp` |
| `get` | `reader_episode_id`, `memory_id` | `content`, `episode_id`, `kind`; logs a ledger `read` |
| `list` | `reader_episode_id` | `items` of that episode only; no ledger entries |
| `close` | | `closed` |

Errors: `E_CROSS_EPISODE` (record belongs to another episode; refused before any ledger write),
`E_NOT_FOUND`, `E_BAD_REQUEST`, and `E_INTERNAL` for unexpected exceptions.

HMEM mapping: `content` is the canonical JSON string, `source="rra.s2"`, `chatId=episode_id`,
`missionId=run_tag`, `tags=["rra","s2","episode:<id>","kind:run|manifest"]`. The HMEM clock is a counter
starting at `clock_start_ms`, so ids and timestamps are deterministic.

## Use

```bash
.venv/bin/python scripts/l6_persist_and_replay.py run --run-tag demo --seeds 14
.venv/bin/python scripts/l6_persist_and_replay.py trail  --run-tag demo --episode ep-014
.venv/bin/python scripts/l6_persist_and_replay.py replay --run-tag demo --episode ep-014
RRA_METERLESS_LIVE=1 .venv/bin/python -m pytest tests/test_meterless_bridge.py -q
```
