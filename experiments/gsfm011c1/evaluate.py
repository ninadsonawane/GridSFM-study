"""11B single-case approximation and original-physics metrics; no solvers/model calls."""
import sys,pathlib,json,math,hashlib,csv
ROOT=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');W=pathlib.Path('/private/tmp/gsfm011b-20261022');O=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(ROOT/'scripts/python'))
import numpy as np
from physics_metrics import evaluate,branch_flows,wrap_degrees,cost
from pypower.makeYbus import makeYbus
from pypower.makeBdc import makeBdc
read=lambda p:json.loads((O/p).read_text())
def save(p,o):(O/p).write_text(json.dumps(o,indent=2,allow_nan=False)+'\n')
c=read('input.json');ids={int(b[0]):i for i,b in enumerate(c['bus'])};ref=read('ac-native.json');base=c['baseMVA'];slack=next(i for i,b in enumerate(c['bus']) if b[1]==3)
b=np.array(c['bus'],float);e=np.array(c['branch'],float);b[:,0]=np.arange(len(b));e[:,0]=[ids[int(br[0])] for br in c['branch']];e[:,1]=[ids[int(br[1])] for br in c['branch']];Y,Yf,Yt=makeYbus(base,b,e);B,Bf,pb,pf=makeBdc(base,b,e)

def ac_residual(s):
 V=np.array(s['vm'])*np.exp(1j*np.deg2rad(s['va_deg']));inj=-np.array([complex(x[2],x[3]) for x in c['bus']]);np.add.at(inj,[ids[int(g[0])] for g in c['gen']],np.array(s['pg_mw'])+1j*np.array(s['qg_mvar']));return inj-base*V*np.conj(Y@V)
def bounds(x,lo,hi):return np.maximum(np.maximum(np.array(lo)-x,np.array(x)-hi),0)
def dstat(x):
 x=np.abs(np.array(x));return {'MAE':float(x.mean()),'RMSE':float(np.sqrt((x*x).mean())),'maximum':float(x.max())}
def b_loc(values):
 i=int(np.argmax(abs(values)));return {'original_bus_id':int(c['bus'][i][0]),'bus_area':int(c['bus'][i][6]),'bus_row_1based':i+1,'signed_value':float(values[i]),'absolute_value':float(abs(values[i]))}
def g_loc(v,x,lo,hi):
 if max(v)==0:return None
 j=int(np.argmax(v));g=c['gen'][j];return {'generator_row_1based':j+1,'original_bus_id':int(g[0]),'bus_area':int(c['bus'][ids[int(g[0])]][6]),'predicted_value':float(x[j]),'lower_limit':float(lo[j]),'upper_limit':float(hi[j]),'violation':float(v[j])}
def v_loc(v,x):
 if max(v)==0:return None
 j=int(np.argmax(v));return {'original_bus_id':int(c['bus'][j][0]),'bus_area':int(c['bus'][j][6]),'predicted_Vm_pu':x[j],'Vmin_pu':c['bus'][j][12],'Vmax_pu':c['bus'][j][11],'violation_pu':float(v[j])}
