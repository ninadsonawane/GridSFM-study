import sys,json,math
from pathlib import Path
OUT=Path(__file__).parent
sys.path.insert(0,str(OUT))
# Diagnose's calculations are deterministic and reuse saved states; no model forward.
import diagnose as d
from gridsfm.model import GridTransformerBackbone as GT
import torch,numpy as np
extra={}
for name,c,p,ref,rcost in d.cases:
    x=(d.load(d.BASE/f'{name}.pyg.json') if name!='control-case500' else d.obj)
    grids=x['grid']['edges'];md=x['metadata'];results={}
    for state_name,s in [('prediction',p),('reference',ref)]:
        T=lambda a:torch.tensor(a,dtype=torch.float64)
        V=T(s['vm']);theta=T([math.radians(a) for a in s['va_deg']]);ef=d.diagnostic_flows(c,s,'forward_epsilon')
        actual=[];idx=0
        for kind in ['ac_line','transformer']:
            e=grids[kind];ei=torch.tensor([e['senders'],e['receivers']],dtype=torch.long);ea=T(e['features'])
            fn=GT._pi_model_flows_ac_line if kind=='ac_line' else GT._pi_model_flows_transformer
            vals=fn(ei,ea,V,theta);arr=torch.stack(vals,dim=-1).numpy()*c['baseMVA'];actual.extend(arr)
        # Native family order differs from original source rows for case300.
        if name=='control-case500':rows=list(range(len(c['branch'])))
        else:rows=md['ac_line_source_rows']+md['transformer_source_rows']
        exact=np.array([[ef[0][j].real,ef[0][j].imag,ef[1][j].real,ef[1][j].imag] for j in rows])
        delta=float(np.max(np.abs(np.asarray(actual)-exact)));assert delta<1e-6,delta
        results[state_name]={'actual_forward_static_double_precision_max_error_MW_or_MVAr':delta}
    rates=np.array([b[5]/c['baseMVA'] for b in c['branch']]);f=d.diagnostic_flows(c,p,'forward_epsilon')
    ratios=np.maximum(np.abs(f[0]),np.abs(f[1]))/c['baseMVA']/np.maximum(rates,1e-9)
    results['zero_rating_stress_bug']={'unlimited_branch_count':int(sum(rates==0)),'max_false_loading_ratio_on_unlimited_branch':float(max(ratios[rates==0])) if any(rates==0) else None,'path':'stress_features.py:155 clamps zero/unlimited RATE_A to1e-9pu, feeds enormous false thermal violations to feasibility head; computed after voltage/generation heads so does not explain their errors'}
    extra[name]=results
d.save('forward-and-rating-checks.json',extra)
gate={'A_gate':'PASS for numerical pipeline/evaluator correctness; model physics differences diagnosed, not repaired','B_authorized':True,'reason':'Control and both solver reference states remain feasible after reloading; prior conversion/mapping/label checks reused; exact evaluator agrees with independently generated references. Loss clamp and unlimited-rating stress semantics are model-side differences, not unresolved input mapping errors.','diagnosis':'model-physics mismatch plus poor frozen transfer; full causal attribution of dispatch error remains uncertain'}
d.save('A-gate.json',gate)
print(json.dumps(extra,indent=2));print(json.dumps(gate))
