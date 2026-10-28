"""Aggregate saved native/solver outputs; never performs inference or solves."""
import csv,json,pathlib,sys
from electrical import *
from prepare import O,read,save,sha
REL=['microsoft-v1.1','newer-base-v2']
def compact():
 flat=[];clamps=[];focus=[];rows=[]
 for d in sorted((O/'cases').glob('*')):
  if not (d/'summary.json').exists():continue
  summaries=read(d/'summary.json')
  for s in summaries:
   r={k:s.get(k) for k in ['scenario','method','status','reference_valid','AC_joint_feasible','native_DC_constraints_pass','P_violating_buses','Q_violating_buses','Pg_violating_count','Qg_violating_count','Vm_violating_count','angle_violating_count','thermal_violating_count','Pg_max_excess','Qg_max_excess','Vm_max_excess','angle_max_excess_deg','thermal_max_excess_MVA_or_DC_MW','thermal_max_ratio','P_worst_bus','Q_worst_bus','total_Pg_MW','total_Qg_MVAr','Qg_at_lower_count','Qg_at_upper_count']}
   for v in ['P','Q']:
    for stat in ['mean','median','p95','max']:r[v+'_'+stat]=None if s.get(v) is None else s[v][stat]
   a=s.get('approximation')
   for label,key in [('Pg','Pg_per_generator_MW'),('Qg','Qg_per_generator_MVAr'),('Vm','Vm_pu'),('angle','aligned_angle_deg'),('Pflow','branch_P_MW')]:
    for stat in ['mean','median','p95','max']:r[label+'_error_'+stat]=None if a is None or a[key] is None else a[key][stat]
   flat.append(r)
  for c in read(d/'clipping-summary.json'):clamps.append(dict(scenario=d.name,**c))
  with (d/'bus-metrics.csv').open(newline='') as f:
   for b in csv.DictReader(f):
    if int(b['original_bus_id']) in [235,238,137,231]:focus.append(b)
 csvsave(O/'method-summary.csv',flat);save(O/'method-summary.json',flat);save(O/'clipping-summary.json',clamps);csvsave(O/'focus-buses.csv',focus)
 def f(v):return 'N/A' if v is None else f'{v:.5g}' if isinstance(v,(int,float)) else str(v)
 lines=['# Live comparison table','','This table is generated only from saved results. All errors use the corresponding independently accepted AC reference. P/Q residual units are MW/MVAr; Vm error is pu; angle error is degrees. Thermal assessment is N/A for original case300 and covers only existing rated ties for the connected system. DC Qg/Vm/joint AC feasibility are N/A.','','| Input | Method | Accepted AC | Pg / Qg / Vm / angle / Pflow MAE | P/Q violations | P/Q max severity | Q mean / median / p95 | Thermal count / max excess | Native joint AC |','|---|---|---|---|---|---|---|---|---|']
 for r in flat:
  lines.append('| '+' | '.join([r['scenario'],r['method'],str(r['reference_valid']),' / '.join(f(r[k+'_error_mean']) for k in ['Pg','Qg','Vm','angle','Pflow']),f(r['P_violating_buses'])+'/'+f(r['Q_violating_buses']),f(r['P_max'])+'/'+f(r['Q_max']),' / '.join(f(r['Q_'+k]) for k in ['mean','median','p95']),f(r['thermal_violating_count'])+'/'+f(r['thermal_max_excess_MVA_or_DC_MW']),f(r['AC_joint_feasible'])])+' |')
 (O/'live-table.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'completed_inputs':len(set(r['scenario'] for r in flat)),'AC_accepted':sum(r['method']=='AC-OPF' and r['reference_valid'] for r in flat),'model_native_joint_pass':sum(r['method'] in REL and r['AC_joint_feasible'] is True for r in flat),'method_rows':len(flat)},indent=2))
def diagnostic():
 c=read(O/'bases/300/input.json');ref=read(O/'recovered-base/AC-reference-DERIVED-state.json')['state'];rows=[];cross=[]
 for rel in REL:
  root=O/'diagnostic'/rel
  if not (root/'summary.json').exists():continue
  report=read(root/'summary.json')
  baseline=None
  for rec in report['records']:
   d=root/rec['name'];file=d/(rel+'-native.json')
   if not file.exists():continue
   cc=read(d/'input.json');state=read(file);sm,_,_,_=score(cc,state,rel)
   row={'release':rel,'diagnostic':rec['name'],'Pmax':sm['P']['max'],'Qmax':sm['Q']['max'],'Qmean':sm['Q']['mean'],'Pviolations':sm['P_violating_buses'],'Qviolations':sm['Q_violating_buses'],'AC_joint_feasible':sm['AC_joint_feasible']}
   if 'native_difference_vs_original_baseline' in rec:
    for key,v in rec['native_difference_vs_original_baseline'].items():row[key+'_diff_max']=v['max_abs'];row[key+'_diff_mean']=v['mean_abs']
   rows.append(row)
   if rec['name']=='baseline-cold':
    baseline=state;historic=read(O/'recovered-base'/(rel+'-DERIVED-state.json'))['state']
    delta={key:{'max_abs':float(np.abs(np.asarray(state[key])-historic[key]).max()),'mean_abs':float(np.abs(np.asarray(state[key])-historic[key]).mean())} for key in historic}
    sm,_,_,_=score(c,state,rel,ref);cross.append({'release':rel,'fresh_vs_historical_native':delta,'fresh_native_score':sm,'note':'Direct cross-platform replay comparison; separate from exact within-platform repeatability.'})
 csvsave(O/'diagnostic-effects.csv',rows);save(O/'cross-platform-replay.json',cross)
 print(json.dumps(cross,indent=2))
if __name__=='__main__':
 diagnostic() if len(sys.argv)>1 and sys.argv[1]=='diagnostic' else compact()
