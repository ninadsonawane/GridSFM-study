"""13: frozen admissible structure, checked Jacobians, separate accuracy/sensitivity/cancellation."""
from electrical import *
import datetime,collections,itertools
from pypower.dSbus_dV import dSbus_dV
O=R/'results/diagnosis/GSFM-013/20261023-accuracy-sensitivity';assert not O.exists(),'Refusing overwrite';O.mkdir(parents=True);B=R/'results/comparisons/GSFM-011B/20261022-original-case300';C=R/'results/comparisons/GSFM-011C-1/20261022-loading-only';T=R/'results/comparisons/GSFM-012/20261023-frozen-two-copy';datasets=[('original300','base',B)]+[('original300',f'load{x:.2f}',C/f'load-{x:.2f}') for x in [.8,.9,.95,1.03,1.06]]+[('constructed600',n,T/n) for n in ['S0','Splus','Sminus']];basecases={n:read(d/'input.json') for n,s,d in datasets if s in ['base','S0']};features={};pairs=[];homologous=[];begin=datetime.datetime.now(datetime.timezone.utc).isoformat()
# Freeze source-only admissibility BEFORE reading any predicted states or residual outcomes.
for network,c in basecases.items():
 ids,b,e,f,t=matrices(c);neighbors=[set() for _ in b];inc=[[] for _ in b];gc=collections.Counter(ids[int(g[0])] for g in c['gen'] if g[7]>0)
 for j,(u,v) in enumerate(zip(f,t)):
  if e[j,10]>0:neighbors[u].add(v);neighbors[v].add(u);inc[u].append(j);inc[v].append(j)
 ff=[]
 for i,z in enumerate(b):
  area,original=identity(c,i);transformers=sum((e[j,8] or 1)!=1 or e[j,9]!=0 or b[f[j],9]!=b[t[j],9] for j in inc[i]);types=collections.Counter(int(b[k,1]) for k in neighbors[i]);zz=[abs(complex(e[j,2],e[j,3])) for j in inc[i]];ff.append({'network':network,'index':i,'bus_id':int(c['bus'][i][0]),'area':area,'original_id':original,'type':int(z[1]),'gen_count':gc[i],'kV':z[9],'zero_injection':gc[i]==0 and all(z[k]==0 for k in [2,3,4,5]),'has_shunt':z[4]!=0 or z[5]!=0,'transformer_count':int(transformers),'parallel_excess':len(inc[i])-len(neighbors[i]),'degree':len(inc[i]),'neighbor_degree':len(neighbors[i]),'Pd':z[2],'Qd':z[3],'Gs':z[4],'Bs':z[5],'neighbor_types':dict(types),'min_abs_z':min(zz),'median_abs_z':float(np.median(zz)),'max_abs_admittance':1/min(zz),'incident_impedances':zz,'neighbors':sorted(neighbors[i]),'incident_rows':inc[i]})
 features[network]=ff
 for i,j in itertools.combinations(range(len(b)),2):
  a,z=ff[i],ff[j]
  if a['area']!=z['area']:continue
  exact=['type','gen_count','kV','zero_injection','has_shunt','transformer_count','parallel_excess']
  if any(a[k]!=z[k] for k in exact):continue
  if abs(a['degree']-z['degree'])>1 or abs(a['neighbor_degree']-z['neighbor_degree'])>1:continue
  pd=abs(a['Pd']-z['Pd'])/max(10,abs(a['Pd']),abs(z['Pd']));qd=abs(a['Qd']-z['Qd'])/max(10,abs(a['Qd']),abs(z['Qd']))
  if pd>.25 or qd>.25:continue
  dist=pd+qd+abs(a['degree']-z['degree'])/max(1,a['degree'],z['degree'])+abs(a['neighbor_degree']-z['neighbor_degree'])/max(1,a['neighbor_degree'],z['neighbor_degree']);pairs.append({'network':network,'i':i,'j':j,'bus_i':a['bus_id'],'bus_j':z['bus_id'],'area':a['area'],'normalized_source_distance':dist,'Pd_relative_distance':pd,'Qd_relative_distance':qd,'impedance_used_for_matching':False})
 if len(b)==600:
  for i in range(300):
   a,z=ff[i],ff[i+300];excluded=a['type']!=z['type'];assert all(a[k]==z[k] for k in ['gen_count','kV','zero_injection','has_shunt','transformer_count','parallel_excess','degree','neighbor_degree','Pd','Qd','Gs','Bs','incident_impedances']);homologous.append({'source_id':a['original_id'],'A_bus_id':a['bus_id'],'B_bus_id':z['bus_id'],'exclude_REF_PV_pair':excluded,'onehop_type_pattern_differs':a['neighbor_types']!=z['neighbor_types']})
