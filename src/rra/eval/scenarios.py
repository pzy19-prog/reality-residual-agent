"""Deterministic preregistered v3 recoverable and invalidating realizations."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np

PRIMITIVES = ("SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP", "ACTUATOR_DELAY")
FAULT_FAMILIES = (
    "SENSOR_STUCK", "SENSOR_SPIKE_BURST", "OBJECT_MISSING", "SECOND_DYNAMICS_CHANGE", "BELT_STOP"
)


@dataclass(frozen=True)
class EpisodeRealization:
    structure: tuple[str, ...]
    recoverable: dict[str, Any]
    fault_family: str | None
    fault: dict[str, Any]


def composition_structures() -> tuple[tuple[str, ...], ...]:
    return tuple((p,) for p in PRIMITIVES) + tuple(combinations(PRIMITIVES, 2)) + tuple(combinations(PRIMITIVES, 3))


def _signed(rng: np.random.Generator, low: float, high: float) -> float:
    return float(rng.choice((-1.0, 1.0)) * rng.uniform(low, high))


def realize_episode(seed: int, structure: tuple[str, ...] = (), fault_family: str | None = None) -> EpisodeRealization:
    """Sample generator truth from isolated deterministic streams."""
    if len(set(structure)) != len(structure) or any(p not in PRIMITIVES for p in structure):
        raise ValueError("structure must contain unique registered primitives")
    if fault_family is not None and fault_family not in FAULT_FAMILIES:
        raise ValueError(f"unknown fault family: {fault_family}")
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), 0x563352]))
    recoverable: dict[str, Any] = {}
    if "SENSOR_BIAS" in structure:
        recoverable["sensor_bias"] = _signed(rng, 0.10, 0.45)
    if "VELOCITY_OFFSET" in structure:
        recoverable["velocity_offset"] = _signed(rng, 0.02, 0.20)
    if "SPEED_STEP" in structure:
        recoverable["speed_step_time"] = float(rng.uniform(1.0, 4.0))
        recoverable["speed_step_delta"] = _signed(rng, 0.08, 0.30)
    if "ACTUATOR_DELAY" in structure:
        recoverable["actuator_delay"] = float(rng.uniform(0.05, 0.40))
    fault: dict[str, Any] = {}
    if fault_family is not None:
        frng = np.random.default_rng(np.random.SeedSequence([int(seed), 0x563346]))
        if fault_family in ("SENSOR_STUCK", "SENSOR_SPIKE_BURST", "OBJECT_MISSING", "BELT_STOP"):
            fault["trigger_target"] = int(frng.integers(2, 10))
            fault["trigger_time"] = float(frng.uniform(1.0, 4.0))
        if fault_family == "SENSOR_SPIKE_BURST":
            fault["duration_samples"] = int(frng.integers(1, 4))
            fault["magnitude"] = _signed(frng, 0.40, 1.20)
        elif fault_family == "SECOND_DYNAMICS_CHANGE":
            fault["first_time"] = float(frng.uniform(1.0, 2.0))
            fault["second_time"] = fault["first_time"] + float(frng.uniform(1.0, 2.0))
            fault["first_delta"] = _signed(frng, 0.08, 0.25)
            fault["second_delta"] = _signed(frng, 0.08, 0.25)
        return EpisodeRealization(tuple(structure), recoverable, fault_family, fault)
    return EpisodeRealization(tuple(structure), recoverable, fault_family, fault)


def v0_combo_realization(seed: int) -> EpisodeRealization:
    """Map frozen V0 combo to its preregistered three-primitive structure."""
    return realize_episode(seed, ("SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP"))
