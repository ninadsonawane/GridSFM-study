from adapter import *
from electrical import terms

records=[]
for net in ['case500goc','case300','case300x2']:
    sid=net+'-base'
    original,c,info=case_for(sid,exact=True)
    ref=read(PRIOR/'results'/sid/'ac-native.json')
    controls=copy.deepcopy(ref)
    controls['vm']=np.ones(c.n_bus).tolist()
    for i in c.ctrl_bus:controls['vm'][i]=ref['vm'][i]
    controls['qg_mvar']=[0.0]*len(original['gen'])
    for exact in [False,True]:
        label='exact-matrix' if exact else 'released-graph'
        target=ROOT/'validation'/f'{net}-reference-controls-{label}'
        if (target/'status.json').exists():
            state=read(target/'state.json'); status=read(target/'status.json')
        else:state,status=score_and_save(target,sid,controls,'REFERENCE-CONTROL-VALIDATION-ONLY',exact=exact,tol=1e-8)
        metric=read(target/'metrics.json')
        records.append({'network':net,'path':label,'converged':status['converged'],'iterations':status['iterations'],
                        'P_max_MW':metric['P_balance_MW']['max_abs'],'Q_max_MVAr':metric['Q_balance_MVAr']['max_abs'],
                        'joint_pass':metric['AC_joint_pass'],'balancing_buses':status['completion_balancing_buses']})
        if exact:
            assert status['converged'] and metric['AC_joint_pass'], records[-1]
            # Independent evaluator and deliberate perturbation gates, without changing production evaluator.
            tr=terms(original,state);assert tr['crosscheck_MW_MVAr']<=1e-6
            altered=copy.deepcopy(state);j=int(np.flatnonzero(np.asarray(original['gen'])[:,7]>0)[0]);altered['pg_mw'][j]+=1
            mm,*_=evaluate(original,altered,'PERTURBATION-ONLY')
            assert mm['P_balance_MW']['max_abs']>0.99 and not mm['AC_joint_pass']
            altered=copy.deepcopy(state);altered['qg_mvar'][j]=original['gen'][j][3]+1
            mm,*_=evaluate(original,altered,'PERTURBATION-ONLY')
            assert mm['constraints']['Qg_MVAr']['maximum']>=0.999 and not mm['AC_joint_pass']
            altered=copy.deepcopy(state);altered['vm'][0]=original['bus'][0][11]+.01
            mm,*_=evaluate(original,altered,'PERTURBATION-ONLY')
            assert mm['constraints']['voltage_pu']['maximum']>=.0099 and not mm['AC_joint_pass']
    if net=='case500goc':
        target=ROOT/'validation/case500goc-untouched-extractor-reference-diagnostic'
        if not (target/'status.json').exists():score_and_save(target,sid,controls,'UNMAPPED-EXTRACTOR-DIAGNOSTIC',supported_roles=False,tol=1e-8)
save(ROOT/'validation/adapter-gates.json',{'status':'PASS_WITH_DECLARED_GRAPH_PHYSICS_DIFFERENCE','original_matrix_known_control_gates_pass':True,
     'unchanged_external_evaluator_reused':True,'perturbations_detected':['+1MW Pg','Qg beyond Qmax','Vm beyond Vmax'],
     'rows':records,'no_model_results_in_this_file':True})
print(json.dumps(records,indent=2))
