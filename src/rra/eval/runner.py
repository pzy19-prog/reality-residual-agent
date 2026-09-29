"""Evaluation orchestration that keeps policy inputs separate from labels."""

from __future__ import annotations

from typing import Any

from rra.eval.scenarios import EpisodeRealization
from rra.eval.scoring import build_denominators, dispositions_for_episode, score_episode
from rra.eval.text_context import TextVariant, generate_text_context, validate_text_context
from rra.evidence import run_episode
from rra.sim import WorldConfig


def run_labeled_episode(
    config: WorldConfig,
    seed: int,
    realization: EpisodeRealization | None,
    *,
    text_variant: TextVariant = "NO_TEXT_CONTEXT",
    compensation: bool = True,
    fast_time_limit: float = 0.50,
    fast_residual_threshold: float = 1.25,
) -> dict[str, Any]:
    """Create evaluator labels first, run sanitized policy, then score truth."""
    # This map is constructed before the policy run and kept outside its receipt.
    dispositions = dispositions_for_episode(realization, config.object_count)
    text = generate_text_context(seed, text_variant)
    hidden_values = (
        [*realization.recoverable.values(), *realization.fault.values()]
        if realization else []
    )
    validate_text_context(text, hidden_values)
    policy_receipt = run_episode(
        config,
        seed,
        compensation,
        terminal_monitoring="corrected",
        realization=realization,
        text_context=text,
        fast_time_limit=fast_time_limit,
        fast_residual_threshold=fast_residual_threshold,
    )
    scores = score_episode(
        policy_receipt,
        dispositions,
        tolerance=config.tolerance,
        dt=config.dt,
        realization=realization,
        challenge_ids=[],
        preservation_ids=[],
    )
    return {
        "policy_receipt": policy_receipt,
        "evaluator": {"dispositions": dispositions, "scores": scores},
    }


def score_against_b1_denominators(
    candidate_receipt: dict[str, Any],
    realization: EpisodeRealization | None,
    config: WorldConfig,
    b1_corrected_receipt: dict[str, Any],
) -> dict[str, Any]:
    """Score a candidate using challenge/preservation IDs frozen by B1."""
    dispositions = dispositions_for_episode(realization, config.object_count)
    frozen = build_denominators(b1_corrected_receipt, dispositions)
    return score_episode(
        candidate_receipt,
        dispositions,
        tolerance=config.tolerance,
        dt=config.dt,
        realization=realization,
        challenge_ids=frozen["challenge"],
        preservation_ids=frozen["preservation"],
    )
