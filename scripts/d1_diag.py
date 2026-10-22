"""Generate RRA-D1-L1c diagnostic artifacts from dev seeds only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.eval.scoring import dispositions_for_episode, pause_clear_step, score_episode
from rra.evidence.episode import run_episode
from rra.eval.runner import score_against_b1_denominators


def selected_seeds():
    seeds = json.loads((ROOT / "config/dev_seeds.json").read_text())["seeds"]
    structures = composition_structures()
    chosen = set()
    for i, seed in enumerate(seeds):
        structure_index = i % 19
        if structure_index in (1, 2, 3):
            chosen.add(seed)
    chosen.update((46, 48, 51, 88, 103, 106))
    return seeds, structures, sorted(chosen)


def first_failure(calls, disposition, target, outcome, evaluator, dt):
    if not calls:
        return "从未升级到 S2"
    for row in calls:
        if row["n_usable_total"] < 6:
            return "n_usable<6"
        if not row["passing"]:
            return "|V|=0"
        if row["gate"] == "AMBIGUOUS":
            return "AMBIGUOUS"
        if row["action_time"] is not None and row["action_time"] > row["planned_window_end"] + 1e-9:
            return "门控时刻已在拾取窗口外"
        if row["action"] == "UPDATE_MODEL_AND_REPLAN":
            break
    if disposition == "REFUSE" or disposition == "PAUSE_THEN_RECOVER":
        return "已授权但 unsafe" if evaluator.get("command_issued") else "已授权但 miss/未执行"
    if evaluator.get("command_issued") and outcome.get("status") != "picked":
        return "已授权但 miss/unsafe"
    if not evaluator.get("command_issued"):
        return "已授权但 miss/未执行"
    return "未归类"


def make_diagnostic(out_path: Path):
    all_seeds, structures, seeds = selected_seeds()
    config = v3_world_config("nominal")
    episodes = []
    for seed in seeds:
        i = all_seeds.index(seed)
        ix = i % 19
        realization = realize_episode(seed, structures[ix]) if ix < len(structures) else realize_episode(
            seed, (), FAULT_FAMILIES[ix - len(structures)])
        b1 = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization)
        rec = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                          system2_enabled=True, include_trace=True, include_s2_diagnostics=True)
        scored = score_against_b1_denominators(rec, realization, config, b1)
        labels = dispositions_for_episode(realization, config.object_count)
        call_index = {}
        for call in rec.get("s2_diagnostic_trace", []):
            call_index.setdefault(call["target_id"], []).append(call)
        eval_rows = {int(x["target_id"]): x for x in rec["evaluator_objects"]}
        outcomes = {int(x["target_id"]): x for x in rec["outcomes"]}
        wrong = []
        for target, disp in labels.items():
            row, outcome = eval_rows.get(target, {}), outcomes.get(target, {})
            issued = bool(row.get("command_issued"))
            clear = pause_clear_step(realization, target, config.dt)
            wrong_disp = (disp == "RECOVER" and not issued) or (disp == "REFUSE" and issued) or (
                disp == "PAUSE_THEN_RECOVER" and issued and row.get("execution_step", -1) < clear)
            if wrong_disp:
                wrong.append({"target_id": target, "disposition": disp,
                              "first_failure": first_failure(call_index.get(target, []), disp, target,
                                                             outcome, row, config.dt),
                              "calls": call_index.get(target, []), "outcome": outcome, "evaluator": row})
        episodes.append({"seed": seed, "structure": list(realization.structure),
                         "fault_family": realization.fault_family,
                         "dispositions": {str(k): v for k, v in labels.items()},
                         "wrong_disposition_objects": wrong,
                         "unsafe_target_ids": scored["unsafe_target_ids"],
                         "system2_diagnostic_trace": rec.get("s2_diagnostic_trace", []),
                         "failure_trace": rec.get("failure_trace", []),
                         "system2_decisions": rec.get("system2_decisions", []),
                         "score": scored})
    funnel = {}
    ambiguous = []
    unsafe = []
    for ep in episodes:
        for item in ep["wrong_disposition_objects"]:
            funnel[item["first_failure"]] = funnel.get(item["first_failure"], 0) + 1
            if item["first_failure"] == "AMBIGUOUS":
                ambiguous.append({"seed": ep["seed"], "target_id": item["target_id"],
                                  "passing_sets": [c["passing"] for c in item["calls"] if c["gate"] == "AMBIGUOUS"],
                                  "true_structure": ep["structure"]})
        for target in ep["unsafe_target_ids"]:
            calls = [c for c in ep["system2_diagnostic_trace"] if c["target_id"] == target]
            unsafe.append({"seed": ep["seed"], "target_id": target, "calls": calls,
                           "decisions": [d for d in ep["system2_decisions"] if d["target_id"] == target],
                           "failure_trace": [x for x in ep["failure_trace"] if x["target_id"] == target]})
    artifact = {"phase": out_path.stem, "seed_source": "config/dev_seeds.json",
                "seeds": seeds, "diagnostic_funnel": funnel, "ambiguous_cases": ambiguous,
                "unsafe_traces": unsafe, "episodes": episodes}
    out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    md = [f"# S2 D1 diagnostic — {out_path.stem}", "", f"Dev seeds selected: {len(seeds)}", "",
          "## Wrong-disposition first-failure funnel", "", "| First failure | Objects |", "|---|---:|"]
    md += [f"| {name} | {n} |" for name, n in sorted(funnel.items())]
    md += ["", "## AMBIGUOUS cases", "", f"Count: {len(ambiguous)}", ""]
    for case in ambiguous:
        md.append(f"- seed {case['seed']}, target {case['target_id']}: passing sets `{case['passing_sets']}`, true structure `{case['true_structure']}`")
    md += ["", "## Unsafe traces", "", f"Count: {len(unsafe)}", ""]
    for item in unsafe:
        md.append(f"### Seed {item['seed']}, target {item['target_id']}")
        md.append("")
        md.append("```json")
        md.append(json.dumps(item, indent=2, ensure_ascii=False))
        md.append("```")
        md.append("")
    out_path.with_suffix(".md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "before"
    if phase not in ("before", "after"):
        raise SystemExit("phase must be before or after")
    make_diagnostic(ROOT / "artifacts/s2" / f"diag-d1-{phase}.json")
