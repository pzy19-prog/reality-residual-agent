from rra.eval.framework import v3_world_config
from rra.sim import World, WorldConfig
from rra.evidence import episode as episode_module
from rra.fast import Corrector as BaseCorrector, ResidualMonitor as BaseMonitor


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


def test_terminal_monitoring_legacy_and_corrected_update_counts(monkeypatch):
    updates = {"monitor": [], "corrector": []}

    class Monitor(BaseMonitor):
        def update(self, observation):
            updates["monitor"].append(observation.target_id)
            return super().update(observation)

    class Corrector(BaseCorrector):
        def correct(self, *args, **kwargs):
            updates["corrector"].append(args[0].target_id)
            return super().correct(*args, **kwargs)

    monkeypatch.setattr(episode_module, "ResidualMonitor", Monitor)
    monkeypatch.setattr(episode_module, "Corrector", Corrector)
    config = WorldConfig(
        scenario="nominal", episode_steps=100, object_count=1,
        initial_position_min=-5.0, initial_position_max=-5.0,
    )
    episode_module.run_episode(config, 1, True, terminal_monitoring="legacy")
    assert len(updates["monitor"]) == 100
    assert len(updates["corrector"]) == 100
    updates["monitor"].clear()
    updates["corrector"].clear()
    episode_module.run_episode(config, 1, True, terminal_monitoring="corrected")
    assert 0 < len(updates["monitor"]) < 100
    assert len(updates["corrector"]) == len(updates["monitor"])
