"""Exhaustive B3 hypothesis enumeration over a policy evidence packet."""
from rra.s2.dsl import structures, FaultHypothesis, Action
from rra.s2.fitter import fit
from rra.s2.verifier import verify, common_action
from rra.s2.faults import check_faults

def run_b3(observations, *, nominal_speed, feedback=(), evidence_refs=(), current_time=0.0, dt=.1, horizon=9.9, tolerance=.2, error=None, presence_events=()):
    """Fit and verify all 14 structures, then apply fault and ambiguity gates."""
    checks=check_faults(observations,nominal_speed=nominal_speed,dt=dt,presence_events=presence_events)
    faults=tuple(x for x in checks if x is not FaultHypothesis.UNKNOWN_OR_INSUFFICIENT_EVIDENCE)
    fitted=[]; verified=[]
    for index,structure in enumerate(structures()):
        result=fit(structure,observations,nominal_speed=nominal_speed,feedback=feedback)
        fitted.append(result)
        verified.append(verify(result,hypothesis_id=f'h{index:02d}',evidence_refs=evidence_refs))
    passing=[x for x in verified if x.passed]
    if faults:
        action=Action.HUMAN_ESCALATION if FaultHypothesis.BELT_STOP_OR_MOTION_LOSS in faults or FaultHypothesis.OBJECT_MISSING_OR_DROPPED in faults else Action.PAUSE_AND_REOBSERVE
        gate_reason='FAULT_EVIDENCE'
        action_time=None
    else:
        error=error or (lambda h,t: abs(t-current_time)*0.0)
        action,action_time,gate_reason=common_action(passing,current_time=current_time,dt=dt,horizon=horizon,tolerance=tolerance,error=error)
    return {'fits':fitted,'verifications':verified,'passing':passing,'faults':faults,'action':action,'action_time':action_time,'gate_reason':gate_reason}
