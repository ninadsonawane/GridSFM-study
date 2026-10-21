import sys,json,math,copy,hashlib
from pathlib import Path
ROOT=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study')
sys.path.insert(0,str(ROOT/'scripts/python'))
from physics_metrics import evaluate,wrap_degrees
from gridsfm_convert import convert
OUT=Path(__file__).parent
def read(name):return json.loads((OUT/name).read_text())
def save(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def close(a,b,tol=1e-8):
    assert abs(a-b)<=tol*max(1,abs(a),abs(b)),(a,b)
def reconstruct(case,obj):
    # Reverse only the native electrical fields; compare physical residuals after.
    c=copy.deepcopy(case);nodes=obj['grid']['nodes'];edges=obj['grid']['edges'];md=obj['metadata'];base=c['baseMVA']
    for b,x in zip(c['bus'],nodes['bus']):
        b[9],b[1],b[12],b[11]=x;b[2]=b[3]=b[4]=b[5]=0
    for kind,fields in [('load',(2,3)),('shunt',(5,4))]:
        e=edges[kind+'_link']
        for x,j in zip(nodes[kind],e['receivers']):
            for v,k in zip(x,fields):c['bus'][j][k]+=v*base
    for g,cost,x in zip(c['gen'],c['gencost'],nodes['generator']):
        g[6],g[1],g[9],g[8],g[2],g[4],g[3],g[5]=[x[0],x[1]*base,x[2]*base,x[3]*base,x[4]*base,x[5]*base,x[6]*base,x[7]]
        cost[4:7]=[x[8]/base**2,x[9]/base,x[10]]
    for kind in ['ac_line','transformer']:
        e=edges[kind]
        for j,x,f,t in zip(md[kind+'_source_rows'],e['features'],e['senders'],e['receivers']):
            row=c['branch'][j];row[0]=c['bus'][f][0];row[1]=c['bus'][t][0]
            row[11:13]=[math.degrees(x[0]),math.degrees(x[1])]
            if kind=='ac_line':
                row[2:8]=[x[4],x[5],x[2]+x[3],x[6]*base,x[7]*base,x[8]*base];row[8]=0;row[9]=0
            else:
                row[2:10]=[x[2],x[3],x[9]+x[10],x[4]*base,x[5]*base,x[6]*base,x[7],math.degrees(x[8])]
    for k in ['bus','gen','branch','gencost']:
        for orig,back in zip(case[k],c[k]):
            for i,(a,b) in enumerate(zip(orig,back)):
                if k=='branch' and i==8:a=a or 1;b=b or 1
                close(a,b)
    return c
summary=[]
for name in ['case300','case300x2']:
    c=read(name+'-input.json');base=c['baseMVA'];p=read(name+'-prediction.json');raw=read(name+'-reference-raw.json');sol=raw['solution'];pm=read(name+'-powermodels-input.json')
    assert raw['termination_status']=='LOCALLY_SOLVED',raw['termination_status']
    # Check original parameters survived PM parsing/unit conversion.
    assert len(pm['bus'])==len(c['bus']) and len(pm['gen'])==len(c['gen']) and len(pm['branch'])==len(c['branch'])
    for b in c['bus']:
        pb=pm['bus'][str(int(b[0]))]
        for key,x in [('bus_type',b[1]),('base_kv',b[9]),('vmin',b[12]),('vmax',b[11])]:close(pb[key],x)
        loads=[v for v in pm['load'].values() if v['load_bus']==int(b[0])]
        shunts=[v for v in pm['shunt'].values() if v['shunt_bus']==int(b[0])]
        for key,x in [('pd',b[2]),('qd',b[3])]:close(sum(v[key] for v in loads)*base,x)
        for key,x in [('gs',b[4]),('bs',b[5])]:close(sum(v[key] for v in shunts)*base,x)
    for i,(g,cost) in enumerate(zip(c['gen'],c['gencost']),1):
        pg=pm['gen'][str(i)];assert pg['gen_bus']==int(g[0])
        for key,j in [('pmin',9),('pmax',8),('qmin',4),('qmax',3)]:close(pg[key]*base,g[j])
        for a,b in zip(pg['cost'],[cost[4]*base**2,cost[5]*base,cost[6]]):close(a,b)
    for i,b in enumerate(c['branch'],1):
        pb=pm['branch'][str(i)]
        for key,x in [('f_bus',b[0]),('t_bus',b[1]),('br_r',b[2]),('br_x',b[3]),('tap',b[8] or 1),('shift',math.radians(b[9])),('angmin',math.radians(b[11])),('angmax',math.radians(b[12]))]:close(pb[key],x)
        close(pb['b_fr']+pb['b_to'],b[4]);close(pb.get('rate_a',0)*base,b[5])
    ref={'vm':[sol['bus'][str(int(b[0]))]['vm'] for b in c['bus']],
         'va_deg':[math.degrees(sol['bus'][str(int(b[0]))]['va']) for b in c['bus']],
         'pg_mw':[sol['gen'][str(i+1)]['pg']*base for i in range(len(c['gen']))],
         'qg_mvar':[sol['gen'][str(i+1)]['qg']*base for i in range(len(c['gen']))]}
    rm=evaluate(c,ref);assert rm['all_tested_constraints_pass'],rm
    close(rm['generation_cost_per_hour'],raw['objective'])
    for key in ['pf_mw','qf_mvar','pt_mw','qt_mvar']:
        for i,x in enumerate(rm[key],1):close(x,sol['branch'][str(i)][key[:2]]*base,tol=1e-7)
    back=reconstruct(c,read(name+'.pyg.json'));bm=evaluate(back,ref)
    for k in ['max_p_residual_mw','max_q_residual_mvar','generation_cost_per_hour']:close(bm[k],rm[k])
    pmtr=evaluate(c,p)
    slack=next(i for i,b in enumerate(c['bus']) if b[1]==3)
    angle_errors=[abs(wrap_degrees((a-p['va_deg'][slack])-(b-ref['va_deg'][slack]))) for a,b in zip(p['va_deg'],ref['va_deg'])]
    row={'case':name,'buses':len(c['bus']),'generators':len(c['gen']),'branches':len(c['branch']),
         'reference_cost_per_hour':raw['objective'],'predicted_dispatch_cost_per_hour':pmtr['generation_cost_per_hour'],
         'absolute_cost_error_percent':100*abs(pmtr['generation_cost_per_hour']-raw['objective'])/abs(raw['objective']),
         'voltage_mae_pu':sum(abs(a-b) for a,b in zip(p['vm'],ref['vm']))/len(c['bus']),
         'angle_reference_aligned_mae_deg':sum(angle_errors)/len(angle_errors),
         'pg_mae_mw':sum(abs(a-b) for a,b in zip(p['pg_mw'],ref['pg_mw']))/len(c['gen']),
         'qg_mae_mvar':sum(abs(a-b) for a,b in zip(p['qg_mvar'],ref['qg_mvar']))/len(c['gen']),
         'max_p_residual_mw':pmtr['max_p_residual_mw'],'max_q_residual_mvar':pmtr['max_q_residual_mvar'],
         'prediction_all_tested_constraints_pass':pmtr['all_tested_constraints_pass'],
         'reference_max_p_residual_mw':rm['max_p_residual_mw'],'reference_max_q_residual_mvar':rm['max_q_residual_mvar'],
         'reference_all_tested_constraints_pass':rm['all_tested_constraints_pass'],
         'model_feasibility_probability':read(name+'-model-output.json')['feas'],
         'reference_solver_status':raw['termination_status'],
         'source_to_pm_and_native_roundtrip':'passed electrical parameter/objective/solved-flow checks'}
    if name=='case300x2':
        row['tie_reference_pf_mw']=rm['pf_mw'][-2:];row['tie_prediction_pf_mw']=pmtr['pf_mw'][-2:]
        row['tie_reference_qf_mvar']=rm['qf_mvar'][-2:];row['tie_prediction_qf_mvar']=pmtr['qf_mvar'][-2:]
    save(name+'-reference.json',ref);save(name+'-reference-metrics.json',rm)
    # Accepted labels for a prediction-level no-leakage check; never model inputs.
    labels=dict(ref,objective=raw['objective'],accepted_feasible=True)
    for key in ['pf_mw','qf_mvar','pt_mw','qt_mvar']:labels[key]=rm[key]
    save(name+'-labeled.pyg.json',convert(c,labels))
    summary.append(row)
save('summary.json',summary)
print(json.dumps(summary,indent=2))
