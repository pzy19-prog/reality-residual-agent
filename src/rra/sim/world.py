"""Seeded conveyor world and configurable reality perturbations."""

from __future__ import annotations

from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class WorldConfig(BaseModel):
    """Frozen simulation inputs. Positions are in arbitrary world units, time in s."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenario: Literal["bias", "drift", "moving", "load", "combo"] = "bias"
    belt_speed: float = Field(default=1.0, gt=0)
    x_pick: float = 0.0
    tolerance: float = Field(default=0.20, gt=0)
    dt: float = Field(default=0.10, gt=0)
    episode_steps: int = Field(default=80, ge=8)
    object_count: int = Field(default=12, ge=1)
    position_bias: float = 0.45
    drift_per_second: float = 0.045
    moving_speed_delta: float = 0.10
    load_step: int = 35
    load_speed_delta: float = 0.16
    load_response_delay: float = 0.22
    initial_position_min: float = -8.0
    initial_position_max: float = -4.0


class Observation(BaseModel):
    """One sensor sample for the current target."""

    model_config = ConfigDict(frozen=True)

    step: int
    time: float
    target_id: int
    observed_x: float
    nominal_x: float
    actual_x: float
    nominal_speed: float
    actual_speed: float


class World:
    """A deterministic conveyor world. All object placement comes from ``seed``."""

    def __init__(self, config: WorldConfig, seed: int):
        self.config = config
        self.seed = int(seed)
        rng = np.random.default_rng(self.seed)
        self._starts = rng.uniform(
            config.initial_position_min,
            config.initial_position_max,
            size=config.object_count,
        ).tolist()
        self.step_index = 0
        self.target_index = 0

    def observation(self) -> Observation:
        """Return the current sample without advancing simulation time."""
        c = self.config
        target = self.target_index % len(self._starts)
        start_x = self._starts[target]
        t = self.step_index * c.dt
        moving_delta = c.moving_speed_delta if c.scenario in ("moving", "combo") else 0.0
        load_delta = c.load_speed_delta if c.scenario in ("load", "combo") else 0.0
        loaded_steps = max(0, self.step_index - c.load_step)
        actual_x = start_x + (c.belt_speed + moving_delta) * t + load_delta * loaded_steps * c.dt
        speed = c.belt_speed + moving_delta + (load_delta if self.step_index >= c.load_step else 0.0)
        nominal_x = start_x + c.belt_speed * t
        bias = 0.0
        if c.scenario in ("bias", "combo"):
            bias += c.position_bias
        if c.scenario in ("drift", "combo"):
            bias += c.drift_per_second * t
        observed_x = actual_x + bias
        return Observation(
            step=self.step_index,
            time=t,
            target_id=target,
            observed_x=observed_x,
            nominal_x=nominal_x,
            actual_x=actual_x,
            nominal_speed=c.belt_speed,
            actual_speed=speed,
        )

    def advance(self) -> None:
        """Advance one fixed time step, then move to the next target after a pick window."""
        self.step_index += 1
        if self.step_index >= self.config.episode_steps:
            self.step_index = 0
            self.target_index += 1
