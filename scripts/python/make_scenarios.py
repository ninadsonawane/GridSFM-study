"""Generate design manifests only; no OPF labels or claimed feasible cases.

All descendants of a load-family stay in one split. The outage test is paired
with the first 100 nominal test families, never with training examples.
Per-bus perturbations are reconstructed from load_seed by load_multipliers().
"""
import argparse
import hashlib
import json
import random
from pathlib import Path


def load_multipliers(load_seed, buses_per_area=300):
    rng = random.Random(load_seed)
    return [[rng.uniform(.97, 1.03) for _ in range(buses_per_area)] for _ in range(2)]


def make_manifest():
    rows=[]
    for split, count, seed in [('train',500,31001),('validation',100,31002),('test_id',200,31003),('test_stress',100,31004)]:
        rng=random.Random(seed)
        for i in range(count):
            lam=rng.uniform(.9,1.1)
            delta=rng.uniform(-.1,.1)
            if split=='test_stress':
                delta=rng.choice([-1,1])*rng.uniform(.15,.20)
            family=f'{split}-{i:04d}'
            rows.append({'scenario_id':family+'-both','family_id':family,'split':split,
                         'lambda':lam,'delta':delta,'load_seed':rng.randrange(2**31),
                         'tie_status':[1,1], 'reference_status':'not_run',
                         'definition':'Pd,Qd multiplied by lambda*(1+delta in A,1-delta in B)*per_bus_multiplier'})
    for source in [r for r in rows if r['split']=='test_id'][:100]:
        out=dict(source)
        out.update(scenario_id=source['family_id']+'-tie2out',split='test_outage',tie_status=[1,0])
        rows.append(out)
    return {'protocol_version':'proposed-v1', 'status':'planned_unexecuted',
            'network_config':'configs/network-case300x2.json',
            'training_seeds':[17,29,43], 'training_budgets':[100,500],
            'nested_training_rule':'first 100 of the fixed train ordering; never filter using ML outcomes',
            'rows':rows}


def pilot():
    # 9 core points + 3 boundaries, both status modes; all excluded from paper splits.
    points=[(l,d) for l in (.9,1.,1.1) for d in (-.1,0.,.1)] + [(1.,-.2),(1.,.2),(.85,0.)]
    return [{'scenario_id':f'pilot-{i:02d}-{mode}', 'family_id':f'pilot-{i:02d}',
             'split':'pilot_only','lambda':l,'delta':d,'load_seed':90000+i,
             'tie_status':status,'reference_status':'not_run'}
            for i,(l,d) in enumerate(points) for mode,status in [('both',[1,1]),('tie2out',[1,0])]]


def validate(data):
    rows=data['rows']
    assert len(rows)==1000
    assert len({r['scenario_id'] for r in rows})==len(rows)
    memberships={}
    for r in rows:
        family_split='test' if r['split'].startswith('test') else r['split']
        memberships.setdefault(r['family_id'],set()).add(family_split)
    assert all(len(v)==1 for v in memberships.values())
    assert [sum(r['split']==s for r in rows) for s in ['train','validation','test_id','test_stress','test_outage']]==[500,100,200,100,100]


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',default='manifests/scenarios')
    args=parser.parse_args()
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    data=make_manifest();validate(data)
    for name,obj in [('proposed-v1.json',data),('pilot-v1.json',pilot())]:
        payload=(json.dumps(obj,indent=2,sort_keys=True)+'\n').encode()
        (out/name).write_bytes(payload)
        print(name,hashlib.sha256(payload).hexdigest())
