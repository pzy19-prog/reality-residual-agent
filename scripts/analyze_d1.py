"""Add evaluator-only superset and prediction-spread analysis to D1 artifacts."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prediction_at_pick(call: dict, params: dict, x_pick: float, speed: float, dt: float) -> float:
    now = call["sim_time"]
    pick_time = call["planned_window_end"] - dt / 2
    nominal_now = x_pick - speed * (pick_time - now)
    execution_time = pick_time + params.get("actuator_delay", 0.0)
    tau = params.get("speed_step_time")
    current = params.get("velocity_offset", 0.0) * now
    future = params.get("velocity_offset", 0.0) * execution_time
    if tau is not None:
        delta = params.get("speed_step_delta", 0.0)
        current += delta * max(0.0, now - tau)
        future += delta * max(0.0, execution_time - tau)
    return (nominal_now + speed * (execution_time - now) + future - current
            - params.get("sensor_bias", 0.0))


def enrich(path: Path) -> None:
    data = json.loads(path.read_text())
    episodes = {e["seed"]: e for e in data["episodes"]}
    ambiguous = []
    for ep in data["episodes"]:
        calls_by_target = {}
        for call in ep["system2_diagnostic_trace"]:
            calls_by_target.setdefault(call["target_id"], []).append(call)
        for target, calls in calls_by_target.items():
            for call in calls:
                if call["gate"] != "AMBIGUOUS":
                    continue
                v = [tuple(s) for s in call["passing"]]
                truth = set(ep["structure"])
                all_supersets = bool(v) and all(truth.issubset(set(s)) for s in v)
                fit_by_structure = {tuple(f["structure"]): f for f in call["fits"]}
                candidates = [fit_by_structure[s] for s in v if s in fit_by_structure]
                positions = [prediction_at_pick(
                    call, f["parameters"], x_pick=0.0, speed=1.0, dt=0.1
                ) for f in candidates if f["parameters"]]
                spread = max(positions) - min(positions) if len(positions) >= 2 else None
                ambiguous.append({
                    "seed": ep["seed"], "target_id": target, "sim_time": call["sim_time"],
                    "passing_structures": [list(s) for s in v], "true_structure": ep["structure"],
                    "all_passing_models_are_supersets": all_supersets,
                    "nominal_pick_time": call["planned_window_end"] - 0.05,
                    "predicted_position_spread_world_units": spread,
                    "models_with_fitted_parameters": len(positions),
                })
    data["ambiguous_cases"] = ambiguous
    data["ambiguous_analysis"] = {
        "facts": "Passing sets, registered true structures, and fitted parameters are copied from dev-only episode evidence and realization labels.",
        "inference": "Prediction spread extrapolates each passing fitted DSL to the nominal pick time using the registered DSL and per-hypothesis actuator delay; nominal x at the decision is reconstructed from the scripted pick plan.",
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    md = [
        f"# S2 D1 diagnostic — {path.stem}", "",
        f"Dev seeds selected: {len(data['seeds'])}", "",
        "## Wrong-disposition first-failure funnel", "",
        "| First failure | Objects |", "|---|---:|",
    ]
    md += [f"| {name} | {n} |" for name, n in sorted(data["diagnostic_funnel"].items())]
    md += ["", "## AMBIGUOUS nested-superset analysis", "",
           "### FACT", "",
           f"Ambiguous calls: {len(ambiguous)}. All passing structures contain the registered true structure in {sum(x['all_passing_models_are_supersets'] for x in ambiguous)} calls.", "",
           "| Seed | Target | V | All V supersets of truth | Predicted position spread at nominal pick (world units) |",
           "|---:|---:|---|---|---:|"]
    md += [f"| {x['seed']} | {x['target_id']} | `{x['passing_structures']}` | {x['all_passing_models_are_supersets']} | {x['predicted_position_spread_world_units']} |" for x in ambiguous]
    md += ["", "### INFERENCE", "", data["ambiguous_analysis"]["inference"], "",
           "## Unsafe traces", "", f"Count: {len(data['unsafe_traces'])}", ""]
    for item in data["unsafe_traces"]:
        md += [f"### Seed {item['seed']}, target {item['target_id']}", "", "```json",
               json.dumps(item, indent=2, ensure_ascii=False), "```", ""]
    path.with_suffix(".md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    for phase in ("before", "after"):
        target = ROOT / "artifacts" / "s2" / f"diag-d1-{phase}.json"
        if target.exists():
            enrich(target)
