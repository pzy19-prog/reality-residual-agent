import json
from pathlib import Path
from types import SimpleNamespace

from rra.eval.context_v3 import VARIANTS, freeze_context
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.evidence import run_episode
from rra.evidence.packet import packet_sha256, project_c1_known_config
from rra.evidence.sources import export_sources, load_packets


class CaptureProposer:
    def __init__(self):
        self.packets = []

    def propose(self, evidence_packet, context_text="", *, s2_summary=None):
        self.packets.append((evidence_packet, s2_summary))
        return SimpleNamespace(items=[], error=None, receipt={"unknown_ids": []})


def _realization(index, seed):
    structures = composition_structures()
    case = index % 19
    return (realize_episode(seed, structures[case]) if case < len(structures)
            else realize_episode(seed, (), FAULT_FAMILIES[case - len(structures)]))


def _diff(left, right, path="$"):
    if type(left) is not type(right) and not (isinstance(left, (int, float)) and isinstance(right, (int, float)) and not isinstance(left, bool) and not isinstance(right, bool)):
        return [f"{path}: {type(left).__name__} {left!r} != {type(right).__name__} {right!r}"]
    if isinstance(left, dict):
        found = []
        for key in sorted(set(left) | set(right), key=str):
            if key not in left or key not in right:
                found.append(f"{path}.{key}: present {key in left} vs {key in right}")
            else:
                found.extend(_diff(left[key], right[key], f"{path}.{key}"))
        return found
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{path}: len {len(left)} != {len(right)}"]
        found = []
        for index, (item, other) in enumerate(zip(left, right)):
            found.extend(_diff(item, other, f"{path}[{index}]"))
        return found
    if left != right:
        return [f"{path}: {left!r} != {right!r}"]
    return []


def test_b4_packets_match_l3_export_projection_for_three_seeds(tmp_path):
    # Seeds 0, 3 and 7 each have at least one fault-free AMBIGUOUS decision in b3-dev.
    # Seed 7's calls are late enough to include earlier command feedback.
    exported = export_sources(tmp_path / "sources", episodes=8)
    tables = exported["tables"]
    config = v3_world_config("nominal")
    compared = {}
    had_feedback = False
    for index, seed in ((0, 0), (3, 3), (7, 7)):
        realization = _realization(index, seed)
        variant = VARIANTS[index % len(VARIANTS)]
        context = freeze_context(str(seed), seed, variant,
                                 realization.fault_family or realization.structure)
        proposer = CaptureProposer()
        run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                    text_context=context.text, system2_enabled=True,
                    s2_variant="B4_STRICT", proposer=proposer)
        assert proposer.packets, f"seed {seed} produced no B4 packet"
        exported_packets = load_packets(tables, str(seed))
        by_decision = {(p["decision"]["target_id"], p["decision"]["step"]): p
                       for p in exported_packets}
        for internal, summary in proposer.packets:
            assert set(summary) == {"passing", "current_time", "horizon"}
            assert all(set(row) == {"structure_id", "rmse", "n_usable"} for row in summary["passing"])
            key = (internal["decision"]["target_id"], internal["decision"]["step"])
            reference = by_decision[key]
            projected_reference = {**reference,
                                   "known_config": project_c1_known_config(reference["known_config"])}
            assert packet_sha256(internal) == packet_sha256(projected_reference), _diff(
                internal, projected_reference)[:12]
            full_known = reference["known_config"]
            assert set(full_known) - set(projected_reference["known_config"]) == {
                "episode_steps", "object_count"}
            assert {k: v for k, v in full_known.items()
                    if k not in ("episode_steps", "object_count")} == projected_reference["known_config"]
            had_feedback |= bool(internal["command_feedback"])
        compared[seed] = len(proposer.packets)
    assert compared.keys() == {0, 3, 7}
    assert had_feedback


def test_all_diag_b4_call_points_match_projected_export_packets(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    diag_seeds = json.loads((repo / "artifacts/s2/diag-d1g.json").read_text())["seeds"]
    b3_rows = json.loads((repo / "artifacts/s2/b3-dev.json").read_text())["episodes"]
    active_seeds = [row["seed"] for row in b3_rows if row["seed"] in diag_seeds
                    and any(not decision.get("faults")
                            and decision.get("gate_reason") == "AMBIGUOUS"
                            and decision.get("trigger") != "outcome_escalation"
                            for decision in row.get("system2_decisions", []))]
    assert active_seeds == [3]
    exported = export_sources(tmp_path / "sources", episodes=4)
    tables = exported["tables"]
    config = v3_world_config("nominal")
    checked = 0
    for seed in active_seeds:
        index = seed
        realization = _realization(index, seed)
        cause = realization.fault_family or realization.structure
        exported_packets = load_packets(tables, str(seed))
        by_decision = {(p["decision"]["target_id"], p["decision"]["step"]): p
                       for p in exported_packets}
        for variant in VARIANTS:
            context = freeze_context(str(seed), seed, variant, cause)
            proposer = CaptureProposer()
            run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                        text_context=context.text, system2_enabled=True,
                        s2_variant="B4_STRICT", proposer=proposer)
            for internal, _summary in proposer.packets:
                reference = by_decision[(internal["decision"]["target_id"],
                                         internal["decision"]["step"])]
                expected = {**reference,
                            "known_config": project_c1_known_config(reference["known_config"]),
                            "context": {"text": context.text,
                                        "content_sha256": context.content_sha256}}
                assert packet_sha256(internal) == packet_sha256(expected)
                checked += 1
    assert checked == 8
