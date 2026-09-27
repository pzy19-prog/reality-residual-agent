"""Deterministic command validation and pick-window execution."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ControllerConfig:
    min_speed: float = 0.50
    max_speed: float = 1.50
    min_pick_position: float = -0.75
    max_pick_position: float = 0.75
    tolerance: float = 0.20


@dataclass(frozen=True)
class Command:
    target_id: int
    speed: float
    pick_position: float
    expected_time: float


@dataclass(frozen=True)
class Execution:
    accepted: bool
    success: bool
    position_error: float
    reason: str


@dataclass
class Controller:
    config: ControllerConfig = field(default_factory=ControllerConfig)
    rejections: list[str] = field(default_factory=list)

    def execute(self, command: Command, actual_x: float, actual_time: float) -> Execution:
        """Reject out-of-bounds commands; otherwise evaluate the physical pick window."""
        if not self.config.min_speed <= command.speed <= self.config.max_speed:
            reason = f"rejected speed {command.speed:.6f} outside controller limits"
            self.rejections.append(reason)
            return Execution(False, False, abs(actual_x - command.pick_position), reason)
        if not self.config.min_pick_position <= command.pick_position <= self.config.max_pick_position:
            reason = f"rejected pick position {command.pick_position:.6f} outside controller limits"
            self.rejections.append(reason)
            return Execution(False, False, abs(actual_x - command.pick_position), reason)
        error = abs(actual_x - command.pick_position)
        time_error = abs(actual_time - command.expected_time) * command.speed
        ok = max(error, time_error) <= self.config.tolerance
        return Execution(True, ok, max(error, time_error), "picked" if ok else "missed pick window")
