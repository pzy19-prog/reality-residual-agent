"""Noiseless oracle for S2 execution-position prediction against the v3 plant."""
import pytest

from rra.eval.scenarios import EpisodeRealization
from rra.s2.prediction import pick_error_at_command_time
from rra.s2.verifier import Verification
from rra.sim import WorldConfig
from rra.sim.v3_world import V3World


CASES = [
    (("SENSOR_BIAS",), {"sensor_bias": 0.23}),
    (("VELOCITY_OFFSET",), {"velocity_offset": 0.12}),
    (("SPEED_STEP",), {"speed_step_time": 0.70, "speed_step_delta": 0.16}),
    (("ACTUATOR_DELAY",), {"actuator_delay": 0.20}),
    (("SENSOR_BIAS", "SPEED_STEP"),
     {"sensor_bias": 0.23, "speed_step_time": 0.70, "speed_step_delta": 0.16}),
    (("SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP"),
     {"sensor_bias": 0.23, "velocity_offset": 0.12,
      "speed_step_time": 0.70, "speed_step_delta": 0.16}),
    (("VELOCITY_OFFSET", "ACTUATOR_DELAY"),
     {"velocity_offset": 0.12, "actuator_delay": 0.20}),
]


def _observation_at(config, realization, step):
    world = V3World(config, 2718, realization)
    for _ in range(step):
        world.advance()
    return world.observation()


@pytest.mark.parametrize("structure,parameters", CASES)
def test_true_parameters_predict_v3_execution_position(structure, parameters):
    dt = 0.05
    config = WorldConfig(
        scenario="nominal", belt_speed=1.0, object_count=1,
        initial_position_min=-3.0, initial_position_max=-3.0,
        observation_noise_sigma=0.0, dt=dt, episode_steps=90,
    )
    realization = EpisodeRealization(tuple(structure), dict(parameters), None, {})
    decision = _observation_at(config, realization, 8)  # local time 0.40 s
    command_time = 1.0
    execution_time = command_time + parameters.get("actuator_delay", 0.0)
    actual = _observation_at(config, realization, round(execution_time / dt)).actual_x
    hypothesis = Verification(
        "oracle", tuple(structure), dict(parameters), 6, 0.0, (), (), True, (),
    )

    error = pick_error_at_command_time(
        hypothesis, command_time, observation=decision,
        nominal_speed=config.belt_speed, x_pick=actual,
    )

    assert error <= 1e-6, {
        "structure": structure, "parameters": parameters,
        "decision_time": decision.time, "command_time": command_time,
        "execution_time": execution_time, "actual_x": actual, "oracle_error": error,
    }
