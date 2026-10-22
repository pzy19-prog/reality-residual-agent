"""One authorized live NIM smoke call with at most two backoff retries."""
from __future__ import annotations

import json
import time

from rra.llm.adapter import HypothesisProposer
from rra.llm.providers import NvidiaNimProvider


def main() -> int:
    packet = {
        "observations": [
            {"target_id": "synthetic-1", "step": 4, "time": 0.4,
             "observed_x": 0.438, "nominal_x": 0.400},
            {"target_id": "synthetic-1", "step": 5, "time": 0.5,
             "observed_x": 0.552, "nominal_x": 0.500},
            {"target_id": "synthetic-1", "step": 6, "time": 0.6,
             "observed_x": 0.671, "nominal_x": 0.600},
        ],
        "command_feedback": [],
        "known_configuration": {"dt": 0.1, "belt_speed": 1.0},
    }
    context = "The position sensor was calibrated recently, though its stability should be checked."
    provider = NvidiaNimProvider()
    proposer = HypothesisProposer(provider)
    errors: list[str] = []
    proposal = None
    for attempt in range(3):
        proposal = proposer.propose(packet, context)
        status = provider.last_http_status
        if status is not None and 200 <= status < 300:
            break
        errors.append(proposal.error or f"HTTP status {status}")
        if attempt < 2:
            time.sleep(2 ** attempt)
    result = {
        "http_status": provider.last_http_status,
        "latency_seconds": provider.last_latency_seconds,
        "structure_ids": [item.hypothesis_id for item in proposal.items] if proposal else [],
        "proposal_error": proposal.error if proposal else "no proposal",
        "retry_errors": errors,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if provider.last_http_status is not None and 200 <= provider.last_http_status < 300 else 2


if __name__ == "__main__":
    raise SystemExit(main())
