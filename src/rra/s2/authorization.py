"""Scoped authorization records; global fast-layer limits are never mutated."""
from dataclasses import dataclass
from rra.s2.dsl import Action
@dataclass(frozen=True)
class RecoveryAuthorization:
    authorization_id: str
    episode_id: str
    hypothesis_id: str
    evidence_ids: tuple[str,...]
    fitted_parameters: dict[str,float]
    verifier_score: float
    permitted_action: Action
    temporary_policy_exception: dict[str,float]
    controller_constraints_preserved: bool
    scope: str
    expires_at: float

def authorize(*, episode_id, hypothesis_id, evidence_ids, parameters, score, action, scope, expires_at, exception=None):
    if action is not Action.UPDATE_MODEL_AND_REPLAN: raise ValueError('only verified replan can be authorized')
    return RecoveryAuthorization(f'{episode_id}:{hypothesis_id}:{expires_at:.6f}',episode_id,hypothesis_id,tuple(evidence_ids),dict(parameters),float(score),action,dict(exception or {}),True,scope,float(expires_at))
