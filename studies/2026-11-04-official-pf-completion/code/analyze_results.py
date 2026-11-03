"""Derive paper evidence from saved states; no new inference or solve."""
from diagnose import *
from collections import Counter

def analyze():
    rows, coverage = rows_now()
    path_rows=[]; paired=[]; aggregate=[]; angle_locations=[]
    for net in ['case300','case300x2','case500goc']:
        for path in ['P','Q','PQ']:
            subset=[r for r in rows if r['network']==net and r['group'] in ['baseline',path]]
            for method in sorted({r['method'] for r in subset}):
                rr=[r for r in subset if r['method']==method and r.get('evaluable')]
                if not rr:continue
                result={'network':net,'path':path,'method':method,'evaluable':len(rr),
                        'converged':sum(r.get('PF_converged') is True for r in rr),
                        'original_balance_passes':None if method=='DC-OPF' else sum(r.get('P_balance_MW.max_abs',1e99)<=.001 and r.get('Q_balance_MVAr.max_abs',1e99)<=.001 for r in rr)}
                for cat in ['Pg_MW','Qg_MVAr','voltage_pu','branch_thermal_MVA','branch_angle_deg']:
                    kk='constraints.'+cat
                    vals=[r[kk+'.maximum'] for r in rr if r.get(kk+'.maximum') is not None]
                    if vals:
                        result[cat+'_max_range']=[min(vals),max(vals)]
                        result[cat+'_violating_scenarios']=sum(r.get(kk+'.violating_count',0)>0 for r in rr)
                path_rows.append(result)
                if method.startswith('V2-') and 'official-PF' in method:
                    native='V2-adapted-native' if 'adapted' in method else 'newer-base-v2'
                    for r in rr:
                        before=next(x for x in subset if x['id']==r['id'] and x['method']==native)
                        for key,value in r.items():
                            if (key.startswith('accuracy.') or key.startswith('constraints.') or key.startswith(('P_balance','Q_balance'))) and isinstance(value,(float,int)) and isinstance(before.get(key),(float,int)):
                                if key.endswith(('eligible_count','bus_count')) or (key.startswith('accuracy.') and key.endswith('.count')):continue
                                paired.append({'network':net,'path':path,'scenario':r['id'],'method':method,'metric':key,'native':before[key],'after':value,'change':value-before[key],'PF_converged':r.get('PF_converged'),'interpretation':'completed candidate' if r.get('PF_converged') else 'failed finite iterate only'})
    for spec in read(ROOT/'manifests/execution.json')['scenarios']:
        c=read(PRIOR/'results'/spec['id']/'input.json');ids,b,e,f,t=matrices(c)
        for folder,method in STAGES:
            target=ROOT/'results'/spec['id']/folder
            if not (target/'status.json').exists():continue
            status=read(target/'status.json');s=read(target/'state.json')
            for alloc in status.get('allocation',[]):
                q=alloc['recovered_bus_Q_MVAr'];lo=alloc['Qmin_sum'];hi=alloc['Qmax_sum'];err=max(lo-q,q-hi,0)
                aggregate.append({'scenario':spec['id'],'network':spec['network'],'group':spec['group'],'method':method,**alloc,'excess_MVAr':err,'violates':err>.001,'PF_converged':status.get('converged')})
            eligible=(e[:,10]>0)&~((e[:,11]==0)&(e[:,12]==0))&((e[:,11]>-360)|(e[:,12]<360))
            va=np.asarray(s['va_deg']);d=va[f]-va[t]
            for j in np.flatnonzero(eligible):
                lo=e[j,11] if e[j,11]>-360 else -np.inf
                hi=e[j,12] if e[j,12]<360 else np.inf
                v=max(lo-d[j],d[j]-hi,0)
                if v>.001:angle_locations.append({'scenario':spec['id'],'method':method,'branch_row_1based':int(j+1),'from_bus':int(c['branch'][j][0]),'to_bus':int(c['branch'][j][1]),'angle_difference_deg':float(d[j]),'excess_deg':float(v),'PF_converged':status.get('converged')})
    save(ROOT/'paper/path-analysis.json',path_rows)
    csvsave(ROOT/'paper/native-completion-metric-changes.csv',paired)
    grouped={}
    for row in paired:
        key=tuple(row[k] for k in ['network','path','method','metric'])
        grouped.setdefault(key,[]).append(row)
    comparison=[]
    for key,rr in sorted(grouped.items()):
        delta=[r['change'] for r in rr]
        comparison.append(dict(zip(['network','path','method','metric'],key),comparisons=len(rr),
            lower=sum(x < -1e-9 for x in delta),higher=sum(x > 1e-9 for x in delta),unchanged=sum(abs(x)<=1e-9 for x in delta),
            failed_iterate_comparisons=sum(r['PF_converged'] is False for r in rr)))
    csvsave(ROOT/'paper/completion-change-summary.csv',comparison)
    csvsave(ROOT/'paper/aggregate-bus-Q-limits.csv',aggregate)
    # Preserve an explicit empty result if there are no violating angle rows.
    save(ROOT/'paper/angle-violation-locations.json',angle_locations)
    sense=read(ROOT/'paper/sensitivity-summary.json')
    focus=[r for r in sense if r['variable']=='qg_mvar' and (r['component']=='Q' or (r['network']=='case500goc' and r['method'] in ['V2-adapted-native','V2-adapted+official-PF'])) and r['status']!='FAILED_ITERATE_SECANT_NOT_OPERATING_RESPONSE']
    nom=[{k:v for k,v in r.items() if k in ['network','method','status','PF_converged'] or k.endswith(('.max_abs','.maximum','.violating_count','.MAE'))} for r in rows if r['group']=='baseline' and r['method'] in ['newer-base-v2','V2-frozen+official-PF','V2-adapted-native','V2-adapted+official-PF','V2-adapted+official-PF-exact-matrix'] and r.get('evaluable')]
    brief={'nominal':nom,'Q_response':[ {k:r[k] for k in ['network','component','left','right','method','baseline_MAE','response_delta_MAE','response_derivative_RMSE','direction_agreement_percent','model_to_reference_L2_ratio','total_reference_delta','total_model_delta','reference_constraint_changes']} for r in focus],
           'sensitivity_status_counts':dict(Counter(r['status'] for r in sense)),
           'aggregate_Q_violations_in_converged_candidates':len([r for r in aggregate if r['violates'] and r['PF_converged']]),
           'angle_violation_rows':len(angle_locations)}
    save(ROOT/'paper/analysis-brief.json',brief)
    budgets=[]
    for spec in read(ROOT/'manifests/execution.json')['scenarios']:
        if spec['network']!='case500goc' or spec['group']=='baseline':continue
        ca=read(PRIOR/'results/case500goc-base/input.json');cb=read(PRIOR/'results'/spec['id']/'input.json')
        for method in ['V2-adapted-native','V2-adapted+official-PF','V2-adapted+official-PF-exact-matrix']:
            sa,sb=state_for('case500goc-base',method),state_for(spec['id'],method)
            ta,tb=terms(ca,sa),terms(cb,sb)
            def net(x):return (x['sf']+x['st']).sum()
            dg=complex(sum(sb['pg_mw'])-sum(sa['pg_mw']),sum(sb['qg_mvar'])-sum(sa['qg_mvar']))
            dd=tb['demand'].sum()-ta['demand'].sum();df=net(tb)-net(ta);ds=tb['shunt'].sum()-ta['shunt'].sum();dr=tb['r'].sum()-ta['r'].sum()
            assert abs(dg-dd-df-ds-dr)<1e-6
            row={'scenario':spec['id'],'method':method,'group':spec['group'],'relative_to':'case500goc-base',
                 'delta_slack_P_MW':sb['pg_mw'][0]-sa['pg_mw'][0],
                 'delta_other_Pg_MW':sum(sb['pg_mw'][1:])-sum(sa['pg_mw'][1:])}
            for key,value in [('generation',dg),('demand',dd),('branch_net',df),('bus_shunt',ds),('signed_residual_sum',dr)]:
                row['delta_'+key+'_P_MW']=float(value.real);row['delta_'+key+'_Q_MVAr']=float(value.imag)
            budgets.append(row)
    save(ROOT/'paper/response-budget.json',budgets)
    csvsave(ROOT/'paper/response-budget.csv',budgets)
    print(json.dumps({'path_summaries':len(path_rows),'paired_metric_rows':len(paired),'aggregate_Q_rows':len(aggregate),'angle_violation_rows':len(angle_locations),'sensitivity_status_counts':brief['sensitivity_status_counts']}))

if __name__=='__main__':analyze()
