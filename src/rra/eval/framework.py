"""Shared v3 diagnostic framework settings."""

from __future__ import annotations

from typing import Any

from rra.sim import WorldConfig

V3_DT = 0.1
V3_EPISODE_STEPS = 100
V3_X_NOISE_SIGMA = 0.015


def v3_world_config(scenario: str, **parameters: Any) -> WorldConfig:
    """Build an episode config under the common preregistered v3 frame."""
    return WorldConfig(
        scenario=scenario,
        dt=V3_DT,
        episode_steps=V3_EPISODE_STEPS,
        observation_noise_sigma=V3_X_NOISE_SIGMA,
        **parameters,
    )
