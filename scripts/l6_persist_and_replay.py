"""L6: persist S2 runs of dev episodes to Meterless, read them back in a fresh process, and replay.

  run      persist + verify (fresh process) + write artifacts/sponsor/meterless-persistence.json
  persist  run episodes and write stores (A, plus a second copy B for the determinism check)
  verify   M1/M3/M4/M5/M8 checks against stores on disk only
  trail    print the stored decision trail of one episode
  replay   re-execute one episode from its stored manifest and compare

Stores live under outputs/l6/meterless/<run-tag>/<episode-id>/ (gitignored).
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import platform
import subprocess
import sys
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rra.eval.framework import v3_world_config
from rra.eval.scenarios import realize_episode
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures
from rra.evidence import run_episode
from rra.sponsor.meterless import (
    HIDDEN_DIAGNOSTIC_KEYS, RUN_RECORD_KEYS, BridgeError, MeterlessBridge, bridge_available,
    build_manifest, canonical_json, dir_bytes, episode_id_for, iter_keys, next_clock_ms,
    persist_episode_run, read_episode, replay_episode, sha256_file, sha256_text,
)

OUT_ROOT = ROOT / "outputs" / "l6" / "meterless"
ARTIFACT = ROOT / "artifacts" / "sponsor" / "meterless-persistence.json"
RUN_KWARGS = {"compensation": True, "terminal_monitoring": "corrected", "system2_enabled": True,
              "include_s2_diagnostics": True}
LEAK_NEEDLES = sorted(HIDDEN_DIAGNOSTIC_KEYS | {"evaluator_objects"})
MEASURE_TARGET = 20


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()


def tool_version(*cmd: str) -> str:
    return subprocess.run(list(cmd), check=True, capture_output=True, text=True).stdout.strip().splitlines()[0]


def dev_seeds() -> list[int]:
    return json.loads((ROOT / "config" / "dev_seeds.json").read_text())["seeds"]


def select_seeds(requested: list[int] | None) -> list[tuple[int, int]]:
    """(index, seed) pairs; index drives the case exactly as b3_dev._run_seed (index % 19)."""
    seeds = dev_seeds()
    chosen = requested if requested is not None else seeds[:MEASURE_TARGET]
    return [(seeds.index(s), s) for s in chosen]


def realization_for(index: int, seed: int):
    structures = composition_structures()
    ix = index % 19
    if ix < len(structures):
        return realize_episode(seed, structures[ix])
    return realize_episode(seed, (), FAULT_FAMILIES[ix - len(structures)])


def store_paths(root: Path, tag: str, episode_id: str) -> tuple[Path, Path]:
    return root / tag / episode_id, root / f"{tag}__b" / episode_id


def default_tag() -> str:
    return f"l6-{git('rev-parse', '--short', 'HEAD')}"


def base_sha() -> str:
    try:
        return git("merge-base", "HEAD", "origin/main")
    except subprocess.CalledProcessError:
        return git("rev-parse", "HEAD")


DIAGNOSTIC_ONLY_EVALUATOR_KEYS = ("actual_x_at_execution", "execution_time")


def production_view(receipt: dict) -> str:
    """Receipt minus what include_s2_diagnostics=True adds (trace, evaluator extras) and run telemetry."""
    view = json.loads(canonical_json(receipt))
    for key in ("receipt_sha256", "s2_diagnostic_trace", "system2_wall_latency_seconds", "git_sha"):
        view.pop(key, None)
    for row in view["evaluator_objects"]:
        for key in DIAGNOSTIC_ONLY_EVALUATOR_KEYS:
            row.pop(key, None)
    return canonical_json(view)


def _persist_one(job: tuple[int, int, str, str, str]) -> tuple[str, dict]:
    index, seed, root_s, tag, base = job
    root, ep = Path(root_s), episode_id_for(seed)
    config = v3_world_config("nominal")
    realization = realization_for(index, seed)
    # M2 toggle: identical run_episode kwargs, persistence off (nothing written) vs on (wrapper called below).
    off = run_episode(config, seed, realization=realization, **RUN_KWARGS)
    on = run_episode(config, seed, realization=realization, **RUN_KWARGS)
    # Supplementary: the production configuration (include_s2_diagnostics=False), which cannot be persisted.
    prod = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                       system2_enabled=True)
    snapshot_before = canonical_json(on)
    manifest = build_manifest(
        episode_id=ep, seed=seed, case=list(realization.structure), fault_family=realization.fault_family,
        run_episode_kwargs=RUN_KWARGS, base_git_sha=base, receipt=on)
    dir_a, dir_b = store_paths(root, tag, ep)
    res_a = persist_episode_run(on, manifest, store_dir=dir_a, run_tag=tag)
    res_b = persist_episode_run(on, manifest, store_dir=dir_b, run_tag=tag)
    return ep, {
        "seed": seed, "index": index, "case": list(realization.structure),
        "fault_family": realization.fault_family, "decisions": res_a.record_count,
        "record_sha256": res_a.record_sha256, "manifest_sha256": res_a.manifest_sha256,
        "memory_ids": res_a.memory_ids, "manifest_memory_id": res_a.manifest_memory_id,
        "write_state_sha256": res_a.state_sha256, "write_ledger_sha256": res_a.ledger_sha256,
        "b_state_sha256": res_b.state_sha256, "b_ledger_sha256": res_b.ledger_sha256,
        "m2": {"receipt_sha256_off": off["receipt_sha256"], "receipt_sha256_on": on["receipt_sha256"],
               "receipt_unmutated_by_persist": canonical_json(on) == snapshot_before,
               "production": {
                   "receipt_sha256": prod["receipt_sha256"],
                   "decisions_equal": canonical_json(prod["system2_decisions"]) == canonical_json(on["system2_decisions"]),
                   "equal_ignoring_diagnostic_fields": production_view(prod) == production_view(on)}},
        "persist_seconds": res_a.seconds, "store_bytes": res_a.store_bytes,
    }


def pool_map(fn, jobs: list, workers: int):
    with mp.Pool(processes=max(1, min(workers, len(jobs)))) as pool:
        yield from pool.imap(fn, jobs)


def cmd_persist(args: argparse.Namespace) -> dict:
    root, tag = Path(args.out_root), args.run_tag
    base = base_sha()
    jobs = [(index, seed, str(root), tag, base) for index, seed in select_seeds(args.seeds)]
    episodes: dict[str, dict] = {}
    for ep, entry in pool_map(_persist_one, jobs, args.workers):
        episodes[ep] = entry
        print(f"persisted {ep} decisions={entry['decisions']} store_bytes={entry['store_bytes']} "
              f"persist_s={entry['persist_seconds']:.2f}", flush=True)
    expected = {"run_tag": tag, "base_git_sha": base, "episodes": episodes}
    (root / tag).mkdir(parents=True, exist_ok=True)
    (root / tag / "expected.json").write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n")
    return expected


def ledger_reads(ledger: Path) -> list[dict]:
    entries = [json.loads(line) for line in ledger.read_text().splitlines() if line]
    return [e for e in entries if e["action"] == "read"]


def _verify_one(job: tuple[str, str, str, str, dict]) -> tuple[str, dict]:
    ep, other, root_s, tag, exp = job
    root = Path(root_s)
    dir_a, dir_b = store_paths(root, tag, ep)
    # M1: round-trip in a new bridge process.
    stored = read_episode(dir_a, ep)
    got = [e["canonical_sha256"] for e in stored["runs"]]
    raw = [e["raw_sha256"] for e in stored["runs"]]
    m1_bad = sum(a != b for a, b in zip(got, exp["record_sha256"])) + abs(len(got) - len(exp["record_sha256"]))
    m1_bad += sum(a != b for a, b in zip(raw, exp["record_sha256"]))
    m1_bad += int(stored["manifest"] is None or stored["manifest"]["canonical_sha256"] != exp["manifest_sha256"])

    # M8: key sets of stored records, plus raw-text scan of the store files.
    m8_bad = 0
    for entry in stored["runs"]:
        rec = entry["record"]
        m8_bad += int(set(rec) != RUN_RECORD_KEYS)
        m8_bad += int(bool(set(iter_keys(rec)) & (HIDDEN_DIAGNOSTIC_KEYS | {"evaluator_objects"})))
    for name in ("state.json", "ledger.jsonl"):
        text = (dir_a / name).read_text()
        m8_bad += sum(needle in text for needle in LEAK_NEEDLES)

    # M3 negative: a different episode id must be refused and leave the ledger untouched.
    ledger_before = sha256_file(dir_a / "ledger.jsonl")
    with MeterlessBridge() as bridge:
        bridge.open(dir_a, next_clock_ms(dir_a), actor="rra.s2.negative")
        try:
            bridge.get(other, exp["manifest_memory_id"])
            neg_code = None
        except BridgeError as exc:
            neg_code = exc.code
        try:
            bridge.get(ep, "mem-999999")
            notfound_code = None
        except BridgeError as exc:
            notfound_code = exc.code
    neg_ok = neg_code == "E_CROSS_EPISODE" and notfound_code == "E_NOT_FOUND"
    neg_no_read = sha256_file(dir_a / "ledger.jsonl") == ledger_before

    # M4: replay from the stored manifest only.
    replay = replay_episode(dir_a, ep)

    # M3 positive: every read entry must be same-episode (scanned after all reads above).
    reads = ledger_reads(dir_a / "ledger.jsonl")
    m3_bad = sum(not (r["details"]["reader_episode_id"] == r["details"]["record_episode_id"] == ep)
                 for r in reads)

    # M5: the untouched copy B must equal A's write-phase hashes.
    m5_ok = (exp["write_state_sha256"] == exp["b_state_sha256"] == sha256_file(dir_b / "state.json")
             and exp["write_ledger_sha256"] == exp["b_ledger_sha256"] == sha256_file(dir_b / "ledger.jsonl")
             and sha256_file(dir_a / "state.json") == exp["write_state_sha256"])

    m2 = exp["m2"]
    result = {
        "seed": exp["seed"], "case": exp["case"], "fault_family": exp["fault_family"],
        "decisions": exp["decisions"],
        "decisions_without_diagnostic": sum(e["record"]["diagnostic"] is None for e in stored["runs"]),
        "state_sha256": exp["write_state_sha256"], "ledger_sha256": exp["write_ledger_sha256"],
        "M1_roundtrip_mismatches": m1_bad,
        "M2_receipt_equal": m2["receipt_sha256_off"] == m2["receipt_sha256_on"] and m2["receipt_unmutated_by_persist"],
        "M2_production_decisions_equal": m2["production"]["decisions_equal"],
        "M2_production_receipt_sha_literal_equal": m2["production"]["receipt_sha256"] == m2["receipt_sha256_on"],
        "M2_production_receipt_equal_ignoring_diagnostic_fields": m2["production"]["equal_ignoring_diagnostic_fields"],
        "M3_cross_episode_reads": m3_bad, "M3_read_entries": len(reads),
        "M3_negative": {"reader": other, "code": neg_code, "not_found_code": notfound_code,
                        "no_read_entry_written": neg_no_read},
        "M4_replay_decisions_match": replay["decisions_match"],
        "M4_replay_receipt_match": replay["receipt_match"],
        "M5_state_ledger_identical": m5_ok,
        "M8_hidden_key_hits": m8_bad,
        "ok": (m1_bad == 0 and m2["receipt_sha256_off"] == m2["receipt_sha256_on"]
               and m2["receipt_unmutated_by_persist"] and m2["production"]["decisions_equal"]
               and m2["production"]["equal_ignoring_diagnostic_fields"] and m3_bad == 0 and neg_ok and neg_no_read
               and replay["decisions_match"] and replay["receipt_match"] and m5_ok and m8_bad == 0),
        "persist_seconds": exp["persist_seconds"], "store_bytes": exp["store_bytes"],
    }
    return ep, result


def cmd_verify(args: argparse.Namespace) -> dict:
    root, tag = Path(args.out_root), args.run_tag
    expected = json.loads((root / tag / "expected.json").read_text())
    ids = sorted(expected["episodes"])
    jobs = [(ep, ids[(n + 1) % len(ids)] if len(ids) > 1 else "ep-other", str(root), tag, expected["episodes"][ep])
            for n, ep in enumerate(ids)]
    results: dict[str, dict] = {}
    for ep, result in pool_map(_verify_one, jobs, args.workers):
        results[ep] = result
        print(f"verified {ep} ok={result['ok']} decisions={result['decisions']}", flush=True)

    n = len(results)
    summary = {
        "episodes": n,
        "M1_roundtrip_mismatches": sum(r["M1_roundtrip_mismatches"] for r in results.values()),
        "M2_equal": sum(r["M2_receipt_equal"] for r in results.values()),
        "M2_production_decisions_equal": sum(r["M2_production_decisions_equal"] for r in results.values()),
        "M2_production_receipt_sha_literal_equal": sum(
            r["M2_production_receipt_sha_literal_equal"] for r in results.values()),
        "M2_production_receipt_equal_ignoring_diagnostic_fields": sum(
            r["M2_production_receipt_equal_ignoring_diagnostic_fields"] for r in results.values()),
        "M3_cross_episode_reads": sum(r["M3_cross_episode_reads"] for r in results.values()),
        "M3_negative_refused": sum(r["M3_negative"]["code"] == "E_CROSS_EPISODE"
                                   and r["M3_negative"]["no_read_entry_written"] for r in results.values()),
        "M4_replay_match": sum(r["M4_replay_decisions_match"] and r["M4_replay_receipt_match"]
                               for r in results.values()),
        "M5_identical": sum(r["M5_state_ledger_identical"] for r in results.values()),
        "M8_hidden_key_hits": sum(r["M8_hidden_key_hits"] for r in results.values()),
        "B4": "DEFERRED: L5/D4",
        "all_ok": all(r["ok"] for r in results.values()),
    }
    vendor = ROOT / "bridges" / "meterless" / "vendor" / "Meterless"
    out = {
        "schema": "rra.l6.meterless_persistence.v1",
        "run_tag": tag, "base_git_sha": expected["base_git_sha"],
        "meterless_sha": subprocess.run(["git", "-C", str(vendor), "rev-parse", "HEAD"], check=True,
                                        capture_output=True, text=True).stdout.strip(),
        "node": tool_version("node", "-v"),
        "tsx": tool_version(str(ROOT / "bridges" / "meterless" / "node_modules" / ".bin" / "tsx"), "--version"),
        "python": platform.python_version(),
        "summary": summary, "episodes": results,
    }
    (root / tag / "results.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    if args.artifact:
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTIFACT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return out


def cmd_trail(args: argparse.Namespace) -> None:
    ep = args.episode
    stored = read_episode(Path(args.out_root) / args.run_tag / ep, ep)
    m = stored["manifest"]["record"]
    print(f"{ep}: seed={m['seed']} case={m['case']} fault_family={m['fault_family']} "
          f"decisions={len(stored['runs'])} receipt_sha256={m['receipt_sha256'][:16]}")
    for entry in stored["runs"]:
        d = entry["record"]["decision"]
        print(f"  {entry['memory_id']} #{entry['record']['decision_index']} t={d['time']:.3f} "
              f"target={d['target_id']} action={d['action']} gate={d['gate_reason']} faults={d['faults'] if 'faults' in d else []}")


def cmd_replay(args: argparse.Namespace) -> None:
    ep = args.episode
    result = replay_episode(Path(args.out_root) / args.run_tag / ep, ep)
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["decisions_match"] and result["receipt_match"] else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["run", "persist", "verify", "trail", "replay"])
    parser.add_argument("--run-tag", default=None)
    parser.add_argument("--out-root", default=str(OUT_ROOT))
    parser.add_argument("--seeds", type=int, nargs="*", default=None)
    parser.add_argument("--episode", default=None, help="episode id such as ep-014 (trail/replay)")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--artifact", action="store_true", help="verify: also write artifacts/sponsor JSON")
    args = parser.parse_args()
    if not bridge_available():
        sys.exit("Meterless bridge not available: run scripts/setup_meterless.sh (needs node)")
    args.run_tag = args.run_tag or default_tag()
    if args.command == "run":
        start = perf_counter()
        cmd_persist(args)
        subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "verify", "--run-tag", args.run_tag,
                        "--out-root", args.out_root, "--workers", str(args.workers),
                        *(["--artifact"] if args.seeds is None else [])], check=True)
        print(f"total_seconds={perf_counter() - start:.1f}")
    elif args.command == "persist":
        cmd_persist(args)
    elif args.command == "verify":
        out = cmd_verify(args)
        sys.exit(0 if out["summary"]["all_ok"] else 1)
    elif args.command == "trail":
        cmd_trail(args)
    else:
        cmd_replay(args)


if __name__ == "__main__":
    main()
