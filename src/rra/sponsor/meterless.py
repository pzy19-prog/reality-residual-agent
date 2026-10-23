"""Persist System-2 episode runs to Meterless H-MEM through a JSON-lines bridge (A02 section 5).

Persistence is a wrapper that runs after ``run_episode`` returns; it never touches the episode.
Hidden evaluator truth is stripped from every stored record.
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[3]
BRIDGE_DIR = ROOT / "bridges" / "meterless"
RUN_SCHEMA = "rra.s2_run.v1"
MANIFEST_SCHEMA = "rra.s2_manifest.v1"
WORLD_CONFIG = "v3/nominal"
WRITE_CLOCK_START_MS = 1_000_000

# Evaluator-only keys of s2_diagnostic_trace rows (M8); stripped before storage.
HIDDEN_DIAGNOSTIC_KEYS = frozenset({"terminal_status", "terminal_reason", "command_issued", "unsafe_witness"})
# Keys that must never appear anywhere inside a stored run record.
FORBIDDEN_RUN_KEYS = HIDDEN_DIAGNOSTIC_KEYS | frozenset({"evaluator_objects", "realization", "recoverable", "fault"})
# Every key allowed anywhere inside a stored run record (fail-closed: a new key stops persistence
# until it is reviewed for evaluator truth). Seen across the 20 dev episodes on main 2a3b52d.
ALLOWED_RUN_KEYS = frozenset({
    "action", "action_time", "actuator_delay", "attempt", "authorization", "authorization_id",
    "check_item", "check_items", "common_action_time", "controller_constraints_preserved", "decision",
    "decision_index", "decision_observation", "diagnostic", "episode_id", "evidence_ids", "evidence_refs",
    "expires_at", "fault_veto", "faults", "first_observed_at", "fit", "fits", "fitted_parameters", "gate",
    "gate_reason", "hypothesis_id", "n_usable", "n_usable_after_upgrade", "n_usable_before_upgrade",
    "n_usable_total", "nominal_speed", "nominal_x", "observed_x", "parameters", "passed", "passing",
    "pause_seconds", "permitted_action", "planned_window_end", "residual_above_threshold",
    "residual_vector", "rmse", "safe_stop_clear", "schema", "scope", "seed", "sensor_bias", "sim_time",
    "speed_step_delta", "speed_step_time", "structure", "target_id", "temporary_policy_exception",
    "terminal_condition", "time", "time_correction_seconds", "trigger", "velocity_offset", "verifications",
    "verified", "verifier_score", "violated_invariants", "window_remaining_time",
})
# Decisions appended without a diagnostic row (hard-fault latch, A02 section 5 deviation from 1:1).
UNDIAGNOSED_TRIGGERS = frozenset({"hard_fault_latch"})
RUN_RECORD_KEYS = frozenset({"schema", "episode_id", "decision_index", "decision", "diagnostic"})
MANIFEST_KEYS = frozenset({
    "schema", "episode_id", "seed", "case", "fault_family", "world_config", "run_episode_kwargs",
    "base_git_sha", "decisions_sha256", "receipt_sha256", "python", "numpy",
})


class BridgeError(RuntimeError):
    """The bridge answered ``ok: false``."""

    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class BridgeUnavailable(RuntimeError):
    """The bridge process could not be started or died."""


class PairingError(RuntimeError):
    """system2_decisions and s2_diagnostic_trace are not one-to-one."""


class LeakError(RuntimeError):
    """A hidden evaluator key reached a record that would be stored."""


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def default_bridge_cmd() -> list[str]:
    return [str(BRIDGE_DIR / "node_modules" / ".bin" / "tsx"), str(BRIDGE_DIR / "bridge.ts")]


def bridge_available() -> bool:
    return (
        shutil.which("node") is not None
        and (BRIDGE_DIR / "node_modules" / ".bin" / "tsx").exists()
        and (BRIDGE_DIR / "vendor" / "Meterless" / "engines" / "hmem" / "reference" / "src" / "index.ts").exists()
    )


def next_clock_ms(store_dir: Path) -> int:
    """First free clock tick for a re-opened store: one past the last ledger timestamp."""
    ledger = Path(store_dir) / "ledger.jsonl"
    if not ledger.exists():
        return WRITE_CLOCK_START_MS
    last = WRITE_CLOCK_START_MS - 1
    for line in ledger.read_text().splitlines():
        if line:
            last = max(last, int(json.loads(line)["timestamp"]))
    return last + 1


class MeterlessBridge:
    """Synchronous client for bridges/meterless/bridge.ts (one request line, one response line)."""

    def __init__(self, cmd: list[str] | None = None):
        self._cmd = cmd or default_bridge_cmd()
        self._proc: subprocess.Popen[str] | None = None
        self._stderr = tempfile.TemporaryFile(mode="w+")

    def __enter__(self) -> "MeterlessBridge":
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def start(self) -> None:
        try:
            self._proc = subprocess.Popen(
                self._cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr,
                text=True, encoding="utf-8", cwd=BRIDGE_DIR,
            )
        except OSError as exc:
            raise BridgeUnavailable(f"cannot start bridge {self._cmd!r}: {exc}") from exc

    def _stderr_tail(self) -> str:
        self._stderr.flush()
        self._stderr.seek(0)
        return self._stderr.read()[-2000:]

    def request(self, op: str, **fields: Any) -> dict[str, Any]:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise BridgeUnavailable("bridge not started")
        try:
            self._proc.stdin.write(json.dumps({"op": op, **fields}) + "\n")
            self._proc.stdin.flush()
            line = self._proc.stdout.readline()
        except BrokenPipeError as exc:
            raise BridgeUnavailable(f"bridge pipe closed: {self._stderr_tail()}") from exc
        if not line:
            raise BridgeUnavailable(f"bridge exited without a response: {self._stderr_tail()}")
        response = json.loads(line)
        if not response.pop("ok"):
            raise BridgeError(response["code"], response["message"])
        return response

    def open(self, store_dir: Path, clock_start_ms: int, *, run_tag: str | None = None,
             actor: str | None = None) -> dict[str, Any]:
        fields: dict[str, Any] = {"store_dir": str(store_dir), "clock_start_ms": clock_start_ms}
        if run_tag is not None:
            fields["run_tag"] = run_tag
        if actor is not None:
            fields["actor"] = actor
        return self.request("open", **fields)

    def put(self, episode_id: str, kind: str, content: str) -> dict[str, Any]:
        return self.request("put", episode_id=episode_id, kind=kind, content=content)

    def get(self, reader_episode_id: str, memory_id: str) -> dict[str, Any]:
        return self.request("get", reader_episode_id=reader_episode_id, memory_id=memory_id)

    def list(self, reader_episode_id: str) -> list[dict[str, Any]]:
        return self.request("list", reader_episode_id=reader_episode_id)["items"]

    def close(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None:
            return
        try:
            if proc.poll() is None and proc.stdin and proc.stdout:
                proc.stdin.write(json.dumps({"op": "close"}) + "\n")
                proc.stdin.flush()
                proc.stdout.readline()
        except (BrokenPipeError, OSError):
            pass
        finally:
            for stream in (proc.stdin, proc.stdout):
                if stream:
                    stream.close()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            self._stderr.close()


def episode_id_for(seed: int) -> str:
    return f"ep-{int(seed):03d}"


def iter_keys(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from iter_keys(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_keys(item)


def assert_no_forbidden_keys(record: dict[str, Any]) -> None:
    keys = set(iter_keys(record))
    leaked = sorted(keys & FORBIDDEN_RUN_KEYS)
    if leaked:
        raise LeakError(f"hidden keys in run record: {leaked}")
    unknown = sorted(keys - ALLOWED_RUN_KEYS)
    if unknown:
        raise LeakError(f"run record keys outside the whitelist: {unknown}")


def build_run_records(episode_id: str, receipt: dict[str, Any]) -> list[dict[str, Any]]:
    """Pair system2_decisions with s2_diagnostic_trace rows (hidden fields stripped).

    On merged main, trigger=hard_fault_latch decisions have no diagnostic row and are stored with
    ``diagnostic: null``. Every other decision must pair with the next diagnostic row, in order;
    any other length or identity mismatch stops persistence.
    """
    decisions = receipt.get("system2_decisions")
    trace = receipt.get("s2_diagnostic_trace")
    if decisions is None or trace is None:
        raise PairingError("receipt needs system2_enabled=True and include_s2_diagnostics=True")
    paired = [i for i, d in enumerate(decisions) if d.get("trigger") not in UNDIAGNOSED_TRIGGERS]
    if len(paired) != len(trace):
        raise PairingError(f"decisions needing a diagnostic={len(paired)} != s2_diagnostic_trace={len(trace)}")
    diag_for = dict(zip(paired, trace))
    records = []
    for index, decision in enumerate(decisions):
        diag = diag_for.get(index)
        if diag is not None and (decision["target_id"] != diag["target_id"] or decision["time"] != diag["sim_time"]):
            raise PairingError(f"decision {index} does not match its diagnostic row")
        record = {
            "schema": RUN_SCHEMA, "episode_id": episode_id, "decision_index": index,
            "decision": decision,
            "diagnostic": None if diag is None else {k: v for k, v in diag.items() if k not in HIDDEN_DIAGNOSTIC_KEYS},
        }
        assert_no_forbidden_keys(record)
        records.append(record)
    return records


def build_manifest(*, episode_id: str, seed: int, case: list[str], fault_family: str | None,
                   run_episode_kwargs: dict[str, Any], base_git_sha: str,
                   receipt: dict[str, Any]) -> dict[str, Any]:
    import numpy

    return {
        "schema": MANIFEST_SCHEMA, "episode_id": episode_id, "seed": int(seed), "case": list(case),
        "fault_family": fault_family, "world_config": WORLD_CONFIG,
        "run_episode_kwargs": dict(run_episode_kwargs), "base_git_sha": base_git_sha,
        "decisions_sha256": sha256_text(canonical_json(receipt["system2_decisions"])),
        "receipt_sha256": receipt["receipt_sha256"],
        "python": platform.python_version(), "numpy": numpy.__version__,
    }


@dataclass
class PersistResult:
    episode_id: str
    store_dir: Path
    record_count: int
    memory_ids: list[str]
    record_sha256: list[str]
    manifest_memory_id: str
    manifest_sha256: str
    state_sha256: str
    ledger_sha256: str
    store_bytes: int
    seconds: float


def dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file())


def persist_episode_run(receipt: dict[str, Any], manifest: dict[str, Any], *, store_dir: Path,
                        run_tag: str, bridge_cmd: list[str] | None = None) -> PersistResult:
    """Write one record per S2 decision, then the manifest, into a fresh per-episode store."""
    episode_id = manifest["episode_id"]
    if set(manifest) != MANIFEST_KEYS or manifest["schema"] != MANIFEST_SCHEMA:
        raise ValueError("manifest does not match rra.s2_manifest.v1")
    records = build_run_records(episode_id, receipt)
    store_dir = Path(store_dir)
    if (store_dir / "state.json").exists() or (store_dir / "ledger.jsonl").exists():
        raise FileExistsError(f"store already populated: {store_dir}")
    start = perf_counter()
    memory_ids: list[str] = []
    shas: list[str] = []
    with MeterlessBridge(bridge_cmd) as bridge:
        bridge.open(store_dir, WRITE_CLOCK_START_MS, run_tag=run_tag, actor="rra.s2")
        for record in records:
            content = canonical_json(record)
            memory_ids.append(bridge.put(episode_id, "run", content)["memory_id"])
            shas.append(sha256_text(content))
        manifest_content = canonical_json(manifest)
        manifest_id = bridge.put(episode_id, "manifest", manifest_content)["memory_id"]
    seconds = perf_counter() - start
    state, ledger = store_dir / "state.json", store_dir / "ledger.jsonl"
    return PersistResult(
        episode_id=episode_id, store_dir=store_dir, record_count=len(records), memory_ids=memory_ids,
        record_sha256=shas, manifest_memory_id=manifest_id, manifest_sha256=sha256_text(manifest_content),
        state_sha256=sha256_file(state), ledger_sha256=sha256_file(ledger),
        store_bytes=dir_bytes(store_dir), seconds=seconds,
    )


def read_episode(store_dir: Path, episode_id: str, *, bridge_cmd: list[str] | None = None,
                 run_tag: str | None = None) -> dict[str, Any]:
    """Read an episode's trail back in a fresh bridge process; every get is a ledgered read."""
    store_dir = Path(store_dir)
    out: dict[str, Any] = {"runs": [], "manifest": None}
    with MeterlessBridge(bridge_cmd) as bridge:
        bridge.open(store_dir, next_clock_ms(store_dir), run_tag=run_tag, actor="rra.s2.reader")
        for item in bridge.list(episode_id):
            got = bridge.get(episode_id, item["memory_id"])
            parsed = json.loads(got["content"])
            entry = {"memory_id": got["memory_id"], "raw_sha256": sha256_text(got["content"]),
                     "canonical_sha256": sha256_text(canonical_json(parsed)), "record": parsed}
            if got["kind"] == "manifest":
                out["manifest"] = entry
            else:
                out["runs"].append(entry)
    out["runs"].sort(key=lambda e: e["record"]["decision_index"])
    return out


