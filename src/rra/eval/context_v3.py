"""Deterministic, preregistered v3 operational text contexts."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Literal, Sequence

from rra.eval.text_context import validate_text_context

TextVariant = Literal[
    "NO_TEXT_CONTEXT", "HELPFUL_TEXT_CONTEXT", "IRRELEVANT_TEXT_CONTEXT", "MISLEADING_TEXT_CONTEXT"
]
VARIANTS: tuple[TextVariant, ...] = (
    "NO_TEXT_CONTEXT", "HELPFUL_TEXT_CONTEXT", "IRRELEVANT_TEXT_CONTEXT", "MISLEADING_TEXT_CONTEXT"
)
TEMPLATE_FAMILIES = (
    "TXT-MOTOR-SERVICE", "TXT-SENSOR-CAL", "TXT-ACTUATOR-SLOW",
    "TXT-PACKAGE-SLIP", "TXT-FLOW-MISSING", "TXT-UNRELATED",
)
# The 14 preregistered structures, represented with canonical primitive order.
PRIMITIVES = ("SENSOR_BIAS", "VELOCITY_OFFSET", "SPEED_STEP", "ACTUATOR_DELAY")
from itertools import combinations

STRUCTURE_IDS = tuple(
    combo[0] if size == 1 else "AND(" + ",".join(combo) + ")"
    for size in (1, 2, 3)
    for combo in combinations(PRIMITIVES, size)
)
FAULT_HYPOTHESIS_IDS = (
    "SENSOR_STUCK", "SENSOR_SPIKE_OR_UNRELIABLE", "OBJECT_MISSING_OR_DROPPED",
    "BELT_STOP_OR_MOTION_LOSS", "POST_VERIFICATION_CHANGE", "UNKNOWN_OR_INSUFFICIENT_EVIDENCE",
)

_WORDING: dict[str, tuple[str, ...]] = {
    "TXT-MOTOR-SERVICE": (
        "The drive motor was serviced recently; belt-speed recalibration may still be pending.",
        "A recent drive-motor service may have left belt-speed calibration unfinished.",
        "The maintenance log notes drive-motor work, and belt-speed recalibration may be due.",
    ),
    "TXT-SENSOR-CAL": (
        "The position sensor was calibrated recently, though its stability should be checked.",
        "A recent vision-sensor calibration was recorded; sensor stability remains worth checking.",
        "Operators noted recent position-sensor calibration and asked that its readings be monitored.",
    ),
    "TXT-ACTUATOR-SLOW": (
        "The gripper response has recently been reported as sluggish.",
        "Operators reported slower-than-usual gripper response during recent shifts.",
        "A maintenance note says the actuator may be responding more slowly than usual.",
    ),
    "TXT-PACKAGE-SLIP": (
        "Operators have observed intermittent package slip or irregular package motion.",
        "Recent shift notes mention occasional package slipping and uneven motion.",
        "The line log records intermittent package-motion irregularities.",
    ),
    "TXT-FLOW-MISSING": (
        "An operator reported a package missing from the expected material flow.",
        "The shift note mentions a possibly dropped package in the line.",
        "Recent operations notes report an interruption in package flow.",
    ),
    "TXT-UNRELATED": (
        "Routine maintenance covered the break-room lighting; conveyor operations were not involved.",
        "The inspection log concerns office ventilation and has no production-line entry.",
        "A routine facilities note records a warehouse door inspection unrelated to the line.",
    ),
}

# Input labels include registered dynamics/fault names and common descriptive aliases.
_CAUSE_FAMILY: dict[str, str] = {
    "SENSOR_BIAS": "sensor", "SENSOR_STUCK": "sensor", "SENSOR_SPIKE_BURST": "sensor",
    "SENSOR_SPIKE_OR_UNRELIABLE": "sensor", "SENSOR FAULT": "sensor", "SENSOR": "sensor",
    "VELOCITY_OFFSET": "motion", "SPEED_STEP": "motion", "ACTUATOR_DELAY": "actuator",
    "OBJECT_MISSING": "missing", "OBJECT_MISSING_OR_DROPPED": "missing",
    "BELT_STOP": "belt", "BELT_STOP_OR_MOTION_LOSS": "belt",
    "SECOND_DYNAMICS_CHANGE": "second_dynamics",
}
_FAMILY_CAUSES = {
    "TXT-MOTOR-SERVICE": {"motion", "belt"},
    "TXT-SENSOR-CAL": {"sensor"},
    "TXT-ACTUATOR-SLOW": {"actuator"},
    "TXT-PACKAGE-SLIP": {"motion"},
    "TXT-FLOW-MISSING": {"missing"},
    "TXT-UNRELATED": set(),
}


def _family_for_cause(cause: str) -> str:
    """Map one primitive/fault label to its registered helpful family."""
    key = str(cause).upper()
    if key == "VELOCITY_OFFSET" or key == "SPEED_STEP":
        return "TXT-MOTOR-SERVICE"  # seed-selectable alternative handled by caller
    if key in _CAUSE_FAMILY:
        return {
            "sensor": "TXT-SENSOR-CAL", "motion": "TXT-MOTOR-SERVICE",
            "actuator": "TXT-ACTUATOR-SLOW", "missing": "TXT-FLOW-MISSING",
            "belt": "TXT-MOTOR-SERVICE",
        }.get(_CAUSE_FAMILY[key], "UNKNOWN")
    return "UNKNOWN"


def select_template_family(seed: int, variant: TextVariant,
                           causal_category: str | Sequence[str] | None = None) -> str | None:
    """Return the selected family, exposed for audit receipts and deterministic tests."""
    if variant == "NO_TEXT_CONTEXT":
        return None
    if variant == "IRRELEVANT_TEXT_CONTEXT":
        return "TXT-UNRELATED"
    if causal_category is None:
        raise ValueError(f"{variant} context requires a registered causal category")
    if variant == "HELPFUL_TEXT_CONTEXT":
        options = compatible_families(causal_category)
        if not options:
            raise ValueError(f"UNKNOWN causal category: {causal_category}")
        return _pick(seed, options)
    causes = (causal_category,) if isinstance(causal_category, str) else tuple(causal_category)
    compatible = set(compatible_families(causes))
    if not compatible:
        raise ValueError(f"UNKNOWN causal category: {causal_category}")
    candidates = [family for family in TEMPLATE_FAMILIES if family != "TXT-UNRELATED" and family not in compatible]
    if not candidates:
        raise ValueError(f"no incompatible registered family for: {causal_category}")
    return _pick(seed, candidates)


def compatible_families(cause: str | Sequence[str]) -> tuple[str, ...]:
    """Return helpful-compatible families; UNKNOWN means the preregistration has no mapping."""
    causes = (cause,) if isinstance(cause, str) else tuple(cause)
    if not causes:
        return ()
    families: set[str] = set()
    for item in causes:
        key = str(item).upper()
        if key == "VELOCITY_OFFSET" or key == "SPEED_STEP":
            families.update(("TXT-MOTOR-SERVICE", "TXT-PACKAGE-SLIP"))
        else:
            family = _family_for_cause(key)
            if family == "UNKNOWN":
                return ()
            families.add(family)
    return tuple(sorted(families))


def _pick(seed: int, values: Sequence[str]) -> str:
    return values[int(seed) % len(values)]


def _render(family: str, seed: int) -> str:
    variants = _WORDING[family]
    return variants[int(seed) % len(variants)]


def _numeric_leak_check(text: str) -> None:
    # All registered context prose is qualitative. Reject any digit or numeric token.
    if re.search(r"(?<![A-Za-z])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", text):
        raise ValueError("policy text contains numeric content")


def generate_context(
    episode_id: str | int,
    seed: int,
    variant: TextVariant,
    causal_category: str | Sequence[str] | None = None,
    hidden_values: Sequence[float | int | str] = (),
) -> str:
    """Generate a frozen-family context. No trigger-time metadata is emitted."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown text context variant: {variant}")
    if variant == "NO_TEXT_CONTEXT":
        text = ""
    elif variant == "IRRELEVANT_TEXT_CONTEXT":
        text = _render("TXT-UNRELATED", seed)
    elif variant == "HELPFUL_TEXT_CONTEXT":
        text = _render(select_template_family(seed, variant, causal_category), seed)  # type: ignore[arg-type]
    else:
        family = select_template_family(seed, variant, causal_category)
        text = _render(family, seed)
    validate_text_context(text, hidden_values)
    _numeric_leak_check(text)
    return text


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class FrozenContext:
    episode_id: str
    variant: TextVariant
    text: str
    content_sha256: str


