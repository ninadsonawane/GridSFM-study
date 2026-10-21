import sys,json,math
from pathlib import Path
OUT=Path(__file__).parent;STUDY=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');BASE=STUDY/'results/inference/2026-10-21-base-cases'
sys.path.insert(0,str(STUDY/'scripts/python'))
from physics_metrics import evaluate
report={}
for name in ['case300','case300x2']:
    obj=json.loads((BASE/f'{name}-labeled.pyg.json').read_text());c=json.loads((BASE/f'{name}-input.json').read_text());native=obj['solution']['nodes'];md=obj['metadata'];base=c['baseMVA'];original=json.loads((BASE/f'{name}-reference.json').read_text())
    s={k:[0.0]*len(c['bus' if k in ['vm','va_deg'] else 'gen']) for k in ['vm','va_deg','pg_mw','qg_mvar']}
    for row,x in zip(md['bus_source_rows'],native['bus']):s['vm'][row]=x[1];s['va_deg'][row]=math.degrees(x[0])
    for row,x in zip(md['gen_source_rows'],native['generator']):s['pg_mw'][row]=x[0]*base;s['qg_mvar'][row]=x[1]*base
    m=evaluate(c,s);assert m['all_tested_constraints_pass'];error=max(abs(a-b) for k in s for a,b in zip(s[k],original[k]));assert error<1e-10
    report[name]={'route':'original solver reference -> saved native labeled .pyg.json -> reload -> source-row map -> radians to degrees,pu to MW/MVAr -> original evaluator','state_max_roundtrip_difference':error,'all_tested_constraints_pass':True,'max_p_residual_mw':m['max_p_residual_mw'],'max_q_residual_mvar':m['max_q_residual_mvar']}
(OUT/'reference-export-reload-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
