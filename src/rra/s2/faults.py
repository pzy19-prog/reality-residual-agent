"""Shared deterministic fault evidence checks from P3 §13.3.1."""
from rra.s2.dsl import FaultHypothesis

def check_faults(observations, *, sigma=.015, dt=.1, nominal_speed=1.0, presence_events=(), contradictory=False,
                 return_windows=False):
    rows=tuple(observations); found=[]
    windows={}
    if len(rows)>=4:
        last=rows[-4:]
        if max(x.observed_x for x in last)-min(x.observed_x for x in last)<=sigma and nominal_speed*3*dt>4*sigma:
            found.append(FaultHypothesis.SENSOR_STUCK)
            windows[FaultHypothesis.SENSOR_STUCK] = tuple(last)
        velocity=(last[-1].observed_x-last[0].observed_x)/(3*dt)
        if abs(velocity)<=2*sigma/dt and nominal_speed>0:
            found.append(FaultHypothesis.BELT_STOP_OR_MOTION_LOSS)
            windows[FaultHypothesis.BELT_STOP_OR_MOTION_LOSS] = tuple(last)
    if any(not bool(e.get('target_observed',True)) for e in presence_events): found.append(FaultHypothesis.OBJECT_MISSING_OR_DROPPED)
    if contradictory: found.append(FaultHypothesis.POST_VERIFICATION_CHANGE)
    if not found: found.append(FaultHypothesis.UNKNOWN_OR_INSUFFICIENT_EVIDENCE)
    faults=tuple(found)
    return (faults, windows) if return_windows else faults
