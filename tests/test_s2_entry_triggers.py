from rra.evidence import episode as episode_module
from rra.s2.dsl import Action
from rra.sim import WorldConfig


def _pause_result():
    return {
        "action": Action.PAUSE_AND_REOBSERVE,
        "action_time": None,
        "faults": (),
        "passing": [],
        "fits": [],
        "verifications": [],
        "gate_reason": "NONE",
    }


def test_correction_infeasible_triggers_s2_before_command_window(monkeypatch):
    calls = []
    monkeypatch.setattr(episode_module, "run_b3", lambda *args, **kwargs: (calls.append(kwargs) or _pause_result()))
    config = WorldConfig(
        scenario="moving", moving_speed_delta=0.10, object_count=1,
        initial_position_min=-7.934, initial_position_max=-7.934,
    )

    receipt = episode_module.run_episode(config, 0, True, system2_enabled=True)

    assert any(row["infeasible"] for row in receipt["compensation_records"])
    assert calls
    command_window_start = (config.x_pick - config.initial_position_min) / config.belt_speed - config.dt / 2
    assert calls[0]["current_time"] < command_window_start
    assert receipt["outcomes"][0]["reason"] == "correction_infeasible"


def test_system2_disabled_receipt_matches_default_byte_for_byte():
    config = WorldConfig(
        scenario="nominal", object_count=1, initial_position_min=-0.15,
        initial_position_max=-0.15, episode_steps=90,
    )
    implicit = episode_module.run_episode(config, 7, True)
    disabled = episode_module.run_episode(config, 7, True, system2_enabled=False)

    assert implicit == disabled
