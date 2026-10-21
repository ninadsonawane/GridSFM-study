import sys,json,math,cmath,copy,hashlib,subprocess,platform,csv
from pathlib import Path
OUT=Path(__file__).parent
STUDY=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study')
MODEL=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM')
BASE=STUDY/'results/inference/2026-10-21-base-cases'
sys.path[:0]=[str(STUDY/'scripts/python'),str(MODEL/'model')]
import numpy as np,torch
from physics_metrics import evaluate,branch_flows,cost
from gridsfm.loss import _flows_rx_bidir
from gridsfm.model import GridTransformerBackbone
def load(p):return json.loads(Path(p).read_text())
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def state(raw,base):return dict(vm=raw['V'],va_deg=[math.degrees(a) for a in raw['theta']],pg_mw=[a*base for a in raw['Pg']],qg_mvar=[a*base for a in raw['Qg']])
def native_case(obj):
    n=obj['grid']['nodes'];e=obj['grid']['edges'];md=obj['metadata'];base=float(np.asarray(obj['grid']['context']).ravel()[0])
    ids=md['bus_id_map'];c={'version':'2','baseMVA':base,'bus':[],'gen':[],'branch':[],'gencost':[],'branch_ids':[]}
    for bid,x in zip(ids,n['bus']):c['bus'].append([bid,x[1],0,0,0,0,1,1,0,x[0],1,x[3],x[2]])
    for kind,ix in [('load',(2,3)),('shunt',(5,4))]:
        for x,j in zip(n[kind],e[kind+'_link']['receivers']):
            for a,k in zip(x,ix):c['bus'][j][k]+=a*base
    for i,(x,j) in enumerate(zip(n['generator'],e['generator_link']['receivers'])):
        c['gen'].append([ids[j],x[1]*base,x[4]*base,x[6]*base,x[5]*base,x[7],x[0],1,x[3]*base,x[2]*base]+[0]*11)
        c['gencost'].append([2,0,0,3,x[8]/base**2,x[9]/base,x[10]])
    for kind in ['ac_line','transformer']:
        for x,f,t,bid in zip(e[kind]['features'],e[kind]['senders'],e[kind]['receivers'],md[kind+'_branch_ids']):
            if kind=='ac_line':row=[ids[f],ids[t],x[4],x[5],x[2]+x[3],x[6]*base,x[7]*base,x[8]*base,0,0,1,math.degrees(x[0]),math.degrees(x[1])]
            else:row=[ids[f],ids[t],x[2],x[3],x[9]+x[10],x[4]*base,x[5]*base,x[6]*base,x[7],math.degrees(x[8]),1,math.degrees(x[0]),math.degrees(x[1])]
            c['branch'].append(row);c['branch_ids'].append(str(bid))
    return c
def residual(c,s,flows=None):
    sf,st=flows or branch_flows(c,s['vm'],s['va_deg']);lookup={int(b[0]):i for i,b in enumerate(c['bus'])}
    out=np.array([complex(-b[2]-b[4]*v*v,-b[3]+b[5]*v*v) for b,v in zip(c['bus'],s['vm'])])
    for g,p,q in zip(c['gen'],s['pg_mw'],s['qg_mvar']):
        if g[7]>0:out[lookup[int(g[0])]]+=complex(p,q)
    for b,f,t in zip(c['branch'],sf,st):out[lookup[int(b[0])]]-=f;out[lookup[int(b[1])]]-=t
    return out
def stats(x):
    x=np.abs(x);return {'max':float(np.max(x)),'median':float(np.median(x)),'p95':float(np.percentile(x,95))}
def physical(c,s,reference_cost):
    m=evaluate(c,s);r=residual(c,s)
    assert abs(max(abs(r.real))-m['max_p_residual_mw'])<1e-7
    return dict(P_MW=stats(r.real),Q_MVAr=stats(r.imag),voltage_violation_pu=m['max_voltage_violation_pu'],generator_violation_mw_or_mvar=m['max_generator_component_violation_mw_or_mvar'],rated_branch_violation_mva=m['max_branch_violation_mva'],rated_branches=m['rated_active_branch_count'],angle_violation_deg=m['max_angle_violation_deg'],joint_pass=m['all_tested_constraints_pass'],cost_per_hour=m['generation_cost_per_hour'],cost_error_percent=100*abs(m['generation_cost_per_hour']-reference_cost)/abs(reference_cost))