csvsave(O/'admissible-pairs.csv',pairs);save(O/'source-bus-features.json',features);save(O/'homologous-pairs.json',homologous);save(O/'matching-rule.json',{'started_UTC':begin,'frozen_before_outcomes':True,'pair_file_sha256':sha(O/'admissible-pairs.csv'),'exact_match':['bus_type','online_generator_count','base_kV','structural_zero_injection','nonzero_shunt_presence','incident_transformer_count','parallel_excess'],'degree_and_unique_neighbors_caliper':1,'signed_Pd_Qd_caliper':.25,'load_distance_denominator':'max(10,abs(a),abs(b))','no_impedance_sensitivity_or_prediction_for_admissibility':True,'accuracy_example_definition':'All local/onehop absVm errors<=.001pu, all incident angle-difference errors<=.001rad, and local generator Pg/Qg errors<=.001MW/MVAr if generators exist','high_low_imbalance_rule':'top/bottom floor(N/4), absolute component then external-ID tie break; networks/releases/P/Q separate'})
allrows=[];jacchecks=[];sourcehashes=[];base_lookup={};selections=[];eligible=[];unmatched=[]
for network,scenario,D in datasets:
 c=read(D/'input.json');ref=read(D/'ac-native.json');assert evaluate(c,ref)['all_tested_constraints_pass'];ids,b,e,f,t=matrices(c);Y,*_=makeYbus(c['baseMVA'],b,e);n=len(b);slack=next(i for i,z in enumerate(b) if z[1]==3);cols=[j for j in range(n) if j!=slack];vm=np.array(ref['vm']);va=np.deg2rad(ref['va_deg']);V=vm*np.exp(1j*va);Jv,Ja=dSbus_dV(Y,V);Jv=c['baseMVA']*Jv.toarray();Ja=c['baseMVA']*Ja.toarray()[:,cols]
 def injection(v,a):
  vv=v*np.exp(1j*a);return c['baseMVA']*vv*np.conj(Y@vv)
 def finite(h,block):
  cc=range(n) if block=='V' else cols;out=np.empty((n,len(cc)),complex)
  for k,j in enumerate(cc):
   vp=vm.copy();vn=vm.copy();ap=va.copy();an=va.copy()
   if block=='V':vp[j]+=h;vn[j]-=h
   else:ap[j]+=h;an[j]-=h
   out[:,k]=(injection(vp,ap)-injection(vn,an))/(2*h)
  return out
 for block,J in [('V',Jv),('theta',Ja)]:
  fd=finite(1e-6,block);half=finite(5e-7,block);rel=float(np.linalg.norm(fd-half)/max(np.linalg.norm(half),1e-20));err=np.max(abs(fd-half),axis=1);tol=1e-3+1e-4*np.max(abs(half),axis=1);analytic=float(np.linalg.norm(J-half)/max(np.linalg.norm(half),1e-20));assert rel<1e-4 and np.all(err<=tol) and analytic<1e-4,(network,scenario,block,rel,analytic);jacchecks.append({'network':network,'scenario':scenario,'block':block,'relative_Frobenius_halfstep':rel,'max_row_entry_disagreement':float(max(err)),'all_inspected_rows_pass':True,'analytic_vs_halfstep_relative':analytic,'units':'MW/MVAr perpu' if block=='V' else 'MW/MVAr perrad','fixed_reference_angle_column_excluded':True})
 rr=terms(c,ref);ff=features[network];sourcehashes.append({'network':network,'scenario':scenario,'input_sha256':sha(D/'input.json'),'reference_sha256':sha(D/'ac-native.json')});gm={i:[j for j,g in enumerate(c['gen']) if g[7]>0 and ids[int(g[0])]==i] for i in range(n)}
 for release in ['newer-base-v2','microsoft-v1.1']:
  s=read(D/(release+'-native.json'));tr=terms(c,s);dxv=np.array(s['vm'])-vm;dxa=(np.deg2rad(s['va_deg'])-np.deg2rad(s['va_deg'][slack]))-(va-va[slack]);linear=Jv@dxv+Ja@dxa[cols];exact=injection(np.array(s['vm']),np.deg2rad(s['va_deg']))-injection(vm,va);remainder=exact-linear;flowf=tr['sf']-rr['sf'];flowt=tr['st']-rr['st'];angerr=(np.array(s['va_deg'])[f]-np.array(s['va_deg'])[t])-(np.array(ref['va_deg'])[f]-np.array(ref['va_deg'])[t]);angerr=(angerr+180)%360-180;sourcehashes[-1][release+'_native_sha256']=sha(D/(release+'-native.json'));rows=[]
  for i,z in enumerate(b):
   feature=ff[i];neighbors=feature['neighbors'];ix=feature['incident_rows'];gens=gm[i];gperr=[s['pg_mw'][j]-ref['pg_mw'][j] for j in gens];gqerr=[s['qg_mvar'][j]-ref['qg_mvar'][j] for j in gens];vneigh=abs(dxv[neighbors]);neighmax=max(np.r_[abs(dxv[i]),vneigh]);anglemax=max(abs(angerr[ix]))*np.pi/180;row={'network':network,'scenario':scenario,'release':release,'bus_id':int(c['bus'][i][0]),'area':feature['area'],'original_id':feature['original_id'],'Vm_signed_error_pu':float(dxv[i]),'Vm_absolute_error_pu':float(abs(dxv[i])),'angle_reference_aligned_error_deg':float((np.rad2deg(dxa[i])+180)%360-180),'onehop_Vm_error_mean_pu':float(vneigh.mean()),'onehop_Vm_error_max_pu':float(vneigh.max()),'incident_angle_difference_error_max_deg':float(max(abs(angerr[ix]))),'incident_both_end_P_error_MAE':float(np.mean(abs(np.r_[flowf.real[ix],flowt.real[ix]]))),'incident_both_end_Q_error_MAE':float(np.mean(abs(np.r_[flowf.imag[ix],flowt.imag[ix]]))),'generator_Pg_errors':json.dumps(gperr) if gens else None,'generator_Qg_errors':json.dumps(gqerr) if gens else None,'generation_P_error_MW':None if not gens else float(sum(gperr)),'generation_Q_error_MVAr':None if not gens else float(sum(gqerr)),'genuinely_accurate_neighborhood_under_declared_box':bool(neighmax<=.001 and anglemax<=.001 and max([abs(x) for x in gperr+gqerr],default=0)<=.001),'min_incident_abs_z':feature['min_abs_z']}
   for co,part in [('P','real'),('Q','imag')]:
    ge=gperr if co=='P' else gqerr;be=[-float(getattr(flowf[j] if f[j]==i else flowt[j],part)) for j in ix];se=-float(getattr(tr['shunt'][i]-rr['shunt'][i],part));cc=ge+be+[se];net=sum(cc);gross=sum(abs(x) for x in cc);assert abs(net-getattr(tr['r'][i]-rr['r'][i],part))<1e-6;bg=sum(abs(x) for x in be);bn=abs(sum(be));blocks=[sum(ge),sum(be),se];blockgross=sum(abs(x) for x in blocks);row.update({co+'_native_residual':float(getattr(tr['r'][i],part)),co+'_residual_error':float(net),co+'_network_injection_error':float(getattr(exact[i],part)),co+'_Jdx':float(getattr(linear[i],part)),co+'_nonlinear_remainder':float(getattr(remainder[i],part)),co+'_H_V_0_001pu':float(sum(abs(getattr(Jv[i],part)))*.001),co+'_H_theta_0_001rad':float(sum(abs(getattr(Ja[i],part)))*.001),co+'_gross_individual_error':float(gross),co+'_net_error':float(abs(net)),co+'_cancellation':None if gross<=.001 else float(1-abs(net)/gross),co+'_branch_only_gross':float(bg),co+'_branch_only_net':float(bn),co+'_branch_only_cancellation':None if bg<=.001 else float(1-bn/bg),co+'_block_grouped_gross':float(blockgross),co+'_block_grouped_cancellation':None if blockgross<=.001 else float(1-abs(net)/blockgross),co+'_generation_contribution':float(sum(ge)),co+'_positive_branch_contributions':float(sum(max(x,0) for x in be)),co+'_negative_branch_contributions':float(sum(min(x,0) for x in be)),co+'_shunt_contribution':float(se)})
   rows.append(row)
  # Separate classifications; no composite prediction/imbalance score.
  for key in ['P_native_residual','Q_native_residual','Vm_absolute_error_pu','onehop_Vm_error_mean_pu','incident_angle_difference_error_max_deg']:
   low=set(sorted(range(n),key=lambda i:(abs(rows[i][key]),int(c['bus'][i][0])))[:n//4]);high=set(sorted(range(n),key=lambda i:(-abs(rows[i][key]),int(c['bus'][i][0])))[:n//4])
   for i,row in enumerate(rows):row[key+'_quartile_class']='low' if i in low else ('high' if i in high else 'middle')
  allrows+=rows
  if scenario in ['base','S0']:
   for i,row in enumerate(rows):base_lookup[(network,release,int(c['bus'][i][0]))]=row
   pp=[x for x in pairs if x['network']==network]
   for co in ['P','Q']:
    matches=[]
    for pair in pp:
     a,z=rows[pair['i']],rows[pair['j']];ca=a[co+'_native_residual_quartile_class'];cz=z[co+'_native_residual_quartile_class']
     if {ca,cz}!={'high','low'}:continue
     high,low=(a,z) if ca=='high' else (z,a);match={'network':network,'release':release,'component':co,'high_bus':high['bus_id'],'low_bus':low['bus_id'],'normalized_source_distance':pair['normalized_source_distance']};matches.append(match)
    eligible+=matches;matches.sort(key=lambda x:(x['normalized_source_distance'],x['high_bus'],x['low_bus']));pairedHigh={x['high_bus'] for x in matches}
    for row in rows:
     if row[co+'_native_residual_quartile_class']=='high' and row['bus_id'] not in pairedHigh:unmatched.append({'network':network,'release':release,'component':co,'bus_id':row['bus_id'],'original_id':row['original_id'],'area':row['area'],'native_residual':row[co+'_native_residual'],'named_hotspot':row['original_id'] in [238,231,137]})
 print('ANALYZED',network,scenario,'Jacobians PASS',flush=True)
for rel in ['newer-base-v2','microsoft-v1.1']:
 for co in ['P','Q']:
  candidates=[x for x in eligible if x['release']==rel and x['component']==co];candidates.sort(key=lambda x:(x['normalized_source_distance'],x['high_bus'],x['low_bus'],x['network']));selections+=candidates[:6]
csvsave(O/'bus-decomposition.csv',allrows);save(O/'jacobian-checks.json',jacchecks);csvsave(O/'eligible-high-low-pairs.csv',eligible);csvsave(O/'matched-examples.csv',selections);csvsave(O/'unmatched-hotspots.csv',unmatched)
tracking=[]
for p in selections:
 for row in allrows:
  if row['network']==p['network'] and row['release']==p['release'] and row['bus_id'] in [p['high_bus'],p['low_bus']]:tracking.append(dict(pair_high=p['high_bus'],pair_low=p['low_bus'],pair_component=p['component'],**row))
csvsave(O/'load-tracking.csv',tracking)
homo=[]
for pair in homologous:
 if pair['exclude_REF_PV_pair']:continue
 for rel in ['newer-base-v2','microsoft-v1.1']:
  a=base_lookup[('constructed600',rel,pair['A_bus_id'])];z=base_lookup[('constructed600',rel,pair['B_bus_id'])];homo.append({**pair,'release':rel,'A_Q_residual':a['Q_native_residual'],'B_Q_residual':z['Q_native_residual'],'A_P_residual':a['P_native_residual'],'B_P_residual':z['P_native_residual'],'A_Vm_error':a['Vm_signed_error_pu'],'B_Vm_error':z['Vm_signed_error_pu']})
csvsave(O/'homologous-comparison.csv',homo);save(O/'gates.json',{'status':'PASS','matching_frozen_before_outcomes':True,'all_Jacobian_halfstep_and_analytic_checks_pass':True,'source_state_hashes':sourcehashes,'network_scenarios':len(datasets),'release_state_count':len(datasets)*2,'original_110_reference_dependent_rows':0,'admissible_pairs':len(pairs),'eligible_high_low_pairs':len(eligible),'selected_example_pairs':len(selections),'all_native_reference_Ybus_branch_gates_pass':True,'new_inference_solves_training':0,'started_UTC':begin,'finished_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()});print('EXPERIMENT13 ANALYSIS COMPLETE',len(pairs),'admissible',len(eligible),'eligible',len(selections),'examples',flush=True)
