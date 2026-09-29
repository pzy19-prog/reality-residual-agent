"""Evaluator-side PAUSE_THEN_RECOVER release semantics."""

from dataclasses import dataclass

PAUSE_CLEAR_SAMPLES = 6


@dataclass
class PauseClearTracker:
    """Clear after six consecutive clean observations following event end."""

    clean_count: int = 0
    cleared: bool = False

    def observe(self, *, clean: bool, event_ended: bool) -> bool:
        if self.cleared:
            return True
        if not event_ended or not clean:
            self.clean_count = 0
            return False
        self.clean_count += 1
        if self.clean_count == PAUSE_CLEAR_SAMPLES:
            self.cleared = True
        return self.cleared