def diagnostic_flows(c,s,mode):
    ids={int(b[0]):i for i,b in enumerate(c['bus'])};v=[a*cmath.exp(1j*math.radians(b)) for a,b in zip(s['vm'],s['va_deg'])];sf=[];st=[]
    for b in c['branch']:
        f,t=ids[int(b[0])],ids[int(b[1])];r,x=b[2:4];z2=r*r+x*x
        den=max(z2,1e-6) if mode=='loss_floor' else z2+1e-12
        y=complex(r,-x)/den;bc=1j*b[4]/2;tap=(b[8] or 1)*cmath.exp(1j*math.radians(b[9]))
        sf.append(c['baseMVA']*v[f]*(((y+bc)/abs(tap)**2)*v[f]-(y/tap.conjugate())*v[t]).conjugate())
        st.append(c['baseMVA']*v[t]*((-y/tap)*v[f]+(y+bc)*v[t]).conjugate())
    return sf,st
def actual_loss_check(c,s,expected):
    ids={int(b[0]):i for i,b in enumerate(c['bus'])};d=lambda x:torch.tensor(x,dtype=torch.float64)
    b=c['branch'];i=torch.tensor([ids[int(x[0])] for x in b]);j=torch.tensor([ids[int(x[1])] for x in b])
    flows=_flows_rx_bidir(d([math.radians(a) for a in s['va_deg']]),d(s['vm']),i,j,d([x[2] for x in b]),d([x[3] for x in b]),d([x[4]/2 for x in b]),d([x[4]/2 for x in b]),d([x[8] or 1 for x in b]),d([math.radians(x[9]) for x in b]))
    sf=np.array(expected[0]);st=np.array(expected[1]);target=[sf.real,sf.imag,st.real,st.imag]
    err=max(float(np.max(np.abs(x.numpy()*c['baseMVA']-y))) for x,y in zip(flows,target));assert err<1e-6,err
    return err
control_path=MODEL/'model/samples/case500_goc.pyg.json';obj=load(control_path);ctrl=native_case(obj)
by=obj['solution']['nodes']['bus'];gy=obj['solution']['nodes']['generator'];b=ctrl['baseMVA']
cr=dict(vm=[x[1] for x in by],va_deg=[math.degrees(x[0]) for x in by],pg_mw=[x[0]*b for x in gy],qg_mvar=[x[1]*b for x in gy])
cases=[('control-case500',ctrl,state(load(BASE/'control-case500-model-output.json'),b),cr,obj['metadata']['objective'])]
for name in ['case300','case300x2']:
    cases.append((name,load(BASE/f'{name}-input.json'),load(BASE/f'{name}-prediction.json'),load(BASE/f'{name}-reference.json'),load(BASE/f'{name}-reference-raw.json')['objective']))