def freeze_context(episode_id: str | int, seed: int, variant: TextVariant,
                   causal_category: str | Sequence[str] | None = None,
                   hidden_values: Sequence[float | int | str] = ()) -> FrozenContext:
    text = generate_context(episode_id, seed, variant, causal_category, hidden_values)
    return FrozenContext(str(episode_id), variant, text, content_sha256(text))


def freeze_episode_contexts(episode_id: str | int, seed: int,
                            causal_category: str | Sequence[str],
                            hidden_values: Sequence[float | int | str] = ()) -> dict[TextVariant, FrozenContext]:
    """Freeze text and content hash for all four paired conditions of one episode."""
    return {
        variant: freeze_context(episode_id, seed, variant, causal_category, hidden_values)
        for variant in VARIANTS
    }


def verify_frozen_context(frozen: FrozenContext | dict, text: str | None = None,
                          expected_sha256: str | None = None) -> None:
    """Fail closed on content/hash mismatch; never downgrade to NO_TEXT_CONTEXT."""
    if isinstance(frozen, dict):
        episode_id, variant = str(frozen["episode_id"]), frozen["variant"]
        expected_text = frozen["text"]
        stored_sha = frozen["content_sha256"]
    else:
        episode_id, variant, expected_text, stored_sha = frozen.episode_id, frozen.variant, frozen.text, frozen.content_sha256
    actual = expected_text if text is None else text
    expected = stored_sha if expected_sha256 is None else expected_sha256
    actual_sha = content_sha256(actual)
    if actual != expected_text or actual_sha != expected or stored_sha != content_sha256(expected_text):
        raise ValueError(f"frozen context mismatch for episode={episode_id}, variant={variant}")


def frozen_context_json(record: FrozenContext) -> str:
    return json.dumps(asdict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
