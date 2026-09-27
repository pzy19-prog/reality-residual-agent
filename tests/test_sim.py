import pytest

from rra.sim import World, WorldConfig


def test_world_is_seeded_and_bias_is_sensor_only():
    config = WorldConfig(scenario="bias")
    a, b = World(config, 17).observation(), World(config, 17).observation()
    assert a == b
    assert a.observed_x - a.actual_x == pytest.approx(config.position_bias)


def test_world_moves_target_and_applies_load_after_step():
    config = WorldConfig(scenario="load")
    world = World(config, 2)
    world.step_index = config.load_step - 1
    before = world.observation()
    world.step_index += 1
    after = world.observation()
    assert after.actual_speed > before.actual_speed
    assert after.actual_x > before.actual_x
