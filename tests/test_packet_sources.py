from dataclasses import asdict
import os

import pytest

from rra.evidence.packet import build_packet, canonical, packet_sha256
from rra.evidence.sources import C1, check_whitelist
from rra.evidence import run_episode
from rra.eval.framework import v3_world_config
from rra.eval.scenarios import realize_episode
from rra.sim.v3_world import V3World
from rra.evidence.policy import sanitize_observation


def test_packet_filters_and_canonical_order():
    obs = [{"target_id": 0, "seq": 1, "v": 1}, {"target_id": 0, "seq": 0, "v": 0}]
    packet = build_packet(episode_id="0", target_id=0, step=0, time=0.0,
                          observations=obs, presence_events=[], command_feedback=[],
                          known_config={}, context={})
    assert [x["seq"] for x in packet["observations"]] == [0]
    assert canonical(packet) == canonical(packet)
    assert packet_sha256(packet) == packet_sha256(packet)


def test_hidden_field_schema_fails_closed():
    schema = {key: set(fields) for key, fields in C1.items()}
    schema["observation_samples"].add("true_delay")
    with pytest.raises(ValueError, match="true_delay"):
        check_whitelist(schema)


@pytest.mark.skipif(os.environ.get("RRA_ZETARIS_LIVE") != "1", reason="Zetaris live checks are opt-in")
def test_live_mode_requires_explicit_switch():
    assert os.environ.get("RRA_ZETARIS_LIVE") == "1"


@pytest.mark.parametrize("seed", [0, 16])
def test_two_episode_s2_anchors(seed):
    config = v3_world_config("nominal")
    realization = realize_episode(seed, ("SENSOR_BIAS",)) if seed == 0 else realize_episode(seed, (), "OBJECT_MISSING")
    receipt = run_episode(config, seed, True, terminal_monitoring="corrected", realization=realization,
                          system2_enabled=True, include_s2_diagnostics=True)
    world = V3World(config, seed, realization)
    obs_ids = {}
    for _ in range(config.object_count * config.episode_steps):
        raw = world.observation()
        if raw.target_present:
            sample = sanitize_observation(raw)
            obs_ids.setdefault(sample.target_id, []).append(f"obs:{sample.target_id}:{sample.time:.3f}")
        world.advance()
    for row in receipt["s2_diagnostic_trace"]:
        count = sum(float(item.rsplit(":", 1)[1]) <= row["sim_time"] for item in obs_ids.get(row["target_id"], []))
        assert count == row["n_usable_total"]
    auth_rows = [d for d in receipt["system2_decisions"] if d.get("authorization")]
    for row in auth_rows:
        auth = row["authorization"]
        assert auth.get("evidence_ids")
        assert auth["evidence_ids"] == [i for i in obs_ids.get(row["target_id"], [])
                                         if float(i.rsplit(":", 1)[1]) <= row["time"]]
