import hashlib
import importlib
import inspect
import json
import subprocess
import sys

import numpy as np
import pytest
from rra.s2.dsl import Action, Primitive, structures
from rra.s2.fitter import Observation, fit
from rra.s2.verifier import Verification, common_action, verify


def test_structures_exactly_14_unique():
    s=structures()
    assert len(s)==14 and len(set(s))==14
    assert all(len(set(x))==len(x) for x in s)

@pytest.mark.parametrize('structure,params',[
    ((Primitive.SENSOR_BIAS,),{'sensor_bias':.22}),
    ((Primitive.VELOCITY_OFFSET,),{'velocity_offset':.12}),
    ((Primitive.SPEED_STEP,),{'speed_step_time':1.75,'speed_step_delta':.16}),
    ((Primitive.ACTUATOR_DELAY,),{'actuator_delay':.2}),
    ((Primitive.SENSOR_BIAS,Primitive.VELOCITY_OFFSET,Primitive.SPEED_STEP),{'sensor_bias':-.18,'velocity_offset':.07,'speed_step_time':2.0,'speed_step_delta':-.12}),
])
def test_fit_recovers_synthetic_parameters(structure,params):
    rng=np.random.default_rng(23); ts=np.arange(0,5,.1); v0=1.0; y=np.zeros_like(ts)
    y += params.get('sensor_bias',0)+params.get('velocity_offset',0)*ts
    y += params.get('speed_step_delta',0)*np.maximum(0,ts-params.get('speed_step_time',99))
    y += rng.normal(0,.002,len(ts))
    obs=[Observation(float(t),float(3+v0*t+e),float(3+v0*t)) for t,e in zip(ts,y)]
    feedback=[]
    if Primitive.ACTUATOR_DELAY in structure:
        from rra.s2.fitter import CommandFeedback
        feedback=[CommandFeedback(float(t),float(t+params['actuator_delay']+rng.normal(0,.002)),True,True) for t in range(10)]
    result=fit(structure,obs,nominal_speed=v0,feedback=feedback)
    assert not result.no_fit
    for k,v in params.items(): assert abs(result.parameters[k]-v)<(.035 if k=='speed_step_time' else .015)

def test_verifier_boundaries():
    from rra.s2.fitter import FitResult
    s=(Primitive.SENSOR_BIAS,)
    assert not verify(FitResult(s,{},.01,(),5),hypothesis_id='x').passed
    assert verify(FitResult(s,{},.030,(),6),hypothesis_id='x').passed
    assert not verify(FitResult(s,{},.03001,(),6),hypothesis_id='x').passed

def test_ambiguity_without_common_action():
    a=Verification('a',(),{},6,.01,(),(),True,())
    b=Verification('b',(),{},6,.01,(),(),True,())
    action,t,reason=common_action([a,b],current_time=0,dt=.1,horizon=.2,tolerance=.2,error=lambda h,t: .3 if h.hypothesis_id=='a' else .4)
    assert action is Action.PAUSE_AND_REOBSERVE and t is None and reason=='AMBIGUOUS'

def test_s2_import_allowlist():
    for name in ['rra.s2.dsl','rra.s2.fitter','rra.s2.verifier','rra.s2.authorization','rra.s2.faults','rra.s2.b3']:
        module=importlib.import_module(name)
        source=inspect.getsource(module)
        assert 'rra.sim' not in source and 'rra.eval.scenarios' not in source

def test_deterministic_receipt_hash(tmp_path):
    code="""import json,hashlib,numpy as np\nfrom rra.s2.dsl import structures\nfrom rra.s2.fitter import Observation,fit\nfrom rra.s2.verifier import verify\nrng=np.random.default_rng(7); obs=[Observation(i*.1,1+i*.1+.2+rng.normal(0,.002),1+i*.1) for i in range(20)]; rows=[]\nfor j,s in enumerate(structures()):\n f=fit(s,obs,nominal_speed=1); v=verify(f,hypothesis_id=f'h{j}',evidence_refs=['e0']); rows.append({'id':v.hypothesis_id,'p':v.fitted_parameters,'rmse':v.rmse,'pass':v.passed})\nb=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); print(hashlib.sha256(b).hexdigest())"""
    vals=[]
    import os
    env=dict(os.environ, PYTHONPATH='src')
    for _ in range(2): vals.append(subprocess.check_output([sys.executable,'-c',code],text=True,env=env).strip())
    assert vals[0]==vals[1]

def test_episode_s2_handoff_is_deterministic():
    from rra.sim.world import WorldConfig
    from rra.eval.scenarios import v0_combo_realization
    from rra.evidence.episode import run_episode
    config=WorldConfig(scenario="nominal")
    realization=v0_combo_realization(0)
    runs=[run_episode(config,0,True,terminal_monitoring='corrected',realization=realization,system2_enabled=True) for _ in range(2)]
    assert runs[0]['receipt_sha256']==runs[1]['receipt_sha256']
    assert runs[0]['system2_decisions']
    for item in runs[0]['system2_decisions']:
        assert item['action'] in {a.value for a in Action}
        if item['action']==Action.UPDATE_MODEL_AND_REPLAN.value:
            assert item['authorization']['controller_constraints_preserved'] is True


def test_actuator_delay_requires_command_feedback():
    obs=[Observation(i*.1,1+i*.1,1+i*.1) for i in range(8)]
    result=fit((Primitive.ACTUATOR_DELAY,),obs,nominal_speed=1.0)
    assert result.no_fit

def test_episode_runner_has_no_dsl_prediction_implementation():
    import inspect
    from rra.evidence import episode
    source = inspect.getsource(episode)
    assert 'def prediction_error' not in source
    assert 'speed_step_delta' not in source
