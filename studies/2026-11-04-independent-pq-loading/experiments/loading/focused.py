"""Case-3 mechanism accounting and predeclared finite differences."""
from study import *
from analyze import METHODS,LABEL
def state(d,method):return read(d/({'AC-OPF':'ac-native.json','DC-OPF':'dc-native.json'}.get(method,method+'-native.json')))
def locate(net,group,p,q):
 return ROOT/'results'/f'{net}-{group}-p{p:.4f}-q{q:.4f}'
def case3():
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 a=locate('case300','case3-PQ',.93,.93);b=locate('case300','case3-PQ',.94,.94);ca=read(a/'input.json');cb=read(b/'input.json');summ=[]
 out=ROOT/'paper/case3';out.mkdir(exist_ok=True)
 for method in ['AC-OPF','microsoft-v1.1','newer-base-v2']:
  sa=state(a,method);sb=state(b,method);ta=terms(ca,sa);tb=terms(cb,sb);ar=abs(ta['r'].imag);br=abs(tb['r'].imag);delta=br-ar
  rows=[{'bus_id':int(ca['bus'][i][0]),'Qabs_093':ar[i],'Qabs_094':br[i],'Qabs_change':delta[i],'V_093':sa['vm'][i],'V_094':sb['vm'][i],'signed_Qres_change':(tb['r']-ta['r'])[i].imag,'Qgen_change':(tb['gen']-ta['gen'])[i].imag,'Qd_change':(tb['demand']-ta['demand'])[i].imag,'Qshunt_change':(tb['shunt']-ta['shunt'])[i].imag,'Qbranch_out_change':(tb['out']-ta['out'])[i].imag} for i in range(len(ar))]
  csvsave(out/(LABEL[method]+'-all-bus-changes.csv'),sorted(rows,key=lambda x:x['Qabs_change']))
  buses=[235,238];idx=[next(i for i,x in enumerate(ca['bus']) if x[0]==bid) for bid in buses]
  near=set(buses)
  edges=[]
  for j,e in enumerate(ca['branch']):
   if int(e[0]) in buses or int(e[1]) in buses:
    near.update(map(int,e[:2]));edges.append({'branch_row':j+1,'from_bus':int(e[0]),'to_bus':int(e[1]),'r_pu':e[2],'x_pu':e[3],'b_pu':e[4],'Qf_093':ta['sf'][j].imag,'Qf_094':tb['sf'][j].imag,'Qt_093':ta['st'][j].imag,'Qt_094':tb['st'][j].imag})
  csvsave(out/(LABEL[method]+'-neighbor-branches.csv'),edges)
  csvsave(out/(LABEL[method]+'-neighbor-buses.csv'),[r for r in rows if r['bus_id'] in near])
  csvsave(out/(LABEL[method]+'-neighbor-generators.csv'),[{'generator_row':j+1,'bus_id':int(g[0]),'Qg_093':sa['qg_mvar'][j],'Qg_094':sb['qg_mvar'][j],'Qmin':g[4],'Qmax':g[3],'online':bool(g[7]>0)} for j,g in enumerate(ca['gen']) if int(g[0]) in near])
  summary={'method':method,'Q_093':dist(ar),'Q_094':dist(br),'improving_bus_count':int(sum(delta<-1e-6)),'worsening_bus_count':int(sum(delta>1e-6)),'unchanged_at_1e-6_MVAr':int(sum(abs(delta)<=1e-6)),'summed_abs_Q_change_MVAr':float(sum(delta)),'buses235_238_abs_Q_change_MVAr':float(sum(delta[idx])),'other_buses_abs_Q_change_MVAr':float(sum(delta)-sum(delta[idx])),'top_improvements':sorted(rows,key=lambda r:r['Qabs_change'])[:5],'top_worsening':sorted(rows,key=lambda r:r['Qabs_change'],reverse=True)[:5],'total_Qg_093':sum(sa['qg_mvar']),'total_Qg_094':sum(sb['qg_mvar'])}
  # Exact branch 321 reactive-flow decomposition, retaining series conductance.
  j=320;e=ca['branch'][j];assert e[:2]==[235.,238.] and e[8] in (0,1) and e[9]==0
  fi,ti=idx
  def qparts(s):
   vf,vt=s['vm'][fi],s['vm'][ti];ang=np.deg2rad(s['va_deg'][fi]-s['va_deg'][ti]);y=1/complex(e[2],e[3]);g,bb=y.real,y.imag
   return np.array([v*ca['baseMVA'] for v in [-bb*vt*(vt-vf),bb*vt*vf*(np.cos(ang)-1)+g*vt*vf*np.sin(ang),-e[4]/2*vt*vt]])
  qa=qparts(sa);qb=qparts(sb);assert abs(sum(qa)-ta['st'][j].imag)<1e-6;assert abs(sum(qb)-tb['st'][j].imag)<1e-6
  summary['branch321_to_end_Q_change_decomposition_MVAr']={'voltage_gap':qb[0]-qa[0],'angle':qb[1]-qa[1],'charging':qb[2]-qa[2],'total':sum(qb-qa)}
  summ.append(summary)
 save(out/'case3-summary.json',summ)
 pts=[s for s in read(ROOT/'scenario-plan.json')['scenarios'] if s['group']=='case3-PQ'];pts.sort(key=lambda s:s['absolute_P_factor'])
 fig,axes=plt.subplots(2,2,figsize=(7,5.5))
 for method in ['microsoft-v1.1','newer-base-v2']:
  x=[];vals=[[],[],[],[]]
  for p in pts:
   d=ROOT/'results'/p['id'];c=read(d/'input.json');s=state(d,method);m,*_=evaluate(c,s,method);i=next(i for i,bus in enumerate(c['bus']) if bus[0]==235);x.append(p['absolute_P_factor'])
   for ar,v in zip(vals,[m['Q_balance_MVAr']['max_abs'],m['Q_balance_MVAr']['p95_abs'],m['Q_balance_MVAr']['violating_bus_count'],s['vm'][i]]):ar.append(v)
  for ax,y in zip(axes.flat,vals):ax.plot(x,y,'.-',label=LABEL[method])
 for ax,label in zip(axes.flat,['Maximum |Q mismatch| (MVAr)','p95 |Q mismatch| (MVAr)','Q violating buses','Voltage at bus 235 (pu)']):ax.set_ylabel(label);ax.set_xlabel('Absolute P and Q loading factor');ax.grid(alpha=.2)
 axes[0,0].legend();fig.tight_layout();fig.savefig(ROOT/'paper/figures/case3.png',dpi=220);fig.savefig(ROOT/'paper/figures/case3.pdf');plt.close(fig)
 print('CASE3 ANALYZED',flush=True)

