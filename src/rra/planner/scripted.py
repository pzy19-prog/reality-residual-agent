"""Nominal-model scripted pick planner."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from rra.sim.world import Observation


class Plan(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_id: int
    expected_arrival_time: float
    pick_position: float
    pick_position_y: float = 0.0
    observation_time: float = 0.0


class ScriptedPlanner:
    """Predict a target's arrival using only the nominal belt model."""

    def plan(self, observation: Observation, nominal_speed: float, x_pick: float) -> Plan:
        if nominal_speed <= 0:
            raise ValueError("nominal_speed must be positive")
        eta = observation.time + (x_pick - observation.observed_x) / nominal_speed
        return Plan(
            target_id=observation.target_id,
            expected_arrival_time=eta,
            pick_position=x_pick,
            observation_time=observation.time,
        )
