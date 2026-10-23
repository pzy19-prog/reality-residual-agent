"""L1d dev-only rerun of the preregistered S2 trigger diagnostic subset."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.eval.scoring import dispositions_for_episode, pause_clear_step
from rra.evidence.episode import run_episode
from rra.eval.runner import score_against_b1_denominators


def selected_seeds():
    seeds = json.loads((ROOT / "config/dev_seeds.json").read_text())["seeds"]
    structures = composition_structures()
    chosen = {seed for i, seed in enumerate(seeds) if i % 19 in (1, 2, 3)}
    chosen.update((46, 48, 51, 88, 103, 106))
    return seeds, structures, sorted(chosen)


def first_failure(calls, disposition, outcome, evaluator):
    if not calls:
        return "从未升级到 S2"
    for row in calls:
        if row["n_usable_total"] < 6:
            return "n_usable<6"
        if not row["passing"]:
            return "|V|=0"
        if row["gate"] == "AMBIGUOUS":
            return "AMBIGUOUS"
        if row["action_time"] is not None and row.get("planned_window_end") is not None \
                and row["action_time"] > row["planned_window_end"] + 1e-9:
            return "门控时刻已在拾取窗口外"
        if row["action"] == "UPDATE_MODEL_AND_REPLAN":
            break
    if evaluator.get("command_issued") and outcome.get("status") != "picked":
        return "已授权但 miss/unsafe"
    return "已授权但 miss/未执行"


def d_trace(seed, target, calls, realization, evaluator, failure_trace):
    if (seed, target) not in ((48, 0), (88, 0)):
        return None
    tau_true = realization.recoverable.get("speed_step_time")
    command_time = next((row.get("command_time") for row in failure_trace if row.get("command_issued")), None)
    execution_x = evaluator.get("actual_x_at_execution")
    rows = []
    for call in calls:
        if call["action"] != "UPDATE_MODEL_AND_REPLAN":
            continue
        decision = call.get("decision_observation", {})
        t = call.get("action_time")
        models = {tuple(f["structure"]): f for f in call["fits"]}
        hypotheses = []
        for structure in call["passing"]:
            fit = models.get(tuple(structure), {})
            params = fit.get("parameters", {})
            tau = params.get("speed_step_time")
            hypotheses.append({"structure": structure, "fitted_tau": tau,
                               "predicted_x_at_execution": None if t is None else (
                                   decision["nominal_x"]
                                   + params.get("velocity_offset", 0.0) * (t + params.get("actuator_delay", 0.0))
                                   + params.get("speed_step_delta", 0.0) * max(
                                       0.0, t + params.get("actuator_delay", 0.0) - (tau or 0.0))
                                   - params.get("sensor_bias", 0.0)
                                   + decision["nominal_speed"] * (t + params.get("actuator_delay", 0.0)
                                                                  - decision["time"])
                               )})
        rows.append({"decision_time": call["sim_time"], "V": hypotheses,
                     "command_time": t, "execution_actual_x": execution_x})
    return {
        "seed": seed, "target_id": target, "true_speed_step_time": tau_true,
        "s2_authorization_decisions": rows, "command_time": command_time,
        "execution_actual_x": execution_x,
        "step_after_decision": bool(rows and tau_true is not None and tau_true > rows[-1]["decision_time"]),
        "conclusion": {
            "FACT": [f"realized speed_step_time={tau_true}",
                     f"final S2 decision time={rows[-1]['decision_time'] if rows else None}",
                     f"command time={command_time}", f"actual execution x={execution_x}"],
            "INFERENCE": ["阶跃是否发生在最终授权决策之后由以上 sim-time 比较计算；S2 只接收截至决策时刻的 policy-visible 观测。"],
        },
    }


def make_diagnostic():
    all_seeds, structures, seeds = selected_seeds()
    config = v3_world_config("nominal")
    episodes, d_cases = [], []
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
        calls_by_target = {}
        for call in rec.get("s2_diagnostic_trace", []):
            calls_by_target.setdefault(call["target_id"], []).append(call)
        eval_rows = {int(row["target_id"]): row for row in rec["evaluator_objects"]}
        outcomes = {int(row["target_id"]): row for row in rec["outcomes"]}
        failures = {int(row["target_id"]): row for row in rec.get("failure_trace", [])}
        wrong = []
        for target, disposition in labels.items():
            evaluator = eval_rows.get(target, {})
            outcome = outcomes.get(target, {})
            issued = bool(evaluator.get("command_issued"))
            clear_step = pause_clear_step(realization, target, config.dt)
            wrong_disposition = ((disposition == "RECOVER" and not issued)
                                 or (disposition == "REFUSE" and issued)
                                 or (disposition == "PAUSE_THEN_RECOVER" and issued
                                     and evaluator.get("execution_step", -1) < clear_step))
            if wrong_disposition:
                wrong.append({"target_id": target, "disposition": disposition,
                              "first_failure": first_failure(calls_by_target.get(target, []), disposition,
                                                             outcome, evaluator),
                              "calls": calls_by_target.get(target, []), "outcome": outcome,
                              "evaluator": evaluator})
            d = d_trace(seed, target, calls_by_target.get(target, []), realization, evaluator,
                        [failures[target]] if target in failures else [])
            if d is not None and scored["unsafe_target_ids"] and target in scored["unsafe_target_ids"]:
                d_cases.append(d)
        episodes.append({"seed": seed, "structure": list(realization.structure),
                         "fault_family": realization.fault_family,
                         "wrong_disposition_objects": wrong,
                         "unsafe_target_ids": scored["unsafe_target_ids"],
                         "system2_diagnostic_trace": rec.get("s2_diagnostic_trace", []),
                         "system2_decisions": rec.get("system2_decisions", []),
                         "system2_episode_authorizations": rec.get("system2_episode_authorizations", []),
                         "failure_trace": rec.get("failure_trace", []), "score": scored})
    funnel = {}
    for ep in episodes:
        for row in ep["wrong_disposition_objects"]:
            key = row["first_failure"]
            funnel[key] = funnel.get(key, 0) + 1
    artifact = {"phase": "diag-d1d", "seed_source": "config/dev_seeds.json", "seeds": seeds,
                "diagnostic_funnel": funnel, "unsafe_diagnostics": d_cases, "episodes": episodes}
    path = ROOT / "artifacts/s2/diag-d1d.json"
    path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
    l1c = json.loads((ROOT / "artifacts/s2/diag-d1-after.json").read_text())["diagnostic_funnel"]
    names = sorted(set(l1c) | set(funnel))
    md = ["# S2 D1d diagnostic", "", f"Dev subset: {len(seeds)} seeds", "",
          "## Wrong-disposition first-failure funnel", "", "| First failure | L1c after | L1d after |", "|---|---:|---:|"]
    md += [f"| {name} | {l1c.get(name, 0)} | {funnel.get(name, 0)} |" for name in names]
    md += ["", "## Unsafe diagnostic cases", ""]
    for case in d_cases:
        md += [f"### Seed {case['seed']}, target {case['target_id']}", "", "```json",
               json.dumps(case, indent=2, ensure_ascii=False), "```", ""]
    (ROOT / "artifacts/s2/diag-d1d.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    make_diagnostic()
