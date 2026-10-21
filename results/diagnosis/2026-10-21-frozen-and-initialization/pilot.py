import time
T_PROCESS=time.perf_counter()
import sys,json,math,copy,subprocess,hashlib,csv,statistics,traceback
from pathlib import Path
OUT=Path(__file__).parent;STUDY=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');MODEL=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM');BASE=STUDY/'results/inference/2026-10-21-base-cases'
assert json.loads((OUT/'A-gate.json').read_text())['B_authorized']
sys.path[:0]=[str(STUDY/'scripts/python'),str(MODEL/'model')]
import torch
from gridsfm import load_model,predict
from gridsfm_convert import convert
from physics_metrics import evaluate,branch_flows
torch.manual_seed(0);torch.set_num_threads(4);torch.use_deterministic_algorithms(True)
def save(path,obj):Path(path).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def load(path):return json.loads(Path(path).read_text())
ART=OUT/'pilot';ART.mkdir(exist_ok=True)
attempt=time.strftime('%H%M%S');cold={'python_import_seconds':time.perf_counter()-T_PROCESS,'timing_policy':'persistent Python model and Julia server; setup/import/JIT first calls reported separately; timed repeats rebuild solver model and recompute GridSFM conversion/preprocessing/inference, reuse model and topology caches; no fallback'}
t=time.perf_counter();model=load_model(MODEL/'model/checkpoints/gridsfm_open_v1.1.pt',device='cpu');cold['checkpoint_load_seconds']=time.perf_counter()-t
source=load(BASE/'case300-input.json');case_paths={}
for lam in [.9,.95,1.,1.05,1.1]:
    tag=f'{round(lam*100):03d}';c=copy.deepcopy(source)
    for b in c['bus']:b[2]*=lam;b[3]*=lam
    path=ART/f'case{tag}.json';save(path,c);case_paths[lam]=path
    lines=[f'function mpc = case{tag}',"mpc.version = '2';",f'mpc.baseMVA = {c["baseMVA"]};']
    for key in ['bus','gen','branch','gencost']:
        lines.append(f'mpc.{key} = [');lines += [' '.join(format(v,'.17g') for v in row)+';' for row in c[key]];lines.append('];')
    (ART/f'case{tag}.m').write_text('\n'.join(lines)+'\n')
