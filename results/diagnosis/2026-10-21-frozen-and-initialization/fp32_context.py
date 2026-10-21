import sys,json,math
from pathlib import Path
OUT=Path(__file__).parent;STUDY=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');BASE=STUDY/'results/inference/2026-10-21-base-cases'
sys.path.insert(0,str(STUDY/'scripts/python'))
from physics_metrics import branch_flows
out={}
for n in ['control-case500','case300','case300x2']:
    c=json.loads((OUT/(n+'-input.json')).read_text());raw=json.loads((BASE/(n+'-model-output.json')).read_text())
    obj=json.loads((BASE/(n+'.pyg.json')).read_text()) if n!='control-case500' else json.loads(Path('/Users/ninadsonawane/workspace/research-dev/GridSFM/model/samples/case500_goc.pyg.json').read_text())
    pred=json.loads((BASE/(n+'-prediction.json')).read_text()) if n!='control-case500' else dict(vm=raw['V'],va_deg=[math.degrees(a) for a in raw['theta']],pg_mw=[a*100 for a in raw['Pg']],qg_mvar=[a*100 for a in raw['Qg']])
    sf,st=branch_flows(c,pred['vm'],pred['va_deg'])
    rows=obj['metadata']['ac_line_source_rows']+obj['metadata']['transformer_source_rows'] if n!='control-case500' else list(range(len(c['branch'])))
    emax=max(abs(complex(raw['Pij'][i]*100,raw['Qij'][i]*100)-sf[j]) for i,j in enumerate(rows))
    tmax=max(abs(complex(raw['Pji'][i]*100,raw['Qji'][i]*100)-st[j]) for i,j in enumerate(rows))
    ys=[1/math.hypot(br[2],br[3]) for br in c['branch']];yc=[1/math.sqrt(max(br[2]**2+br[3]**2,1e-6)) for br in c['branch']]
    out[n]={'saved_FP32_forward_max_complex_branch_flow_difference_from_exact_MVA':max(emax,tmax),'graph_context_admittance_feature':{'exact_max_abs_series_y_pu':max(ys),'clipped_max_abs_series_y_pu':max(yc),'exact_mean_abs_series_y_pu':sum(ys)/len(ys),'clipped_mean_abs_series_y_pu':sum(yc)/len(yc),'scope':'pe_features graph context summarizes admittance with r2+x2 floor1e-6; a clipped model input statistic, not exact network evaluation'}}
(OUT/'fp32-and-context-check.json').write_text(json.dumps(out,indent=2)+'\n')