def active_set(c,s):
 g=np.array(c['gen']);b=np.array(c['bus']);e=np.array(c['branch']);out=set()
 for key,a,lo,hi,tol in [('Pg',s['pg_mw'],g[:,9],g[:,8],1e-3),('Qg',s['qg_mvar'],g[:,4],g[:,3],1e-3),('V',s['vm'],b[:,12],b[:,11],1e-4)]:
  for i,v in enumerate(a):
   if key!='V' and g[i,7]<=0:continue
   if abs(v-lo[i])<=tol:out.add(f'{key}:lower:{i+1}')
   if abs(v-hi[i])<=tol:out.add(f'{key}:upper:{i+1}')
 tr=terms(c,s)
 for i in range(len(e)):
  if e[i,10]>0 and e[i,5]>0 and abs(max(abs(tr['sf'][i]),abs(tr['st'][i]))-e[i,5])<=1e-3:out.add(f'thermal:{i+1}')
 _,_,_,f,t=matrices(c);va=np.array(s['va_deg']);da=va[f]-va[t]
 for i,z in enumerate(e):
  if z[10]<=0 or (z[11]==0 and z[12]==0):continue
  if z[11]>-360 and abs(da[i]-z[11])<=1e-3:out.add(f'angle:lower:{i+1}')
  if z[12]<360 and abs(da[i]-z[12])<=1e-3:out.add(f'angle:upper:{i+1}')
 return out

