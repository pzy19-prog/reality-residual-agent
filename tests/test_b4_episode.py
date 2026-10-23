from types import SimpleNamespace

from rra.eval.framework import v3_world_config
from rra.eval.scenarios import composition_structures, realize_episode
from rra.evidence import episode as episode_module
from rra.evidence import run_episode


class PassingFirstProposer:
    def __init__(self):
        self.calls = 0

    def propose(self, evidence_packet, context_text):
        self.calls += 1
        return SimpleNamespace(
            items=[SimpleNamespace(hypothesis_id=row["structure_id"])
                   for row in evidence_packet["passing"]],
            error=None,
            receipt={"unknown_ids": []},
        )


def _seed_zero():
    return realize_episode(0, composition_structures()[0])


def _seed_realization(seed):
    import json
    from rra.eval.scenarios import FAULT_FAMILIES

    seeds = json.load(open("config/dev_seeds.json"))["seeds"]
    index = seeds.index(seed)
    structures = composition_structures()
    case = index % 19
    return (realize_episode(seed, structures[case]) if case < len(structures)
            else realize_episode(seed, (), FAULT_FAMILIES[case - len(structures)]))


def test_b4_strict_preserves_b3_decisions_and_records_proposal_rank():
    config = v3_world_config("nominal")
    realization = _seed_zero()
    baseline = run_episode(config, 0, True, terminal_monitoring="corrected",
                           realization=realization, system2_enabled=True)
    proposer = PassingFirstProposer()
    strict = run_episode(config, 0, True, terminal_monitoring="corrected",
                         realization=realization, system2_enabled=True,
                         s2_variant="B4_STRICT", proposer=proposer)

    assert strict["system2_decisions"] == baseline["system2_decisions"]
    assert len(strict["system2_proposal_rank"]) == proposer.calls
    assert proposer.calls == sum(
        not decision["faults"] and decision["gate_reason"] == "AMBIGUOUS"
        for decision in baseline["system2_decisions"]
    )


def test_b4_tiebreak_authorizations_still_pass_through_authorize(monkeypatch):
    config = v3_world_config("nominal")
    realization = _seed_realization(21)
    authorized = []
    original = episode_module.authorize

    def checked_authorize(*args, **kwargs):
        result = original(*args, **kwargs)
        authorized.append(result)
        return result

    monkeypatch.setattr(episode_module, "authorize", checked_authorize)
    tie = run_episode(config, 21, True, terminal_monitoring="corrected",
                      realization=realization, system2_enabled=True,
                      s2_variant="B4_TIEBREAK", proposer=PassingFirstProposer())
    text_ties = [d for d in tie["system2_decisions"] if d["gate_reason"] == "TEXT_TIEBREAK"]
    assert text_ties
    authorized_rows = [row for row in text_ties if row.get("authorization") is not None]
    assert authorized_rows
    approved_ids = {item.authorization_id for item in authorized}
    assert all(row["authorization"]["authorization_id"] in approved_ids
               for row in authorized_rows)


def test_b4_tiebreak_falls_back_when_proposal_contains_fault_id():
    config = v3_world_config("nominal")
    realization = _seed_zero()

    class FaultFirstProposer(PassingFirstProposer):
        def propose(self, evidence_packet, context_text):
            super().propose(evidence_packet, context_text)
            return SimpleNamespace(
                items=[SimpleNamespace(hypothesis_id="SENSOR_STUCK"),
                       *[SimpleNamespace(hypothesis_id=row["structure_id"])
                         for row in evidence_packet["passing"]]],
                error=None,
                receipt={"unknown_ids": []},
            )

    tie = run_episode(config, 0, True, terminal_monitoring="corrected",
                      realization=realization, system2_enabled=True,
                      s2_variant="B4_TIEBREAK", proposer=FaultFirstProposer())
    assert any(d["gate_reason"] == "TIEBREAK_FALLBACK:FAULT_ID"
               for d in tie["system2_decisions"])


def test_b4_tiebreak_falls_back_when_proposal_contains_unknown_id():
    config = v3_world_config("nominal")
    realization = _seed_zero()

    class UnknownIdProposer(PassingFirstProposer):
        def propose(self, evidence_packet, context_text):
            super().propose(evidence_packet, context_text)
            return SimpleNamespace(
                items=[SimpleNamespace(hypothesis_id=row["structure_id"])
                       for row in evidence_packet["passing"]],
                error=None,
                receipt={"unknown_ids": ["NOT_REGISTERED"]},
            )

    tie = run_episode(config, 0, True, terminal_monitoring="corrected",
                      realization=realization, system2_enabled=True,
                      s2_variant="B4_TIEBREAK", proposer=UnknownIdProposer())
    assert any(d["gate_reason"] == "TIEBREAK_FALLBACK:UNKNOWN_ID"
               for d in tie["system2_decisions"])


def test_b3_default_and_explicit_variant_have_identical_receipt_hashes():
    config = v3_world_config("nominal")
    realization = _seed_zero()
    implicit = run_episode(config, 0, True, terminal_monitoring="corrected",
                           realization=realization, system2_enabled=True)
    explicit = run_episode(config, 0, True, terminal_monitoring="corrected",
                           realization=realization, system2_enabled=True,
                           s2_variant="B3", proposer=PassingFirstProposer())
    assert implicit["receipt_sha256"] == explicit["receipt_sha256"]
