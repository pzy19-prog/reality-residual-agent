"""Explicit whitelist boundary for structured policy-visible data."""

from __future__ import annotations

from dataclasses import dataclass

from rra.sim.world import Observation, WorldConfig


@dataclass(frozen=True, slots=True)
class PolicyObservationSample:
    target_id: int
    step: int
    time: float
    observed_x: float
    observed_y: float
    nominal_x: float
    nominal_y: float
    nominal_speed: float


@dataclass(frozen=True, slots=True)
class PolicyKnownConfig:
    dt: float
    tolerance: float
    x_pick: float
    y_pick: float
    belt_speed: float


@dataclass(frozen=True, slots=True)
class PolicyCommandFeedback:
    command_id: str
    target_id: int
    issued_time: float
    execution_time: float
    accepted: bool
    success: bool
    reason_code: str


def sanitize_observation(observation: Observation) -> PolicyObservationSample:
    """Copy exactly the registered policy-visible observation whitelist."""
    if not isinstance(observation, Observation):
        raise TypeError("sanitizer accepts only a simulator Observation")
    return PolicyObservationSample(
        target_id=observation.target_id,
        step=observation.step,
        time=observation.time,
        observed_x=observation.observed_x,
        observed_y=observation.observed_y,
        nominal_x=observation.nominal_x,
        nominal_y=observation.nominal_y,
        nominal_speed=observation.nominal_speed,
    )


def sanitize_config(config: WorldConfig) -> PolicyKnownConfig:
    """Copy only registered known configuration into policy-visible form."""
    return PolicyKnownConfig(
        dt=config.dt,
        tolerance=config.tolerance,
        x_pick=config.x_pick,
        y_pick=config.y_pick,
        belt_speed=config.belt_speed,
    )


def command_feedback(
    *, command_id: str, target_id: int, issued_time: float, execution_time: float,
    accepted: bool, success: bool,
) -> PolicyCommandFeedback:
    """Expose registered controller telemetry; never expose simulator delay."""
    reason_code = "picked" if accepted and success else "missed" if accepted else "rejected"
    return PolicyCommandFeedback(
        command_id=command_id,
        target_id=target_id,
        issued_time=issued_time,
        execution_time=execution_time,
        accepted=accepted,
        success=success,
        reason_code=reason_code,
    )
