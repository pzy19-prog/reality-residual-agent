"""Dev-only paired B1-corrected and exhaustive B3 run."""
from __future__ import annotations
import json
from hashlib import sha256
from pathlib import Path
from typing import Any
from rra.eval.scenarios import FAULT_FAMILIES, composition_structures, realize_episode
from rra.eval.scoring import dispositions_for_episode
from rra.eval.runner import score_against_b1_denominators
from rra.evidence import run_episode
from rra.eval.framework import v3_world_config

ROOT=Path(__file__).resolve().parents[3]

def run_b3_dev(output_dir: Path=ROOT/'artifacts'/'s2') -> dict[str,Any]:
    """Run paired corrected B1/B3 over every registered dev seed, never eval seeds."""
    seeds=json.loads((ROOT/'config'/'dev_seeds.json').read_text())['seeds']
    config=v3_world_config('nominal')
    structures=composition_structures()
    episodes=[]
    for i,seed in enumerate(seeds):
        if i%19 < len(structures):
            realization=realize_episode(seed,structures[i%19])
        else:
            realization=realize_episode(seed,(),FAULT_FAMILIES[i%19-len(structures)])
        b1=run_episode(config,seed,True,terminal_monitoring='corrected',realization=realization)
        b3=run_episode(config,seed,True,terminal_monitoring='corrected',realization=realization,system2_enabled=True)
        score=score_against_b1_denominators(b3,realization,config,b1)
        labels=dispositions_for_episode(realization,config.object_count)
        auth=[d for d in b3.get('system2_decisions',[]) if d['action']=='UPDATE_MODEL_AND_REPLAN']
        successes=score['success_count']
        episodes.append({
            'seed':seed,'case':list(realization.structure),'fault_family':realization.fault_family,
            'b1_terminal_counts':b1['metrics']['terminal_counts'],
            'b3_terminal_counts':b3['metrics']['terminal_counts'],'score':score,
            'challenge_ids':sorted(int(k) for k,v in score['dispositions'].items() if b1['outcomes'][int(k)]['status']!='picked'),
            'preservation_ids':sorted(int(k) for k,v in score['dispositions'].items() if b1['outcomes'][int(k)]['status']=='picked' and v=='RECOVER'),
            'refuse_total':sum(v=='REFUSE' for v in labels.values()),
            'refuse_correct':sum(v=='REFUSE' and not any(int(o['target_id'])==k and o.get('command_issued') for o in b3['evaluator_objects']) for k,v in labels.items()),
            'authorizations':len(auth),'pause_target_ids':sorted({d['target_id'] for d in b3.get('system2_decisions',[]) if d['action'] in ('PAUSE_AND_REOBSERVE','HUMAN_ESCALATION')}),'pause_seconds':sum(d.get('pause_seconds',0.0) for d in b3.get('system2_decisions',[])),
            'miss_count':score['ordinary_miss_count'],
        })
    def summed(key): return sum(ep['score'][key] for ep in episodes)
    recoverable_challenge=sum(ep['score']['recoverable_challenge_count'] for ep in episodes)
    challenge_success=sum(ep['score']['challenge_success_count'] for ep in episodes)
    preservation=sum(ep['score']['preservation_count'] for ep in episodes)
    refuse_n=sum(ep['refuse_total'] for ep in episodes)
    receipt={
        'schema_version':'rra.s2.b3-dev.v1','seed_identity':{'path':'config/dev_seeds.json','values':seeds},
        'episode_count':len(episodes),'b1':'corrected','b3':'exhaustive-14-structures',
        'metrics':{
            'recoverable_success':challenge_success/recoverable_challenge if recoverable_challenge else 0.0,
            'recoverable_challenge_success_count':challenge_success,'recoverable_challenge_count':recoverable_challenge,
            'pause_refusal':sum(len(ep['pause_target_ids']) for ep in episodes),
            'correct_refuse_rate':sum(ep['refuse_correct'] for ep in episodes)/refuse_n if refuse_n else 0.0,
            'wrong_disposition':summed('wrong_disposition_count'),'miss':summed('ordinary_miss_count'),
            'unsafe_action':summed('unsafe_action_count'),'preservation_regression_count':summed('preservation_regression_count'),
            'preservation_count':preservation,'authorization_count':sum(ep['authorizations'] for ep in episodes),
            'production_pause_seconds':sum(ep['pause_seconds'] for ep in episodes),
        },'episodes':episodes,
    }
    raw=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode()
    receipt['receipt_sha256']=sha256(raw).hexdigest()
    output_dir.mkdir(parents=True,exist_ok=True)
    (output_dir/'b3-dev.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    m=receipt['metrics']
    md='\n'.join(['# B1-corrected vs B3 — dev seeds','',f"Seeds: {len(seeds)} from `config/dev_seeds.json`; B3 enumerates all 14 DSL structures at every fast-layer escalation.",'','| Metric | B3 dev |','|---|---:|',f"| Recoverable challenge success | {m['recoverable_success']:.4f} ({m['recoverable_challenge_success_count']}/{m['recoverable_challenge_count']}) |",f"| Correct refusal rate | {m['correct_refuse_rate']:.4f} |",f"| Wrong disposition | {m['wrong_disposition']} |",f"| Miss | {m['miss']} |",f"| Unsafe action | {m['unsafe_action']} |",f"| Preservation regression | {m['preservation_regression_count']}/{m['preservation_count']} |",f"| Authorizations | {m['authorization_count']} |",f"| Production pause seconds | {m['production_pause_seconds']:.3f} |",'',f"Receipt SHA-256: `{receipt['receipt_sha256']}`",''])
    (output_dir/'b3-dev.md').write_text(md)
    return receipt
