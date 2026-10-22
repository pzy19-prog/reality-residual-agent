"""Deterministic bounded least-squares fitting over policy-visible evidence."""
from dataclasses import dataclass
from itertools import product
from math import sqrt
from typing import Sequence
import numpy as np
from rra.s2.dsl import Primitive

@dataclass(frozen=True)
class Observation:
    time: float
    observed_x: float
    nominal_x: float

@dataclass(frozen=True)
class CommandFeedback:
    issued_time: float
    execution_time: float
    accepted: bool
    success: bool

@dataclass(frozen=True)
class FitResult:
    structure: tuple[Primitive, ...]
    parameters: dict[str, float]
    objective: float
    residuals: tuple[float, ...]
    n_usable: int
    no_fit: bool = False

def _linear_fit(A, y):
    if A.shape[1] == 0: return np.array([]), y
    x, *_ = np.linalg.lstsq(A, y, rcond=None)
    return x, y-A@x

def fit(structure: Sequence[Primitive], observations: Sequence[Observation], *, nominal_speed: float, feedback: Sequence[CommandFeedback]=(), min_observations: int=6) -> FitResult:
    s=tuple(structure); obs=tuple(sorted(observations,key=lambda o:o.time))
    if len(set(s)) != len(s) or any(not isinstance(p,Primitive) for p in s): raise ValueError('invalid structure')
    if len(obs)<min_observations or nominal_speed<=0:
        return FitResult(s,{},float('inf'),(),len(obs),True)
    if Primitive.ACTUATOR_DELAY in s and not any(q.accepted for q in feedback):
        return FitResult(s,{},float('inf'),(),len(obs),True)
    t=np.array([o.time for o in obs]); y=np.array([o.observed_x-o.nominal_x for o in obs]); cols=[]; names=[]
    if Primitive.SENSOR_BIAS in s: cols.append(np.ones(len(t))); names.append('sensor_bias')
    if Primitive.VELOCITY_OFFSET in s: cols.append(t); names.append('velocity_offset')
    best=None
    taus=np.arange(0.5,5.001,0.05) if Primitive.SPEED_STEP in s else [None]
    delays=np.arange(0.0,0.501,0.01) if Primitive.ACTUATOR_DELAY in s else [None]
    for tau,d in product(taus,delays):
        c=list(cols); n=list(names)
        if tau is not None: c.append(np.maximum(0,t-tau)); n.append('speed_step_delta')
        A=np.column_stack(c) if c else np.zeros((len(t),0))
        x,res=_linear_fit(A,y); sq=float(res@res)
        params=dict(zip(n,map(float,x)))
        if tau is not None: params['speed_step_time']=float(tau)
        if d is not None: params['actuator_delay']=float(d)
        # Feedback timing is numeric evidence; only accepted commands contribute.
        f=[q for q in feedback if q.accepted]
        if d is not None and f:
            sq += sum((q.execution_time-q.issued_time-d)**2 for q in f)
        key=(sq, float(tau) if tau is not None else -1, float(d) if d is not None else -1)
        if best is None or key<best[0]: best=(key,params,res)
    key,params,res=best
    rmse=sqrt(float(key[0])/max(1,len(obs)+(len(feedback) if feedback else 0)))
    return FitResult(s,params,rmse,tuple(map(float,res)),len(obs),False)
