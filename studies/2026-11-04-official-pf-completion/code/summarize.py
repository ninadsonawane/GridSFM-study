from run_extension import *
import csv

NATIVE=['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2']
STAGES=[('frozen-official','V2-frozen+official-PF'),('frozen-exact','V2-frozen+official-PF-exact-matrix'),('adapted-native','V2-adapted-native'),('adapted-official','V2-adapted+official-PF'),('adapted-exact','V2-adapted+official-PF-exact-matrix')]
def flatten(value,prefix=''):
    out={}
    for key,item in value.items():
        k=prefix+key
        if isinstance(item,dict):out.update(flatten(item,k+'.'))
        else:out[k]=item
    return out
def rows_now():
    rows=[];coverage=[]
    for spec in read(ROOT/'manifests/execution.json')['scenarios']:
        sid=spec['id'];network=spec['network'];d=PRIOR/'results'/sid
        for metric in read(d/'metrics.json'):
            method=metric['method'];available='AC_joint_pass' in metric or 'DC_own_constraints_pass' in metric
            # UNKNOWN reference rows remain attempted and unevaluable as accepted operating points.
            status='UNKNOWN' if method=='AC-OPF' and not (d/'ac-native.json').exists() else 'RETURNED'
            row={**spec,**flatten(metric),'status':status,'attempted':True,'returned':available,'evaluable':available,'PF_converged':None,'stage':'reused native/reference'}
            rows.append(row);coverage.append({k:row.get(k) for k in ['id','network','group','method','status','attempted','returned','evaluable','PF_converged']})
        for folder,method in STAGES:
            target=ROOT/'results'/sid/folder
            unavailable=folder.startswith('adapted') and network!='case500goc'
            if unavailable:
                row={**spec,'method':method,'status':'UNAVAILABLE_COMPATIBLE_WEIGHTS','attempted':False,'returned':False,'evaluable':False}
            elif not (target/'status.json').exists():
                row={**spec,'method':method,'status':'PENDING','attempted':False,'returned':False,'evaluable':False}
            else:
                status=read(target/'status.json');mp=target/'metrics.json';metric=read(mp) if mp.exists() else {}
                returned=(target/'state.json').exists();converged=status.get('converged')
                row={**spec,**flatten(metric),'method':method,'attempted':True,'returned':returned,'evaluable':mp.exists(),'PF_converged':converged,
                     'status':('RETURNED_NATIVE' if folder=='adapted-native' else 'CONVERGED' if converged else 'FAILED_FINITE_ITERATE' if returned else 'NO_EVALUABLE_STATE'),
                     'stage':folder,'iterations':status.get('iterations')}
            rows.append(row);coverage.append({k:row.get(k) for k in ['id','network','group','method','status','attempted','returned','evaluable','PF_converged']})
    return rows,coverage
def fmt(v):
    if v is None:return 'N/A'
    if isinstance(v,bool):return 'PASS' if v else 'FAIL'
    if isinstance(v,(float,np.floating)):return f'{v:.6g}'
    return str(v)
def baseline(rows):
    lines=['# Expanded nominal baseline tables','','Each metric uses the original physical matrices and prescribed demand. Official PF uses released graph physics with the disclosed supported bus-role adapter. The exact-matrix row is a separate diagnostic. Failed finite iterates are scored as failed candidates, not completed operating solutions. Adapted-native is retained to isolate completion within that checkpoint. Missing thermal limits are N/A.','']
    skip={'id','network','group','scenario','method','stage','relative_baseline','relative_P_factor','relative_Q_factor','input_sha256','reused_v2_state_sha256','reused_prepared_graph_sha256','historical_control'}
    for net in ['case300','case300x2','case500goc']:
        rr=[r for r in rows if r['network']==net and r['group']=='baseline'];methods=[r['method'] for r in rr]
        keys=list(dict.fromkeys(k for r in rr for k in r if k not in skip))
        table=[{'metric':k,**{r['method']:r.get(k) for r in rr}} for k in keys]
        csvsave(ROOT/'paper'/('baseline-'+net+'.csv'),table)
        lines += ['## '+net,'','| Metric | '+' | '.join(methods)+' |','|---|'+'---:|'*len(methods)]
        lines += ['| '+k+' | '+' | '.join(fmt(r.get(k)) for r in rr)+' |' for k in keys]
        lines.append('')
    (ROOT/'paper/baseline-tables.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def summarize():
    rows,coverage=rows_now();csvsave(ROOT/'paper/all-metrics.csv',rows);csvsave(ROOT/'paper/scenario-method-coverage.csv',coverage);baseline(rows)
    summaries=[]
    for net in ['case300','case300x2','case500goc']:
        for group in ['main-unique','P','Q','PQ','case3-all','sensitivity-all','all-unique']:
            group_rows=[r for r in rows if r['network']==net and (group=='all-unique' or (group=='main-unique' and r['group'] in ['baseline','P','Q','PQ']) or (group in ['P','Q','PQ'] and r['group'] in ['baseline',group]) or (group=='case3-all' and r['group'].startswith('case3')) or (group=='sensitivity-all' and r['group'].startswith('sensitivity')))]
            for method in NATIVE+[m for _,m in STAGES]:
                rr=[r for r in group_rows if r['method']==method]
                if not rr:continue
                attempted=sum(r['attempted'] for r in rr);evaluable=sum(r['evaluable'] for r in rr)
                def success(r):return r.get('DC_own_constraints_pass') is True if method=='DC-OPF' else (r.get('successful_AC_operating_point',r.get('AC_joint_pass')) is True)
                passes=sum(success(r) for r in rr)
                summaries.append({'network':net,'group':group,'method':method,'scenario_slots':len(rr),'attempted':attempted,'returned':sum(r['returned'] for r in rr),'evaluable':evaluable,
                                  'nonconverged':sum(r.get('PF_converged') is False and r['attempted'] for r in rr),'converged':sum(r.get('PF_converged') is True for r in rr),
                                  'missing_or_unevaluable_attempts':sum(r['attempted'] and not r['evaluable'] for r in rr),'unavailable':sum(r['status']=='UNAVAILABLE_COMPATIBLE_WEIGHTS' for r in rr),'pending':sum(r['status']=='PENDING' for r in rr),
                                  'passes':passes,'passes_over_attempts':None if not attempted else f'{passes}/{attempted}','passes_over_evaluable':None if not evaluable else f'{passes}/{evaluable}',
                                  'percent_attempted':100*passes/attempted if attempted else None,'percent_evaluable':100*passes/evaluable if evaluable else None,
                                  'definition':'native DC own constraints; full AC N/A' if method=='DC-OPF' else 'all original AC equations and limits, plus PF convergence where applicable'})
    csvsave(ROOT/'paper/feasibility-summary.csv',summaries)
    save(ROOT/'paper/summary.json',{'metric_slots':len(rows),'available_attempted':sum(r['attempted'] for r in rows),'pending':sum(r['status']=='PENDING' for r in rows),'summary':summaries})
    print(json.dumps([r for r in summaries if r['group']=='main-unique'],indent=2))

if __name__=='__main__':summarize()