rsf,rst=branch_flows(c,ref['vm'],ref['va_deg']);rP=np.r_[np.real(rsf),np.real(rst)];points={'AC-OPF':ref,'DC-OPF':read('dc-native.json'),'Microsoft v1.1':read('microsoft-v1.1-native.json'),'Newer v2':read('newer-base-v2-native.json')}
approx=[];physical=[];locations={};busrows=[];flowrows=[];verification={}
for method,s in points.items():
 pg=np.array(s['pg_mw']);pviol=bounds(pg,[g[9] for g in c['gen']],[g[8] for g in c['gen']]);unwrapped=(np.array(s['va_deg'])-s['va_deg'][slack])-(np.array(ref['va_deg'])-ref['va_deg'][slack]);angle=np.array([wrap_degrees(x) for x in unwrapped]);isdc=method=='DC-OPF'
 if isdc:
  assert s['vm'] is None and s['qg_mvar'] is None
  f=np.array(s['pf_mw']);t=np.array(s['pt_mw']);fp=np.r_[f,t];r=-np.array([x[2]+x[4] for x in c['bus']]);np.add.at(r,[ids[int(g[0])] for g in c['gen']],pg);r-=base*(B@np.deg2rad(s['va_deg'])+pb);qviol=vv=None
  ph={'method':method,'balance_law':'DC only; AC P/Q balance N/A','max_P_imbalance_MW':float(abs(r).max()),'max_Q_imbalance_MVAr':None,'max_Pg_violation_MW':float(pviol.max()),'max_Qg_violation_MVAr':None,'max_Vm_violation_pu':None,'thermal_assessment':'N/A: all original RATE_A=0','AC_feasibility':None,'native_DC_constraints_pass':bool(abs(r).max()<=1e-3 and pviol.max()<=1e-3)}
  qmae=vmae=None;locations[method]={'P_balance_DC':b_loc(r),'Q_balance_AC':None,'Pg_bounds':g_loc(pviol,pg,[g[9] for g in c['gen']],[g[8] for g in c['gen']]),'Qg_bounds':None,'Vm_bounds':None,'AC_P_balance':None};verification[method]={'native_Qg_and_Vm_null':True,'DC_balance_pass':ph['native_DC_constraints_pass'],'flow_recomputed_max_disagreement_MW':float(abs(f-base*(Bf@np.deg2rad(s['va_deg'])+pf)).max())}
 else:
  sf,st=branch_flows(c,s['vm'],s['va_deg']);fp=np.r_[np.real(sf),np.real(st)];r=ac_residual(s);m=evaluate(c,s);save(method.replace(' ','-')+'-exact-metrics.json',m)
  assert abs(m['max_p_residual_mw']-float(abs(r.real).max()))<1e-7 and abs(m['max_q_residual_mvar']-float(abs(r.imag).max()))<1e-7
  qviol=bounds(s['qg_mvar'],[g[4] for g in c['gen']],[g[3] for g in c['gen']]);vv=bounds(s['vm'],[bb[12] for bb in c['bus']],[bb[11] for bb in c['bus']]);qmae=dstat(np.array(s['qg_mvar'])-ref['qg_mvar']);vmae=dstat(np.array(s['vm'])-ref['vm'])
  ph={'method':method,'balance_law':'Original FP64 AC Ybus; includes shunts once','max_P_imbalance_MW':float(abs(r.real).max()),'max_Q_imbalance_MVAr':float(abs(r.imag).max()),'max_Pg_violation_MW':float(pviol.max()),'max_Qg_violation_MVAr':float(qviol.max()),'max_Vm_violation_pu':float(vv.max()),'max_angle_difference_violation_deg':m['max_angle_violation_deg'],'thermal_assessment':'N/A: all original RATE_A=0','AC_feasibility':m['all_tested_constraints_pass'],'dispatch_cost_per_hour':m['generation_cost_per_hour']}
  locations[method]={'P_balance_AC':b_loc(r.real),'Q_balance_AC':b_loc(r.imag),'Pg_bounds':g_loc(pviol,pg,[g[9] for g in c['gen']],[g[8] for g in c['gen']]),'Qg_bounds':g_loc(qviol,s['qg_mvar'],[g[4] for g in c['gen']],[g[3] for g in c['gen']]),'Vm_bounds':v_loc(vv,s['vm'])}
  if method=='AC-OPF':assert m['all_tested_constraints_pass']
  verification[method]={'Ybus_matches_independent_branch_checker':True,'original_constraints_pass':m['all_tested_constraints_pass'],'source_reference_bus_id':int(c['bus'][slack][0]),'unaligned_to_aligned_angle_max_deg':float(abs(unwrapped).max()),'angle_wrapping_changed_error_max_deg':float(abs(unwrapped-angle).max())}
 ar={'method':method,'Pg_MW':dstat(pg-ref['pg_mw']),'aligned_angle_deg':dstat(angle),'active_branch_flow_MW_both_ends':dstat(fp-rP),'Qg_MVAr':qmae,'Vm_pu':vmae,'flow_definition':'DC law, Pf=-Pt; no losses' if isdc else 'Original exact AC branch equations from native Vm/angle; all original taps/shunts/parallel rows','DC_native_Qg_Vm':'N/A' if isdc else None};approx.append(ar);physical.append(ph)
 for i,bb in enumerate(c['bus']):busrows.append({'method':method,'original_bus_id':int(bb[0]),'area':int(bb[6]),'aligned_angle_error_deg':float(angle[i]),'P_imbalance_MW':float(r[i] if isdc else r[i].real),'Q_imbalance_MVAr':None if isdc else float(r[i].imag),'balance_law':'DC' if isdc else 'AC'})
 for j,br in enumerate(c['branch']):flowrows.append({'method':method,'branch_row_1based':j+1,'from_bus':int(br[0]),'to_bus':int(br[1]),'from_active_flow_MW':float(fp[j]),'to_active_flow_MW':float(fp[j+411]),'from_error_MW':float(fp[j]-rP[j]),'to_error_MW':float(fp[j+411]-rP[j+411]),'flow_law':'DC' if isdc else 'AC'})
# Record difference between API's derived flows (native epsilon/precision) and
# authoritative recomputation on ORIGINAL parameters, without replacing native outputs.
for name,method in [('microsoft-v1.1','Microsoft v1.1'),('newer-base-v2','Newer v2')]:
 raw=read(name+'-returned.json');md=read(name+'-metadata.json')['mapping'];native=points[method];sf,st=branch_flows(c,native['vm'],native['va_deg']);api=np.zeros((411,4));offset=0
 for fam,num in zip(raw['flow_edge_types'],raw['flow_edge_counts']):
  ix=md[fam+'_source_rows'];assert len(ix)==num;api[ix]=np.array([raw[k][offset:offset+num] for k in ['Pij','Qij','Pji','Qji']]).T*100;offset+=num
 want=np.array([np.real(sf),np.imag(sf),np.real(st),np.imag(st)]).T
 verification[method]['API_derived_vs_original_recomputed_flow_max_component_difference_MVA']=float(abs(api-want).max());verification[method]['native_returned_saved_unchanged_before_recomputation']=True
save('approximation.json',approx);save('physical-validity.json',physical);save('worst-locations.json',locations);save('verification.json',{'status':'PASS','scope':'one original case300; no PF completion, no numerical repair, no training, no sigmoid override, six-point loading-only 11C-1','methods':verification,'same_input_sha256':hashlib.sha256((O/'input.json').read_bytes()).hexdigest(),'AC_reference_independently_feasible':True,'DC_native_fields_not_fabricated':True})
for name,rows in [('bus-diagnostics.csv',busrows),('branch-approximation.csv',flowrows)]:
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
print('APPROXIMATION',json.dumps(approx,indent=2));print('PHYSICAL',json.dumps(physical,indent=2));print('LOCATIONS',json.dumps(locations,indent=2))
