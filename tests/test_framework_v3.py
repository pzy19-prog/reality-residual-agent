from rra.eval.framework import v3_world_config
from rra.sim import World, WorldConfig


def test_v3_noise_is_keyed_per_sample_and_world_draws_are_unchanged():
    plain = World(WorldConfig(scenario="nominal"), seed=41).observation()
    noisy = World(WorldConfig(scenario="nominal", observation_noise_sigma=0.0), seed=41).observation()
    assert plain.actual_x == noisy.actual_x
    assert plain.observed_x == noisy.observed_x

    sigma_a = WorldConfig(scenario="nominal", observation_noise_sigma=0.015)
    sigma_b = WorldConfig(scenario="nominal", observation_noise_sigma=0.030)
    a = World(sigma_a, seed=41).observation()
    b = World(sigma_b, seed=41).observation()
    assert a.actual_x == b.actual_x
    assert abs((a.observed_x - a.actual_x) * 2 - (b.observed_x - b.actual_x)) < 1e-12


def test_v3_framework_constants_are_applied():
    config = v3_world_config("nominal")
    assert (config.dt, config.episode_steps, config.observation_noise_sigma) == (0.1, 100, 0.015)