mapping=load(BASE/'construction-map.json');summary={};worst={};mismatch={};node_rows=[]
for name,c,p,ref,rcost in cases:
    m=physical(c,p,rcost);rm=physical(c,ref,rcost);summary[name]={'prediction':m,'reference_reloaded':rm}
    save(name+'-input.json',c);save(name+'-reference-reloaded.json',ref)
    rr=residual(c,p);reference_rr=residual(c,ref)
    if name!='control-case500':assert rm['joint_pass']
    ids={int(b[0]):i for i,b in enumerate(c['bus'])}
    for i,bus in enumerate(c['bus']):node_rows.append(dict(case=name,bus_id=int(bus[0]),P_mw=float(rr[i].real),Q_mvar=float(rr[i].imag)))
    if name!='control-case500':
        worst[name]={}
        for kind,vals in [('P',rr.real),('Q',rr.imag)]:
            rows=[]
            for i in np.argsort(-np.abs(vals))[:10]:
                i=int(i);bus=c['bus'][i];bid=int(bus[0]);orig=(mapping['bus_map'][i] if name=='case300x2' else {'area':'original','source_external_id':bid})
                gens=[]
                for j,g in enumerate(c['gen']):
                    if int(g[0])==bid:gens.append(dict(row=j+1,predicted_pg_mw=p['pg_mw'][j],reference_pg_mw=ref['pg_mw'][j],pg_error_mw=p['pg_mw'][j]-ref['pg_mw'][j],predicted_qg_mvar=p['qg_mvar'][j],reference_qg_mvar=ref['qg_mvar'][j],qg_error_mvar=p['qg_mvar'][j]-ref['qg_mvar'][j]))
                incident=[]
                for j,br in enumerate(c['branch']):
                    if bid in [int(br[0]),int(br[1])]:
                        other=int(br[1] if int(br[0])==bid else br[0]);oi=ids[other]
                        incident.append(dict(branch_id=c.get('branch_ids',list(range(1,len(c['branch'])+1)))[j],from_bus=int(br[0]),to_bus=int(br[1]),other_original_bus=(mapping['bus_map'][oi]['source_external_id'] if name=='case300x2' else other),r_pu=br[2],x_pu=br[3],charging_b_total_pu=br[4],tap=br[8] or 1,shift_deg=br[9],rateA_mva=br[5],loss_admittance_retained_fraction=min(1,(br[2]**2+br[3]**2)/1e-6)))
                rows.append(dict(matrix_row_1based=i+1,bus_id=bid,original_bus_id=orig['source_external_id'],area=orig['area'],P_residual_mw=float(rr[i].real),Q_residual_mvar=float(rr[i].imag),predicted_vm=p['vm'][i],reference_vm=ref['vm'][i],predicted_va_deg=p['va_deg'][i],reference_va_deg=ref['va_deg'][i],Pd_mw=bus[2],Qd_mvar=bus[3],GS_mw_at_unit_voltage=bus[4],BS_mvar_at_unit_voltage=bus[5],generator_errors=gens,incident_branches=incident))
            worst[name][kind]=rows
    affected=[]
    for j,br in enumerate(c['branch']):
        z2=br[2]**2+br[3]**2
        if z2<1e-6:affected.append(dict(row=j+1,branch_id=c.get('branch_ids',list(range(1,len(c['branch'])+1)))[j],from_bus=int(br[0]),to_bus=int(br[1]),r=br[2],x=br[3],admittance_retained_fraction=z2/1e-6))
    mismatch[name]={'loss_floor_affected_branches':affected}
    for state_name,s in [('prediction',p),('reference',ref)]:
        exact=residual(c,s);dct={}
        for mode in ['loss_floor','forward_epsilon']:
            f=diagnostic_flows(c,s,mode);r=residual(c,s,f);ef=branch_flows(c,s['vm'],s['va_deg'])
            dct[mode]=dict(P_MW=stats(r.real),Q_MVAr=stats(r.imag),max_bus_P_residual_difference_MW=float(max(abs((r-exact).real))),max_bus_Q_residual_difference_MVAr=float(max(abs((r-exact).imag))),max_branch_complex_flow_difference_MVA=float(max(max(abs(a-b) for a,b in zip(f[0],ef[0])),max(abs(a-b) for a,b in zip(f[1],ef[1])))))
            if mode=='loss_floor':dct[mode]['actual_torch_loss_function_double_precision_max_flow_disagreement_MVA']=actual_loss_check(c,s,f)
        mismatch[name][state_name]=dct
save('physical-summary.json',summary);save('worst-buses.json',worst);save('physics-mismatch.json',mismatch)
with (OUT/'nodal-residuals.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(node_rows[0]));w.writeheader();w.writerows(node_rows)
evidence={'study_commit':subprocess.check_output(['git','-C',str(STUDY),'rev-parse','HEAD'],text=True).strip(),'model_commit':subprocess.check_output(['git','-C',str(MODEL),'rev-parse','HEAD'],text=True).strip(),'checkpoint_sha256':load(BASE/'environment.json')['checkpoint_sha256'],'hardware':'Apple M5 Pro,18 CPU cores,64 GB RAM; system_profiler SPHardwareDataType -detailLevel mini','existing_evidence':{str(BASE/x):hashlib.sha256((BASE/x).read_bytes()).hexdigest() for x in ['checks.json','summary.json','provenance.json','analyze.py','verify_inference.py']},'reused_input_hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [control_path]+list(BASE.glob('*-input.json'))+list(BASE.glob('*-prediction.json'))+list(BASE.glob('*-model-output.json'))},'control_reference_source':{'path':str(control_path),'upstream_case':'pglib_opf_case500_goc.m, per shipped samples/README.md','metadata':{k:v for k,v in obj['metadata'].items() if not isinstance(v,list)},'producing_solver_version':'not recorded in shipped sample; do not infer exact solver or original source revision'},'checks':{'reused_prior_checks':str(BASE/'checks.json'),'units':'Power in saved physical states MW/MVAr = native pu*100MVA; angles radians->degrees; costs reverse system-base scaling','ordering':'original matrix rows preserved for case300 and source-row/area maps for case300x2; generator order unchanged; full prior checks linked','reference_reload':'serialized physical references reloaded and independently checked here; full numerical native reverse/export checks linked to previous analyze.py','gate_B':'pending control reference feasibility and physics review'}}
save('provenance-A.json',evidence)
print(json.dumps(summary,indent=2));print('affected branches',[(k,len(v['loss_floor_affected_branches'])) for k,v in mismatch.items()]);print('worst',[(k,v['P'][0]['original_bus_id'],v['Q'][0]['original_bus_id']) for k,v in worst.items()])
