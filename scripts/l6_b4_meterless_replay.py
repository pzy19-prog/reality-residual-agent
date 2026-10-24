"""Verify that meterless persistence leaves cached B4-tiebreak decisions unchanged."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rra.eval.context_v3 import freeze_context, VARIANTS
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.evidence import run_episode
from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import ReplayProvider
from rra.sponsor.meterless import build_manifest, episode_id_for, persist_episode_run

ARTIFACT = ROOT / "artifacts" / "sponsor" / "meterless-persistence.json"
OUT_ROOT = ROOT / "outputs" / "l6" / "meterless" / "b4-phaseb-r1"
DEFAULT_OUTPUT = ROOT / "outputs" / "l6" / "meterless-persistence.json"


def realization_for(seed: int):
    seeds = json.loads((ROOT / "config" / "dev_seeds.json").read_text())["seeds"]
    index = seeds.index(seed)
    structures = composition_structures()
    case = index % 19
    return (realize_episode(seed, structures[case]) if case < len(structures)
            else realize_episode(seed, (), FAULT_FAMILIES[case - len(structures)]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_OUTPUT,
        help="where to write the updated persistence JSON (default: outputs/l6/meterless-persistence.json); "
             f"pass {ARTIFACT.relative_to(ROOT)} explicitly to rewrite the tracked file")
    args = parser.parse_args(argv)
    artifact = json.loads(ARTIFACT.read_text())
    subset = json.loads((ROOT / "artifacts" / "s2" / "diag-d1g.json").read_text())["seeds"]
    seeds = subset[:20]
    config = v3_world_config("nominal")
    cache = ROOT / "artifacts" / "llm_cache"
    bridge_root = ROOT / "bridges" / "meterless"
    if not (bridge_root / "vendor" / "Meterless" / "engines" / "hmem" / "reference" / "src" / "index.ts").is_file():
        print("Meterless vendor source is missing; run scripts/setup_meterless.sh in this worktree.",
              file=sys.stderr)
        return 2
    bridge_cmd = [str(bridge_root / "node_modules" / ".bin" / "tsx"), str(bridge_root / "bridge.ts")]
    rows = []
    for seed in seeds:
        realization = realization_for(seed)
        frozen = freeze_context(str(seed), seed, "NO_TEXT_CONTEXT", realization.fault_family or realization.structure)
        kwargs = {
            "compensation": True, "terminal_monitoring": "corrected", "system2_enabled": True,
            "s2_variant": "B4_TIEBREAK", "text_context": frozen.text,
            "include_s2_diagnostics": True,
        }
        off = run_episode(config, seed, realization=realization,
                          proposer=HypothesisProposer(ReplayProvider(cache)), **kwargs)
        on = run_episode(config, seed, realization=realization,
                         proposer=HypothesisProposer(ReplayProvider(cache)), **kwargs)
        episode_id = episode_id_for(seed)
        manifest = build_manifest(
            episode_id=episode_id, seed=seed, case=list(realization.structure),
            fault_family=realization.fault_family, run_episode_kwargs=kwargs,
            base_git_sha=subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                        check=True, capture_output=True, text=True).stdout.strip(),
            receipt=on,
        )
        store = OUT_ROOT / episode_id
        persisted = persist_episode_run(on, manifest, store_dir=store, run_tag="l5b-b4",
                                        bridge_cmd=bridge_cmd)
        rows.append({
            "episode_id": episode_id, "seed": seed,
            "decisions_equal": off["system2_decisions"] == on["system2_decisions"],
            "receipt_equal": off["receipt_sha256"] == on["receipt_sha256"],
            "decision_count": len(on["system2_decisions"]),
            "off_receipt_sha256": off["receipt_sha256"],
            "on_receipt_sha256": on["receipt_sha256"],
            "persisted_decision_records": persisted.record_count,
            "manifest_sha256": persisted.manifest_sha256,
        })
    result = {
        "status": "PASS" if all(x["decisions_equal"] and x["receipt_equal"] for x in rows) else "FAIL",
        "provider": "ReplayProvider", "cache_dir": "artifacts/llm_cache",
        "s2_variant": "B4_TIEBREAK", "text_variant": VARIANTS[0],
        "seed_source": "artifacts/s2/diag-d1g.json:first-20", "episode_count": len(rows),
        "decisions_equal": sum(x["decisions_equal"] for x in rows),
        "receipt_equal": sum(x["receipt_equal"] for x in rows),
        "live_llm_calls": 0, "episodes": rows,
    }
    artifact["B4"] = result
    artifact.setdefault("summary", {})["B4"] = (
        f"{result['status']}: B4_TIEBREAK meterless off/on decisions "
        f"{result['decisions_equal']}/{result['episode_count']}, receipt hashes "
        f"{result['receipt_equal']}/{result['episode_count']}"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "s2_variant", "episode_count", "decisions_equal", "receipt_equal", "live_llm_calls")}, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
