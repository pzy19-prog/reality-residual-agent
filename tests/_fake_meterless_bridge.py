"""In-memory stand-in for bridges/meterless/bridge.ts: same JSON-lines protocol, no Node needed."""
import json
import sys
from pathlib import Path

store: Path | None = None
records: dict[str, dict] = {}
clock = 0
seq = 0


def tick() -> int:
    global clock
    clock += 1
    return clock - 1


def log(entry: dict) -> None:
    with (store / "ledger.jsonl").open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def fail(code: str, message: str) -> dict:
    return {"ok": False, "code": code, "message": message}


def handle(req: dict) -> dict:
    global store, clock, seq
    op = req.get("op")
    if op == "open":
        store = Path(req["store_dir"])
        store.mkdir(parents=True, exist_ok=True)
        clock = req["clock_start_ms"]
        state = store / "state.json"
        if state.exists():
            saved = json.loads(state.read_text())
            seq = saved["seq"]
            records.update({r["id"]: r for r in saved["records"]})
        (store / "ledger.jsonl").touch()
        return {"ok": True, "store_dir": str(store), "records": len(records)}
    if store is None:
        return fail("E_BAD_REQUEST", "store not opened")
    if op == "put":
        seq += 1
        rec = {"id": f"mem-{seq}", "content": req["content"], "chatId": req["episode_id"],
               "kind": req["kind"], "timestamp": tick()}
        records[rec["id"]] = rec
        (store / "state.json").write_text(json.dumps({"seq": seq, "records": list(records.values())}, sort_keys=True))
        log({"memoryId": rec["id"], "action": "create", "timestamp": tick()})
        return {"ok": True, "memory_id": rec["id"], "timestamp": rec["timestamp"]}
    if op == "get":
        rec = records.get(req["memory_id"])
        if rec is None:
            return fail("E_NOT_FOUND", "unknown memory id")
        if rec["chatId"] != req["reader_episode_id"]:
            return fail("E_CROSS_EPISODE", "memory belongs to another episode")
        log({"memoryId": rec["id"], "action": "read", "timestamp": tick(),
             "details": {"reader_episode_id": req["reader_episode_id"], "record_episode_id": rec["chatId"]}})
        return {"ok": True, "memory_id": rec["id"], "episode_id": rec["chatId"], "kind": rec["kind"],
                "timestamp": rec["timestamp"], "content": rec["content"]}
    if op == "list":
        items = [{"memory_id": r["id"], "kind": r["kind"], "timestamp": r["timestamp"]}
                 for r in records.values() if r["chatId"] == req["reader_episode_id"]]
        return {"ok": True, "items": items}
    if op == "close":
        return {"ok": True, "closed": True}
    return fail("E_BAD_REQUEST", f"unknown op {op!r}")


for line in sys.stdin:
    if not line.strip():
        continue
    response = handle(json.loads(line))
    print(json.dumps(response), flush=True)
    if json.loads(line).get("op") == "close":
        break
