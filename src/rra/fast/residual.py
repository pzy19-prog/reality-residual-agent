"""Bounded residual monitoring and EWMA correction."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import fmean
from typing import TYPE_CHECKING, Literal

from rra.planner.scripted import Plan

if TYPE_CHECKING:
    from rra.sim.world import Observation

Disturbance = Literal["position_bias", "drift", "moving_target", "load_change", "none", "unknown"]
MAX_TIME_CORRECTION = 0.50


class ResidualMonitor:
    """Track a fixed-size residual window and classify simple disturbance signatures."""

    def __init__(self, window_size: int = 12):
        if window_size < 3:
            raise ValueError("window_size must be at least 3")
        self.window_size = window_size
        self._samples: deque[tuple[int, float, float]] = deque(maxlen=window_size)

    def update(self, observation: Observation) -> float:
        residual = observation.observed_x - observation.nominal_x
        self._samples.append((observation.step, observation.time, residual))
        return residual

    def classify(self) -> Disturbance:
        rows = list(self._samples)
        if len(rows) < 3:
            return "unknown"
        residuals = [row[2] for row in rows]
        deltas = [residuals[i] - residuals[i - 1] for i in range(1, len(residuals))]
        if max(deltas) - min(deltas) >= 0.008 and abs(fmean(deltas)) >= 0.004:
            return "load_change"
        slope = (residuals[-1] - residuals[0]) / max(rows[-1][1] - rows[0][1], 1e-9)
        if abs(slope) >= 0.075:
            return "moving_target"
        if abs(slope) >= 0.012:
            return "drift"
        if abs(fmean(residuals)) >= 0.05:
            return "position_bias"
        return "none"

    @property
    def mean(self) -> float:
        return fmean(row[2] for row in self._samples) if self._samples else 0.0

    @property
    def max_abs(self) -> float:
        return max((abs(row[2]) for row in self._samples), default=0.0)


@dataclass(frozen=True)
class Correction:
    plan: Plan
    residual: float
    disturbance: Disturbance
    position_delta: float
    time_delta: float
    saturated: bool
    reason: str


class Corrector:
    """Separate fixed sensor offset from motion lead and bound time corrections."""

    def __init__(
        self,
        alpha: float = 0.25,
        max_position_correction: float = 0.50,
        max_time_correction: float = MAX_TIME_CORRECTION,
        safe_residual_threshold: float = 1.25,
    ):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")
        if min(max_position_correction, max_time_correction, safe_residual_threshold) <= 0:
            raise ValueError("correction limits and safety threshold must be positive")
        self.alpha = alpha
        self.max_position_correction = max_position_correction
        self.max_time_correction = max_time_correction
        self.safe_residual_threshold = safe_residual_threshold
        self.estimate = 0.0
        self._sensor_offset: float | None = None
        self._last_residual: float | None = None
        self._last_time: float | None = None

    def correct(
        self,
        plan: Plan,
        residual: float,
        disturbance: Disturbance,
        nominal_speed: float,
    ) -> Correction:
        if nominal_speed <= 0:
            raise ValueError("nominal_speed must be positive")
        if abs(residual) > self.safe_residual_threshold:
            return Correction(
                plan=plan,
                residual=residual,
                disturbance=disturbance,
                position_delta=0.0,
                time_delta=0.0,
                saturated=False,
                reason="ESCALATE: residual exceeded fixed safety threshold",
            )
        self.estimate = self.alpha * residual + (1 - self.alpha) * self.estimate
        if self._sensor_offset is None:
            self._sensor_offset = residual
        sensor_offset = self._sensor_offset
        kinematic_lead = residual - sensor_offset
        now = plan.observation_time
        slope = 0.0
        if self._last_residual is not None and self._last_time is not None and now > self._last_time:
            slope = (residual - self._last_residual) / (now - self._last_time)
        self._last_residual, self._last_time = residual, now
        # The conveyor gripper is mechanically fixed at x_pick, so V0 limits
        # spatial correction to zero and compensates in time.
        position_delta = 0.0
        if disturbance in ("moving_target", "drift", "load_change"):
            time_to_arrival = max(0.0, plan.expected_arrival_time - now)
            predicted_lead = kinematic_lead + slope * time_to_arrival
        else:
            predicted_lead = kinematic_lead
        motion_speed = nominal_speed + slope
        if disturbance in ("moving_target", "drift", "load_change") and motion_speed <= 0:
            return Correction(
                plan=plan,
                residual=residual,
                disturbance=disturbance,
                position_delta=0.0,
                time_delta=0.0,
                saturated=False,
                reason="ESCALATE: predicted motion speed is non-positive",
            )
        # Sensor offset is measured against nominal geometry; only physical
        # motion lead is converted using the residual-adjusted speed estimate.
        uncapped_time_delta = sensor_offset / nominal_speed - predicted_lead / (
            motion_speed if disturbance in ("moving_target", "drift", "load_change") else nominal_speed
        )
        saturated = abs(uncapped_time_delta) > self.max_time_correction
        time_delta = max(
            -self.max_time_correction,
            min(self.max_time_correction, uncapped_time_delta),
        )
        corrected = Plan(
            target_id=plan.target_id,
            expected_arrival_time=plan.expected_arrival_time + time_delta,
            pick_position=plan.pick_position + position_delta,
        )
        return Correction(
            plan=corrected,
            residual=residual,
            disturbance=disturbance,
            position_delta=position_delta,
            time_delta=time_delta,
            saturated=saturated,
            reason=(
                f"sensor offset {sensor_offset:.6f}; predicted motion lead "
                f"{predicted_lead:.6f}; clamped={saturated}"
            ),
        )
