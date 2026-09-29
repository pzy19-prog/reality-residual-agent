"""Plant and sensor realization for the preregistered v3 evaluation world."""

from __future__ import annotations

from math import ceil

import numpy as np

from rra.eval.scenarios import EpisodeRealization
from rra.sim.world import Observation, World, WorldConfig


class V3World:
    """World-compatible simulator with recoverable and invalidating events."""

    def __init__(self, config: WorldConfig, seed: int, realization: EpisodeRealization):
        self.config = config
        self.seed = int(seed)
        self.realization = realization
        base = World(config.model_copy(update={"scenario": "nominal", "position_bias": 0.0}), seed)
        self._starts = base._starts
        self._y_starts = base._y_starts
        self.step_index = 0
        self.target_index = 0
        self._stuck_value: dict[int, float] = {}

    def _sample_noise(self, target: int, step: int) -> float:
        rng = np.random.default_rng(np.random.SeedSequence([self.seed, 0x525241, target, step]))
        return float(rng.normal(0.0, self.config.observation_noise_sigma))

    def _fault_active(self, target: int, t: float) -> bool:
        f = self.realization.fault
        return target >= f.get("trigger_target", 10**9) and t >= f.get("trigger_time", float("inf"))

    def _speed_delta(self, t: float) -> float:
        r = self.realization.recoverable
        delta = r.get("velocity_offset", 0.0)
        if t >= r.get("speed_step_time", float("inf")):
            delta += r.get("speed_step_delta", 0.0)
        if self.realization.fault_family == "SECOND_DYNAMICS_CHANGE":
            f = self.realization.fault
            if t >= f["first_time"]:
                delta += f["first_delta"]
            if t >= f["second_time"]:
                delta += f["second_delta"]
        return float(delta)

    def _position(self, target: int, t: float) -> tuple[float, float]:
        c, r = self.config, self.realization.recoverable
        f = self.realization.fault
        points = {0.0, t}
        for key in ("speed_step_time",):
            if 0 < r.get(key, float("inf")) < t:
                points.add(r[key])
        if self.realization.fault_family == "SECOND_DYNAMICS_CHANGE":
            points.update(x for x in (f["first_time"], f["second_time"]) if 0 < x < t)
        elif self.realization.fault_family == "BELT_STOP" and target >= f.get("trigger_target", 10**9):
            stop_time = f.get("trigger_time", float("inf"))
            if 0 < stop_time < t:
                points.add(stop_time)
        ordered = sorted(points)
        travel = 0.0
        stopped = False
        for left, right in zip(ordered, ordered[1:]):
            midpoint = (left + right) / 2
            if self.realization.fault_family == "BELT_STOP" and self._fault_active(target, midpoint):
                stopped = True
            if not stopped:
                travel += (right - left) * (c.belt_speed + self._speed_delta(midpoint))
        return self._starts[target] + travel, self._y_starts[target]

    def observation(self) -> Observation:
        c, r, f = self.config, self.realization.recoverable, self.realization.fault
        target = self.target_index % len(self._starts)
        t = self.step_index * c.dt
        actual_x, y = self._position(target, t)
        actual_speed = c.belt_speed + self._speed_delta(t)
        if self.realization.fault_family == "BELT_STOP" and self._fault_active(target, t):
            actual_speed = 0.0
        nominal_x = self._starts[target] + c.belt_speed * t
        observed_x = actual_x + r.get("sensor_bias", 0.0) + self._sample_noise(target, self.step_index)
        active_fault = self._fault_active(target, t)
        present = not (self.realization.fault_family == "OBJECT_MISSING" and active_fault)
        if self.realization.fault_family == "SENSOR_SPIKE_BURST" and active_fault:
            since = self.step_index - ceil(f["trigger_time"] / c.dt)
            if 0 <= since < f["duration_samples"]:
                observed_x += f["magnitude"]
        if self.realization.fault_family == "SENSOR_STUCK" and active_fault:
            if target not in self._stuck_value:
                self._stuck_value[target] = observed_x
            observed_x = self._stuck_value[target]
        response_delay = r.get("actuator_delay", 0.0)
        return Observation(
            step=self.step_index,
            time=t,
            target_id=target,
            observed_x=observed_x,
            nominal_x=nominal_x,
            actual_x=actual_x,
            nominal_speed=c.belt_speed,
            actual_speed=actual_speed,
            observed_y=y,
            nominal_y=y,
            actual_y=y,
            target_present=present,
            response_delay=response_delay,
        )

    def advance(self) -> None:
        self.step_index += 1
        if self.step_index >= self.config.episode_steps:
            self.step_index = 0
            self.target_index += 1
