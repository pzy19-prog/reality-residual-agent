"""Numeric verification and common-action gate."""
from dataclasses import dataclass
from math import sqrt
from typing import Callable, Iterable
from rra.s2.dsl import Action
from rra.s2.fitter import FitResult

@dataclass(frozen=True)
class Verification:
    hypothesis_id: str
    structure: tuple[str,...]
    fitted_parameters: dict[str,float]
    n_usable: int
    rmse: float
    residual_vector: tuple[float,...]
    violated_invariants: tuple[str,...]
    passed: bool
    evidence_refs: tuple[str,...]
    action_time: float|None=None
    common_action: bool=False

def verify(result: FitResult, *, hypothesis_id: str, evidence_refs: Iterable[str]=(), threshold: float=.030) -> Verification:
    violations=[]
    if result.no_fit or result.n_usable < 6: violations.append('n_usable < 6')
    if result.objective > threshold: violations.append('RMSE > 0.030')
    return Verification(hypothesis_id,tuple(p.value for p in result.structure),result.parameters,result.n_usable,result.objective,result.residuals,tuple(violations),not violations,tuple(evidence_refs))

def common_action(passing: Iterable[Verification], *, current_time: float, dt: float, horizon: float, tolerance: float, error: Callable[[Verification,float],float]):
    rows=tuple(passing)
    if not rows: return Action.PAUSE_AND_REOBSERVE, None, 'NO_VERIFIED_HYPOTHESIS'
    grid=[]; k=0
    while current_time+k*dt <= horizon+1e-12:
        t=round(current_time+k*dt,10); score=max(error(h,t) for h in rows)
        if score<=tolerance: grid.append((score,t))
        k+=1
    if grid:
        score,t=min(grid,key=lambda x:(x[0],x[1])); return Action.UPDATE_MODEL_AND_REPLAN,t,'COMMON_ACTION'
    if len(rows)>=2: return Action.PAUSE_AND_REOBSERVE,None,'AMBIGUOUS'
    return Action.PAUSE_AND_REOBSERVE,None,'NO_SAFE_ACTION'