def sensitivity():
 rows=[];active=[];details=[]
 for net in ['case300','case300x2','case500goc']:
  for component in ['P','Q']:
   pairs=[(1.,1.005,'sensitivity-'+component),(1.,1.01,component),(1.01,1.02,component)]
   for left,right,group in pairs:
    da=ROOT/'results'/f'{net}-base' if left==1. else locate(net,component,left if component=='P' else 1.,left if component=='Q' else 1.)
    db=locate(net,group,right if component=='P' else 1.,right if component=='Q' else 1.);h=right-left
    if not (da/'ac-native.json').exists() or not (db/'ac-native.json').exists():
     rows.append({'network':net,'component':component,'left':left,'right':right,'status':'UNKNOWN_REFERENCE'});continue
    ca=read(da/'input.json');cb=read(db/'input.json');ra=state(da,'AC-OPF');rb=state(db,'AC-OPF');aa=active_set(ca,ra);ab=active_set(cb,rb);active.append({'network':net,'component':component,'left':left,'right':right,'added':sorted(ab-aa),'removed':sorted(aa-ab)})
    for method in ['microsoft-v1.1','newer-base-v2']:
     sa=state(da,method);sb=state(db,method)
     for variable,tol in [('vm',1e-6),('pg_mw',1e-3),('qg_mvar',1e-3)]:
      idx=np.arange(len(ca['bus'])) if variable=='vm' else np.flatnonzero(np.array(ca['gen'])[:,7]>0)
      a=np.array(sa[variable])[idx];b=np.array(sb[variable])[idx];r=np.array(ra[variable])[idx];s=np.array(rb[variable])[idx];pred=b-a;ref=s-r;eligible=abs(ref)>tol
      direction=(np.sign(pred[eligible])==np.sign(ref[eligible]))&(abs(pred[eligible])>tol)
      row={'network':net,'component':component,'left':left,'right':right,'h':h,'method':method,'variable':variable,'count':len(idx),'baseline_MAE':float(abs(a-r).mean()),'response_delta_MAE':float(abs(pred-ref).mean()),'response_derivative_MAE':float(abs((pred-ref)/h).mean()),'response_derivative_RMSE':float(np.sqrt(np.mean(((pred-ref)/h)**2))),'reference_derivative_L2':float(np.linalg.norm(ref/h)),'model_to_reference_L2_ratio':float(np.linalg.norm(pred)/np.linalg.norm(ref)) if np.linalg.norm(ref)>0 else None,'direction_eligible_count':int(sum(eligible)),'direction_agreement_count':int(sum(direction)),'direction_agreement_percent':100*float(np.mean(direction)) if any(eligible) else None,'reference_response_threshold':tol,'reference_constraint_changes':len(ab-aa)+len(aa-ab),'total_reference_delta':float(sum(ref)),'total_model_delta':float(sum(pred)),'status':'CHECKED_REFERENCE_PAIR'};rows.append(row)
      for k,i in enumerate(idx):details.append({'network':net,'component':component,'left':left,'right':right,'method':method,'variable':variable,'row_1based':int(i)+1,'reference_delta':ref[k],'model_delta':pred[k],'reference_derivative':ref[k]/h,'model_derivative':pred[k]/h,'baseline_offset':a[k]-r[k]})
 save(ROOT/'paper/sensitivity-summary.json',rows);save(ROOT/'paper/reference-constraint-changes.json',active);csvsave(ROOT/'paper/sensitivity-summary.csv',rows);csvsave(ROOT/'paper/sensitivity-details.csv',details)
 # Step-size consistency is reported explicitly, without selecting a favorable h.
 stability=[]
 for r in rows:
  if r.get('left')!=1. or abs(r.get('h',0)-.005)>1e-8:continue
  other=next(x for x in rows if all(x.get(k)==r.get(k) for k in ['network','component','method','variable']) and x['left']==1. and abs(x['h']-.01)<1e-8)
  stability.append({**{k:r[k] for k in ['network','component','method','variable']},'h005_derivative_RMSE':r['response_derivative_RMSE'],'h010_derivative_RMSE':other['response_derivative_RMSE'],'h005_direction_percent':r['direction_agreement_percent'],'h010_direction_percent':other['direction_agreement_percent'],'constraint_changes_h005':r['reference_constraint_changes'],'constraint_changes_h010':other['reference_constraint_changes']})
 save(ROOT/'paper/step-size-check.json',stability);print('SENSITIVITY ANALYZED',len(rows),'comparisons',flush=True)

if __name__=='__main__':case3() if sys.argv[1]=='case3' else sensitivity()
