"""Shared policy-side prediction helpers for verifier and action machinery."""
from __future__ import annotations

from rra.s2.verifier import Verification


def pick_error_at_command_time(
    hypothesis: Verification,
    command_time: float,
    *,
    observation,
    nominal_speed: float,
    x_pick: float,
) -> float:
    """Predict physical pick error using the fitted DSL at a command time."""
    params = hypothesis.fitted_parameters
    now = observation.time
    if command_time < now + params.get("actuator_delay", 0.0):
        return float("inf")
    elapsed = command_time - now
    tau = params.get("speed_step_time")
    current_residual = params.get("velocity_offset", 0.0) * now
    execution_residual = params.get("velocity_offset", 0.0) * command_time
    if tau is not None:
        delta = params.get("speed_step_delta", 0.0)
        current_residual += delta * max(0.0, now - tau)
        execution_residual += delta * max(0.0, command_time - tau)
    physical_x = (
        observation.nominal_x
        + current_residual
        - params.get("sensor_bias", 0.0)
        + nominal_speed * elapsed
        + execution_residual - current_residual
    )
    return abs(physical_x - x_pick)