stderr=(ART/f'{attempt}-julia-stderr.log').open('w')
t=time.perf_counter();server=subprocess.Popen(['/Users/ninadsonawane/julia/bin/julia','--startup-file=no','--project='+str(MODEL/'power_grid/US/topology_solver_pipeline'),str(OUT/'solver_server.jl')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=stderr,text=True,bufsize=1)
readyline=server.stdout.readline();cold['julia_startup_ready_seconds']=time.perf_counter()-t
if not readyline:raise RuntimeError('Julia startup failed; see '+str(stderr.name))
cold['server']=json.loads(readyline);save(ART/f'{attempt}-cold-setup.json',cold)
records=[]
def run(lam,method,phase,repeat):
    tag=f'{round(lam*100):03d}';rid=f'{attempt}-load{tag}-{method}-{phase}{repeat}'
    t0=time.perf_counter();c=load(case_paths[lam]);t_read=time.perf_counter()-t0
    prediction_seconds=0.;init_seconds=0.;preparation_seconds=0.;raw_metrics=None;clipping=None
    req={'run_id':rid,'matpower_file':str(ART/f'case{tag}.m'),'method':method,'load_scale':lam}
    if phase=='cold':req['capture_internal_iterate']=True
    if method=='gridsfm':
        t=time.perf_counter();obj=convert(c);pyg=ART/f'{rid}-input.pyg.json';save(pyg,obj);preparation_seconds=time.perf_counter()-t
        t=time.perf_counter();out=predict(model,pyg);prediction_seconds=time.perf_counter()-t
        # Save raw predictions; their physical evaluation is outside timed solver workflow.
        raw={k:v.tolist() if torch.is_tensor(v) else v for k,v in out.items()}
        p=dict(vm=raw['V'],va_deg=[math.degrees(a) for a in raw['theta']],pg_mw=[a*100 for a in raw['Pg']],qg_mvar=[a*100 for a in raw['Qg']])
        t=time.perf_counter();init=copy.deepcopy(p);counts={'vm':0,'pg':0,'qg':0};maxclip={'vm':0.,'pg_mw':0.,'qg_mvar':0.}
        for i,b in enumerate(c['bus']):
            x=init['vm'][i];y=min(b[11],max(b[12],x));counts['vm']+=int(x!=y);maxclip['vm']=max(maxclip['vm'],abs(x-y));init['vm'][i]=y
        for key,low,high,ct,mx in [('pg_mw',9,8,'pg','pg_mw'),('qg_mvar',4,3,'qg','qg_mvar')]:
            for i,g in enumerate(c['gen']):
                x=init[key][i];y=min(g[high],max(g[low],x));counts[ct]+=int(x!=y);maxclip[mx]=max(maxclip[mx],abs(x-y));init[key][i]=y
        slack=next(i for i,b in enumerate(c['bus']) if b[1]==3);anchor=init['va_deg'][slack];init['va_deg']=[a-anchor for a in init['va_deg']]
        sf,st=branch_flows(c,init['vm'],init['va_deg'])
        js={'bus':{str(int(b[0])):{'vm':v,'va':math.radians(a)} for b,v,a in zip(c['bus'],init['vm'],init['va_deg'])},'gen':{str(i+1):{'pg':p/100,'qg':q/100} for i,(p,q) in enumerate(zip(init['pg_mw'],init['qg_mvar']))},'branch':{str(i+1):{'pf':f.real/100,'qf':f.imag/100,'pt':t.real/100,'qt':t.imag/100} for i,(f,t) in enumerate(zip(sf,st))}}
        initpath=ART/f'{rid}-initialization.json';save(initpath,js);req['initialization_file']=str(initpath);init_seconds=time.perf_counter()-t
        clipping={'counts':counts,'max_change':maxclip,'angle_anchor_removed_deg':anchor,'policy':'clip only Vm/Pg/Qg to original boxes; anchor angles to original reference; compute branch primal starts from exact pi physics; no power-flow projection or solved labels; Ipopt default bound_push/bound_frac may move boundary starts'}
    t=time.perf_counter();server.stdin.write(json.dumps(req)+'\n');server.stdin.flush();line=server.stdout.readline();solver_roundtrip=time.perf_counter()-t
    e2e=time.perf_counter()-t0
    response=json.loads(line) if line else {'ok':False,'error':'server ended'}
    rec=dict(run_id=rid,scale=lam,method=method,phase=phase,repeat=repeat,end_to_end_seconds=e2e,input_read_seconds=t_read,conversion_serialization_seconds=preparation_seconds,predict_including_preprocessing_seconds=prediction_seconds,initialization_seconds=init_seconds,solver_roundtrip_seconds=solver_roundtrip,fallback_seconds=0.,clipping=clipping,solver_response=response)
    if method=='gridsfm':
        save(ART/f'{rid}-raw-prediction.json',p);raw_metrics=evaluate(c,p);rec['raw_prediction_metrics']=raw_metrics
        if lam==1.:
            saved=load(BASE/'case300-prediction.json');rec['nominal_saved_prediction_max_difference']=max(abs(a-b) for k in p for a,b in zip(p[k],saved[k]));assert rec['nominal_saved_prediction_max_difference']==0
    if response['ok']:
        result=load(response['result_path']);sol=result['solution'];ref={'vm':[sol['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[math.degrees(sol['bus'][str(int(b[0]))]['va']) for b in c['bus']],'pg_mw':[sol['gen'][str(i+1)]['pg']*100 for i in range(len(c['gen']))],'qg_mvar':[sol['gen'][str(i+1)]['qg']*100 for i in range(len(c['gen']))]}
        m=evaluate(c,ref);rec.update(final_metrics=m,objective=result['objective'],iterations=result['iterations'],termination_status=result['termination_status'],parse_build_seconds=result['parse_build_seconds'],optimize_call_seconds=result['optimize_call_seconds'])
        save(ART/f'{rid}-final-state.json',ref)
        # Initialization audit compares actual JuMP starts with the requested values.
        if method=='gridsfm':
            expected={'vm':{k:v['vm'] for k,v in js['bus'].items()},'va':{k:v['va'] for k,v in js['bus'].items()},'pg':{k:v['pg'] for k,v in js['gen'].items()},'qg':{k:v['qg'] for k,v in js['gen'].items()}}
            err=max(abs(v-result['initial_starts'][sym][k]) for sym,vals in expected.items() for k,v in vals.items());assert err<1e-12
            cb=result['iteration_zero_primal'];assert cb,'No Ipopt iteration-zero callback evidence'
            cb_delta={sym:max(abs(v-cb[sym][k]) for k,v in vals.items()) for sym,vals in expected.items()}
            rec['initialization_audit']={'requested_vs_JuMP_start_max_difference':err,'iteration_zero_callback_present':True,'callback_vs_supplied_start_max_difference':cb_delta,'iteration_zero_objective':result['iteration_trace'][0]['objective']}
    save(ART/f'{rid}-record.json',rec);records.append(rec)
    print(rid,response.get('termination_status',response.get('error')),rec.get('iterations'),round(e2e,4),rec.get('final_metrics',{}).get('all_tested_constraints_pass'),flush=True)
    if not response['ok']:raise RuntimeError('Instrumentation/server failure retained at '+rid)
    return rec
if len(sys.argv)>1 and sys.argv[1] in ['cold-default','cold-gridsfm']:
    method=sys.argv[1].split('-',1)[1]
    try:
        r=run(1.,method,'cold',0)
        save(OUT/(sys.argv[1]+'.json'),dict(setup=cold,first_call=r,note='Fresh Python and Julia processes per arm; shared harness imports include ML packages even for default; do not treat common harness import overhead as intrinsic default solver overhead.'))
    finally:
        server.stdin.write('{"quit":true}\n');server.stdin.flush();server.wait(timeout=30);stderr.close()
    sys.exit(0)
try:
    # Cold first calls and one per-method/per-input warm-up are retained separately.
    for lam in [1.,.9,.95,1.05,1.1]:
        for method in ['default','gridsfm']:run(lam,method,'warmup',0)
    for repeat in [1,2,3]:
        for lam in [.9,.95,1.,1.05,1.1]:
            for method in (['default','gridsfm'] if repeat%2 else ['gridsfm','default']):run(lam,method,'timed',repeat)
finally:
    if server.poll() is None:
        server.stdin.write('{"quit":true}\n');server.stdin.flush();server.wait(timeout=30)
    stderr.close();save(OUT/f'pilot-records-{attempt}.json',records)
summary=[]
for lam in [.9,.95,1.,1.05,1.1]:
    row={'load_scale':lam}
    for method in ['default','gridsfm']:
        rs=[r for r in records if r['phase']=='timed' and r['scale']==lam and r['method']==method]
        good=[r for r in rs if r.get('termination_status') in ['LOCALLY_SOLVED','OPTIMAL'] and r.get('final_metrics',{}).get('all_tested_constraints_pass')]
        row[method]={'successful_feasible_runs':len(good),'attempts':len(rs),'iterations':[r.get('iterations') for r in rs],'objective':[r.get('objective') for r in rs],'end_to_end_median_seconds':statistics.median(r['end_to_end_seconds'] for r in rs),'end_to_end_range_seconds':[min(r['end_to_end_seconds'] for r in rs),max(r['end_to_end_seconds'] for r in rs)],'solver_median_seconds':statistics.median(r['optimize_call_seconds'] for r in rs if 'optimize_call_seconds' in r),'parse_build_median_seconds':statistics.median(r['parse_build_seconds'] for r in rs if 'parse_build_seconds' in r),'preprocessing_inference_median_seconds':statistics.median(r['conversion_serialization_seconds']+r['predict_including_preprocessing_seconds'] for r in rs),'raw_max_P_MW':rs[0]['raw_prediction_metrics']['max_p_residual_mw'] if method=='gridsfm' else None,'raw_max_Q_MVAr':rs[0]['raw_prediction_metrics']['max_q_residual_mvar'] if method=='gridsfm' else None,'final_max_P_MW':max(r['final_metrics']['max_p_residual_mw'] for r in rs if 'final_metrics' in r),'final_max_Q_MVAr':max(r['final_metrics']['max_q_residual_mvar'] for r in rs if 'final_metrics' in r)}
    summary.append(row)
save(OUT/'pilot-summary.json',summary);save(OUT/'cold-start.json',dict(setup=cold,first_calls=[{k:r[k] for k in ['run_id','method','end_to_end_seconds','solver_roundtrip_seconds','predict_including_preprocessing_seconds']} for r in records[:2]]))
print(json.dumps(summary,indent=2))
