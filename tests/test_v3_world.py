from rra.eval.pause import PAUSE_CLEAR_SAMPLES, PauseClearTracker
from rra.eval.scenarios import (
    EpisodeRealization,
    composition_structures,
    realize_episode,
)
from rra.eval.framework import v3_world_config
from rra.sim.v3_world import V3World


def test_registered_composition_world_has_fourteen_unique_structures():
    structures = composition_structures()
    assert len(structures) == 14
    assert all(len(set(s)) == len(s) for s in structures)
    assert [len(s) for s in structures] == [1] * 4 + [2] * 6 + [3] * 4


def test_recoverable_and_fault_realizations_are_seed_deterministic_and_bounded():
    for primitive, limits in {
        "SENSOR_BIAS": (0.10, 0.45),
        "VELOCITY_OFFSET": (0.02, 0.20),
        "SPEED_STEP": (0.08, 0.30),
    }.items():
        first = realize_episode(17, (primitive,))
        assert first == realize_episode(17, (primitive,))
        key = {"SENSOR_BIAS": "sensor_bias", "VELOCITY_OFFSET": "velocity_offset",
               "SPEED_STEP": "speed_step_delta"}[primitive]
        assert limits[0] <= abs(first.recoverable[key]) <= limits[1]
    delay = realize_episode(17, ("ACTUATOR_DELAY",)).recoverable["actuator_delay"]
    assert 0.05 <= delay <= 0.40
    for family in ("SENSOR_STUCK", "SENSOR_SPIKE_BURST", "OBJECT_MISSING", "BELT_STOP"):
        fault = realize_episode(20, fault_family=family).fault
        assert 2 <= fault["trigger_target"] <= 9
        assert 1.0 <= fault["trigger_time"] <= 4.0


def test_sensor_stuck_freezes_noisy_observation_and_missing_hides_target():
    config = v3_world_config("nominal")
    stuck = EpisodeRealization((), {}, "SENSOR_STUCK", {"trigger_target": 2, "trigger_time": 1.0})
    world = V3World(config, 8, stuck)
    world.target_index = 2
    world.step_index = 10
    first = world.observation()
    world.advance()
    second = world.observation()
    assert first.observed_x == second.observed_x

    missing = EpisodeRealization((), {}, "OBJECT_MISSING", {"trigger_target": 2, "trigger_time": 1.0})
    absent = V3World(config, 8, missing)
    absent.target_index = 2
    absent.step_index = 10
    assert absent.observation().target_present is False


def test_remaining_fault_world_primitives_have_registered_effects():
    config = v3_world_config("nominal")
    spike = EpisodeRealization((), {}, "SENSOR_SPIKE_BURST", {
        "trigger_target": 0, "trigger_time": 1.0, "duration_samples": 2, "magnitude": 0.5,
    })
    world = V3World(config, 9, spike)
    baseline = V3World(config, 9, EpisodeRealization((), {}, None, {}))
    world.step_index = 9
    baseline.step_index = 9
    world.advance()
    first_row = world.observation()
    baseline.advance()
    first_clean = baseline.observation()
    world.advance()
    second_row = world.observation()
    baseline.advance()
    second_clean = baseline.observation()
    assert abs(first_row.observed_x - first_clean.observed_x - 0.5) < 1e-12
    assert abs(second_row.observed_x - second_clean.observed_x - 0.5) < 1e-12

    dynamics = EpisodeRealization((), {}, "SECOND_DYNAMICS_CHANGE", {
        "first_time": 1.0, "second_time": 2.0, "first_delta": 0.1, "second_delta": -0.2,
    })
    changed = V3World(config, 9, dynamics)
    changed.step_index = 15
    assert abs(changed.observation().actual_speed - 1.1) < 1e-12
    changed.step_index = 25
    assert abs(changed.observation().actual_speed - 0.9) < 1e-12

    stop = EpisodeRealization((), {}, "BELT_STOP", {"trigger_target": 0, "trigger_time": 1.05})
    stopped = V3World(config, 9, stop)
    stopped.step_index = 11
    assert stopped.observation().actual_speed == 0.0

    delayed = realize_episode(11, ("ACTUATOR_DELAY",))
    assert 0.05 <= V3World(config, 11, delayed).observation().response_delay <= 0.40


def test_pause_clears_after_sixth_consecutive_clean_sample():
    tracker = PauseClearTracker()
    assert not tracker.observe(clean=True, event_ended=False)
    for _ in range(2):
        assert not tracker.observe(clean=True, event_ended=True)
    assert not tracker.observe(clean=False, event_ended=True)
    for index in range(PAUSE_CLEAR_SAMPLES - 1):
        assert not tracker.observe(clean=True, event_ended=True)
    assert tracker.observe(clean=True, event_ended=True)
    assert tracker.observe(clean=False, event_ended=True)