def run_episode_from_manifest(manifest: dict[str, Any], *, provider: Any = None) -> dict[str, Any]:
    """Re-execute run_episode using only what the manifest records."""
    if provider is not None:
        raise NotImplementedError("provider replay cache is reserved for L5 (B4)")
    from rra.eval.framework import v3_world_config
    from rra.eval.scenarios import realize_episode
    from rra.evidence import run_episode

    if manifest["world_config"] != WORLD_CONFIG:
        raise ValueError(f"unsupported world_config {manifest['world_config']!r}")
    realization = realize_episode(manifest["seed"], tuple(manifest["case"]), manifest["fault_family"])
    return run_episode(v3_world_config("nominal"), manifest["seed"], realization=realization,
                       **manifest["run_episode_kwargs"])


def replay_episode(store_dir: Path, episode_id: str | None = None, *, provider: Any = None,
                   bridge_cmd: list[str] | None = None) -> dict[str, Any]:
    """Replay from the stored manifest and compare against the persisted decisions."""
    store_dir = Path(store_dir)
    episode_id = episode_id or store_dir.name
    stored = read_episode(store_dir, episode_id, bridge_cmd=bridge_cmd)
    if stored["manifest"] is None:
        raise BridgeError("E_NOT_FOUND", f"no manifest stored for {episode_id}")
    manifest = stored["manifest"]["record"]
    persisted_sha = sha256_text(canonical_json([r["record"]["decision"] for r in stored["runs"]]))
    receipt = run_episode_from_manifest(manifest, provider=provider)
    replay_sha = sha256_text(canonical_json(receipt["system2_decisions"]))
    return {
        "episode_id": episode_id, "decisions": len(stored["runs"]),
        "persisted_decisions_sha256": persisted_sha, "replay_decisions_sha256": replay_sha,
        "manifest_decisions_sha256": manifest["decisions_sha256"],
        "decisions_match": persisted_sha == replay_sha == manifest["decisions_sha256"],
        "receipt_match": receipt["receipt_sha256"] == manifest["receipt_sha256"],
        "replay_receipt_sha256": receipt["receipt_sha256"],
        "manifest_receipt_sha256": manifest["receipt_sha256"],
    }
