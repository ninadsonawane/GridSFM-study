"""Saved-state reporting only; no inference or solves."""
from study import *
METHODS=['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2']
LABEL={'microsoft-v1.1':'V1','newer-base-v2':'V2','AC-OPF':'AC-OPF','DC-OPF':'DC-OPF'}
def flat(x,prefix=''):
 out={}
 for k,v in x.items():
  key=prefix+k
  if isinstance(v,dict):out.update(flat(v,key+'.'))
  else:out[key]=v
 return out
def fmt(x):
 if x is None:return 'N/A'
 if isinstance(x,bool):return 'PASS' if x else 'FAIL'
 if isinstance(x,str):return x
 if isinstance(x,int):return str(x)
 return f'{x:.5g}'
def baseline_tables():
 lines=['# Baseline comparisons','', 'Nominal loads and unchanged original equipment limits. State errors use independently checked AC-OPF references. P and Q are MW and MVAr; V is pu; angles are degrees. DC Q, V, apparent thermal and full AC feasibility are N/A. Mean equipment excess includes all eligible items, including zeros. Generator state errors average online generators only; equipment checks include required zero output of offline units.','']
 for net in ['case300','case300x2','case500goc']:
  ms=read(ROOT/'results'/f'{net}-base/metrics.json');fm={m['method']:flat(m) for m in ms}
  keys=list(dict.fromkeys(k for m in fm.values() for k in m if k not in ['method','scenario','status','reference_valid']))
  lines += [f'## {net}','','| Metric | AC-OPF | DC-OPF | V1 | V2 |','|---|---:|---:|---:|---:|']
  for k in keys:
   if k.endswith('count') and ('.accuracy' in k or k.startswith('accuracy')):continue
   lines.append('| '+k+' | '+' | '.join(fmt(fm[m].get(k)) for m in METHODS)+' |')
  lines+=[''];csvsave(ROOT/'paper'/f'baseline-{net}.csv',[{'metric':k,**{LABEL[m]:fm[m].get(k) for m in METHODS}} for k in keys])
 (ROOT/'paper/baseline-tables.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def summary_and_plots():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 rows=[];plans=read(ROOT/'scenario-plan.json')['scenarios'];byid={s['id']:s for s in plans}
 for d in (ROOT/'results').iterdir():
  if not d.is_dir() or not (d/'metrics.json').exists():continue
  spec=byid.get(d.name,{'network':d.name.removesuffix('-base'),'group':'baseline','absolute_P_factor':1.,'absolute_Q_factor':1.})
  for m in read(d/'metrics.json'):rows.append({**spec,**flat(m)})
 csvsave(ROOT/'paper/all-metrics.csv',rows)
 main=[r for r in rows if r['group'] in ['baseline','P','Q','PQ']]
 feas=[]
 for net in ['case300','case300x2','case500goc']:
  for method in METHODS:
   rr=[r for r in main if r['network']==net and r['method']==method];dc=method=='DC-OPF';key='DC_own_constraints_pass' if dc else 'AC_joint_pass'
   feas.append({'network':net,'method':method,'attempted':len(rr),'returned':sum(key in r for r in rr),'passes':sum(r.get(key) is True for r in rr),'pass_percent':100*sum(r.get(key) is True for r in rr)/len(rr) if rr else None,'definition':'own DC constraints' if dc else 'all applicable AC constraints','accepted_references':sum(r.get('reference_valid') is True for r in rr)})
 save(ROOT/'loading-analysis.json',{'generated_UTC':now(),'main_feasibility':feas,'records':len(rows),'case3_records':sum(r['group'].startswith('case3') for r in rows),'note':'Descriptive, fixed finite scenarios; no confidence intervals or population generalization.'})
 csvsave(ROOT/'paper/feasibility-summary.csv',feas)
 (ROOT/'paper/figures').mkdir(exist_ok=True)
 colors={'AC-OPF':'#111111','DC-OPF':'#888888','microsoft-v1.1':'#1874b8','newer-base-v2':'#d34d39'}
 metricsets={
  'state-accuracy':[('accuracy.Pg_MW.MAE','Pg MAE (MW)'),('accuracy.Qg_MVAr.MAE','Qg MAE (MVAr)'),('accuracy.V_pu.MAE','V MAE (pu)'),('accuracy.aligned_angle_deg.MAE','Aligned angle MAE (deg)')],
  'balance':[('P_balance_MW.max_abs','Max |P residual| (MW)'),('P_balance_MW.p95_abs','p95 |P residual| (MW)'),('Q_balance_MVAr.max_abs','Max |Q residual| (MVAr)'),('Q_balance_MVAr.p95_abs','p95 |Q residual| (MVAr)')],
  'constraints':[('constraints.Pg_MW.violating_count','Pg violating units'),('constraints.Qg_MVAr.violating_count','Qg violating units'),('constraints.voltage_pu.violating_count','V violating buses'),('constraints.branch_thermal_MVA.violating_count','Thermally violating branches')],
  'state-rmse':[(f'accuracy.{k}.RMSE',lab) for k,lab in [('Pg_MW','Pg RMSE (MW)'),('Qg_MVAr','Qg RMSE (MVAr)'),('V_pu','V RMSE (pu)'),('aligned_angle_deg','Aligned angle RMSE (deg)')]],
  'P-balance':[(f'P_balance_MW.{k}',lab) for k,lab in [('max_abs','Maximum (MW)'),('mean_abs','Mean (MW)'),('p95_abs','p95 (MW)'),('violating_bus_count','P violating buses')]],
  'Q-balance':[(f'Q_balance_MVAr.{k}',lab) for k,lab in [('max_abs','Maximum (MVAr)'),('mean_abs','Mean (MVAr)'),('p95_abs','p95 (MVAr)'),('violating_bus_count','Q violating buses')]],
  'constraint-maximum':[(f'constraints.{k}.maximum',lab) for k,lab in [('Pg_MW','Pg max excess (MW)'),('Qg_MVAr','Qg max excess (MVAr)'),('voltage_pu','V max excess (pu)'),('branch_thermal_MVA','Thermal max excess (MVA)')]],
  'constraint-mean':[(f'constraints.{k}.mean_all',lab) for k,lab in [('Pg_MW','Pg mean excess (MW)'),('Qg_MVAr','Qg mean excess (MVAr)'),('voltage_pu','V mean excess (pu)'),('branch_thermal_MVA','Thermal mean excess (MVA)')]]}
 for net in ['case300','case300x2','case500goc']:
  for kind,metrics in metricsets.items():
   fig,axes=plt.subplots(4,3,figsize=(10,9),sharex=True)
   for col,group in enumerate(['P','Q','PQ']):
    for row,(key,label) in enumerate(metrics):
     ax=axes[row,col]
     for method in METHODS:
      rr=[r for r in main if r['network']==net and r['method']==method and r['group'] in ['baseline',group] and r.get(key) is not None];rr.sort(key=lambda r:max(r['absolute_P_factor'],r['absolute_Q_factor']))
      if rr:ax.plot([max(r['absolute_P_factor'],r['absolute_Q_factor']) for r in rr],[r[key] for r in rr],'.-',label=LABEL[method],color=colors[method],linewidth=1.1,markersize=3)
     if row==0:ax.set_title({'P':'P only','Q':'Q only','PQ':'P and Q'}[group])
     if col==0:ax.set_ylabel(label,fontsize=8)
     if row==3:ax.set_xlabel('Absolute loading factor')
     ax.grid(alpha=.2);ax.tick_params(labelsize=8)
   handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=4,bbox_to_anchor=(.5,.97));fig.suptitle(net+' / '+kind,y=.995);fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(ROOT/'paper/figures'/f'{net}-{kind}.png',dpi=180);fig.savefig(ROOT/'paper/figures'/f'{net}-{kind}.pdf');plt.close(fig)
 print('ANALYZED',len(rows),'records',flush=True)

if __name__=='__main__':
 baseline_tables()
 if len(sys.argv)>1 and sys.argv[1]=='loading':summary_and_plots()
