from summarize import *
from electrical import terms, excess
from focused import active_set

def state_for(sid,method):
    if method in NATIVE:
        filename={'AC-OPF':'ac-native.json','DC-OPF':'dc-native.json'}.get(method,method+'-native.json')
        p=PRIOR/'results'/sid/filename
    else:p=ROOT/'results'/sid/next(f for f,m in STAGES if m==method)/'state.json'
    return read(p) if p.exists() else None
def converged_for(sid,method):
    if 'official-PF' not in method:return None
    p=ROOT/'results'/sid/next(f for f,m in STAGES if m==method)/'status.json'
    return read(p).get('converged',False) if p.exists() else False

def main_diagnosis():
    records=[];locations=[];pairrows=[];trace=[]
    for spec in read(ROOT/'manifests/execution.json')['scenarios']:
        sid=spec['id'];c=read(PRIOR/'results'/sid/'input.json');ids,b,e,f,t=matrices(c);g=np.asarray(c['gen'])
        for folder,method in STAGES:
            p=ROOT/'results'/sid/folder
            if not (p/'metrics.json').exists():continue
            m=read(p/'metrics.json');status=read(p/'status.json');s=read(p/'state.json');tr=terms(c,s)
            native_method='V2-adapted-native' if folder.startswith('adapted') else 'newer-base-v2'
            sn=state_for(sid,native_method);tn=terms(c,sn)
            for i,row in enumerate(c['bus']):
                pairrows.append({'scenario':sid,'method':method,'bus_id':int(row[0]),'P_native_MW':float(tn['r'][i].real),'P_after_MW':float(tr['r'][i].real),'Q_native_MVAr':float(tn['r'][i].imag),'Q_after_MVAr':float(tr['r'][i].imag),'Qabs_change_MVAr':float(abs(tr['r'][i].imag)-abs(tn['r'][i].imag))})
            vals={'Pg':np.where(g[:,7]>0,excess(s['pg_mw'],g[:,9],g[:,8]),abs(np.asarray(s['pg_mw']))),
                  'Qg':np.where(g[:,7]>0,excess(s['qg_mvar'],g[:,4],g[:,3]),abs(np.asarray(s['qg_mvar']))),
                  'V':excess(s['vm'],b[:,12],b[:,11]),
                  'thermal':np.where((e[:,10]>0)&(e[:,5]>0),np.maximum(np.maximum(abs(tr['sf']),abs(tr['st']))-e[:,5],0),0)}
            for kind,v in vals.items():
                threshold=1e-4 if kind=='V' else 1e-3
                for j in np.flatnonzero(v>threshold):locations.append({'scenario':sid,'method':method,'constraint':kind,'row_1based':int(j)+1,'bus_id':int(g[j,0]) if kind in ['Pg','Qg'] else int(b[j,0]) if kind=='V' else None,'from_bus':int(c['branch'][j][0]) if kind=='thermal' else None,'to_bus':int(c['branch'][j][1]) if kind=='thermal' else None,'excess':float(v[j]),'PF_converged':status.get('converged')})
            records.append({**spec,'method':method,'PF_converged':status.get('converged'),'Q_max':m['Q_balance_MVAr']['max_abs'],'Q_p95':m['Q_balance_MVAr']['p95_abs'],'Q_mean':m['Q_balance_MVAr']['mean_abs'],'Q_count':m['Q_balance_MVAr']['violating_bus_count'],
                            'worst_Q_bus':int(c['bus'][int(np.argmax(abs(tr['r'].imag)))][0]),'worst_P_bus':int(c['bus'][int(np.argmax(abs(tr['r'].real)))][0]),
                            'total_Pg_MW':sum(s['pg_mw']),'total_Qg_MVAr':sum(s['qg_mvar']),'total_requested_Q_MVAr':float(tr['demand'].imag.sum()),'branch_net_Q_MVAr':float((tr['sf']+tr['st']).imag.sum()),'bus_shunt_Q_MVAr':float(tr['shunt'].imag.sum()),'signed_Q_residual_sum':float(tr['r'].imag.sum())})
            if 'norm_history_pu' in status:trace.append({'scenario':sid,'method':method,'converged':status['converged'],'iterations':status['iterations'],'first_residual_pu':status['norm_history_pu'][0],'last_residual_pu':status['norm_history_pu'][-1],'best_residual_pu':min(status['norm_history_pu']),'residual_increases':sum(v>u for u,v in zip(status['norm_history_pu'],status['norm_history_pu'][1:]))})
    for name,rows in [('stage-response-accounting',records),('constraint-locations',locations),('native-to-completed-bus-changes',pairrows),('newton-trace-summary',trace)]:csvsave(ROOT/'paper'/(name+'.csv'),rows)

def case3():
    a='case300-case3-PQ-p0.9300-q0.9300';z='case300-case3-PQ-p0.9400-q0.9400'
    ca=read(PRIOR/'results'/a/'input.json');cb=read(PRIOR/'results'/z/'input.json');out=ROOT/'paper/case3';out.mkdir(exist_ok=True)
    summary=[]
    for method in ['AC-OPF','microsoft-v1.1','newer-base-v2','V2-frozen+official-PF','V2-frozen+official-PF-exact-matrix']:
        sa=state_for(a,method);sb=state_for(z,method);ta=terms(ca,sa);tb=terms(cb,sb);ar=abs(ta['r'].imag);br=abs(tb['r'].imag);delta=br-ar
        rows=[]
        for i,bus in enumerate(ca['bus']):
            qgen=(tb['gen']-ta['gen'])[i].imag;qd=(tb['demand']-ta['demand'])[i].imag;qo=(tb['out']-ta['out'])[i].imag;qs=(tb['shunt']-ta['shunt'])[i].imag;dr=(tb['r']-ta['r'])[i].imag
            assert abs(dr-(qgen-qd-qo-qs))<1e-6
            rows.append({'bus_id':int(bus[0]),'Qabs_093':ar[i],'Qabs_094':br[i],'Qabs_change':delta[i],'signed_Qres_change':dr,'Qgen_change':qgen,'Qd_change':qd,'branch_Qout_change':qo,'shunt_Q_change':qs,'V_093':sa['vm'][i],'V_094':sb['vm'][i],'angle_093':sa['va_deg'][i],'angle_094':sb['va_deg'][i]})
        name=method.replace('+','_');csvsave(out/(name+'-all-bus-changes.csv'),sorted(rows,key=lambda r:r['Qabs_change']))
        hotspots={235,238,int(ca['bus'][np.argmax(ar)][0]),int(ca['bus'][np.argmax(br)][0])};near=set(hotspots);edges=[]
        for j,e in enumerate(ca['branch']):
            if int(e[0]) in hotspots or int(e[1]) in hotspots:
                near.update(map(int,e[:2]));edges.append({'branch_row':j+1,'from_bus':int(e[0]),'to_bus':int(e[1]),'r':e[2],'x':e[3],'charging':e[4],'Qf_093':ta['sf'][j].imag,'Qf_094':tb['sf'][j].imag,'Qt_093':ta['st'][j].imag,'Qt_094':tb['st'][j].imag})
        csvsave(out/(name+'-neighbor-branches.csv'),edges);csvsave(out/(name+'-neighbor-buses.csv'),[r for r in rows if r['bus_id'] in near])
        csvsave(out/(name+'-neighbor-generators.csv'),[{'row':i+1,'bus':int(g[0]),'Qg_093':sa['qg_mvar'][i],'Qg_094':sb['qg_mvar'][i],'Qmin':g[4],'Qmax':g[3]} for i,g in enumerate(ca['gen']) if int(g[0]) in near])
        j=320;e=ca['branch'][j];fi=next(i for i,bus in enumerate(ca['bus']) if bus[0]==e[0]);ti=next(i for i,bus in enumerate(ca['bus']) if bus[0]==e[1])
        def qparts(s):
            vf,vt=s['vm'][fi],s['vm'][ti];ang=np.deg2rad(s['va_deg'][fi]-s['va_deg'][ti]);y=1/complex(e[2],e[3]);g,bb=y.real,y.imag
            return ca['baseMVA']*np.array([-bb*vt*(vt-vf),bb*vt*vf*(np.cos(ang)-1)+g*vt*vf*np.sin(ang),-e[4]/2*vt*vt])
        qa,qb=qparts(sa),qparts(sb);assert abs(sum(qa)-ta['st'][j].imag)<1e-6 and abs(sum(qb)-tb['st'][j].imag)<1e-6
        def dist(v):return {'max':float(max(v)),'mean':float(np.mean(v)),'p95':float(np.percentile(v,95)),'count':int(sum(v>1e-3))}
        summary.append({'method':method,'Q_093':dist(ar),'Q_094':dist(br),'PF_093':converged_for(a,method),'PF_094':converged_for(z,method),'worst_bus_093':int(ca['bus'][np.argmax(ar)][0]),'worst_bus_094':int(ca['bus'][np.argmax(br)][0]),'improving_buses':int(sum(delta<-1e-6)),'worsening_buses':int(sum(delta>1e-6)),'unchanged_buses':int(sum(abs(delta)<=1e-6)),'branch321_Qt_change':float(sum(qb-qa)),'branch321_voltage_gap_component':float(qb[0]-qa[0]),'branch321_angle_component':float(qb[1]-qa[1]),'branch321_charging_component':float(qb[2]-qa[2]),'interpretation':'failed-iterate comparison only' if 'official-PF' in method else 'checked reference' if method=='AC-OPF' else 'native-output comparison'})
    ra,rb=state_for(a,'AC-OPF'),state_for(z,'AC-OPF');aa,ab=active_set(ca,ra),active_set(cb,rb)
    save(out/'reference-constraint-changes.json',{'added':sorted(ab-aa),'removed':sorted(aa-ab)})
    save(out/'summary.json',summary);print(json.dumps(summary,indent=2))

def sensitivity():
    rows=[];details=[];sets=[]
    for net in ['case300','case300x2','case500goc']:
        methods=['microsoft-v1.1','newer-base-v2']+[m for _,m in STAGES if not m.startswith('V2-adapted') or net=='case500goc']
        for component in ['P','Q']:
            for left,right,group in [(1.,1.005,'sensitivity-'+component),(1.,1.01,component),(1.01,1.02,component)]:
                a=net+'-base' if left==1 else f'{net}-{component}-p{left if component=="P" else 1.:.4f}-q{left if component=="Q" else 1.:.4f}'
                z=f'{net}-{group}-p{right if component=="P" else 1.:.4f}-q{right if component=="Q" else 1.:.4f}'
                ca=read(PRIOR/'results'/a/'input.json');cb=read(PRIOR/'results'/z/'input.json');ra,rb=state_for(a,'AC-OPF'),state_for(z,'AC-OPF');h=right-left
                if ra is None or rb is None:raise ValueError('Required sensitivity reference missing')
                aa,ab=active_set(ca,ra),active_set(cb,rb);sets.append({'network':net,'component':component,'left':left,'right':right,'added':sorted(ab-aa),'removed':sorted(aa-ab)})
                for method in methods:
                    sa,sb=state_for(a,method),state_for(z,method)
                    failed=any(converged_for(sid,method) is False for sid in [a,z])
                    for variable,threshold in [('vm',1e-6),('pg_mw',1e-3),('qg_mvar',1e-3)]:
                        idx=np.arange(len(ca['bus'])) if variable=='vm' else np.flatnonzero(np.asarray(ca['gen'])[:,7]>0)
                        av,bv,rv,sv=[np.asarray(s[variable])[idx] for s in [sa,sb,ra,rb]]
                        pred=bv-av;ref=sv-rv;eligible=abs(ref)>threshold;direction=(np.sign(pred[eligible])==np.sign(ref[eligible]))&(abs(pred[eligible])>threshold)
                        row={'network':net,'component':component,'left':left,'right':right,'h':h,'method':method,'variable':variable,'count':len(idx),'baseline_MAE':float(abs(av-rv).mean()),'response_delta_MAE':float(abs(pred-ref).mean()),'response_derivative_MAE':float(abs((pred-ref)/h).mean()),'response_derivative_RMSE':float(np.sqrt(np.mean(((pred-ref)/h)**2))),'reference_derivative_L2':float(np.linalg.norm(ref/h)),'model_to_reference_L2_ratio':float(np.linalg.norm(pred)/np.linalg.norm(ref)) if np.linalg.norm(ref)>0 else None,'direction_eligible_count':int(sum(eligible)),'direction_agreement_count':int(sum(direction)),'direction_agreement_percent':100*float(np.mean(direction)) if any(eligible) else None,'reference_response_threshold':threshold,'reference_constraint_changes':len(ab-aa)+len(aa-ab),'total_reference_delta':float(sum(ref)),'total_model_delta':float(sum(pred)),'status':'FAILED_ITERATE_SECANT_NOT_OPERATING_RESPONSE' if failed else 'CHECKED_REFERENCE_PAIR','both_PF_endpoints_converged':None if 'official-PF' not in method else not failed};rows.append(row)
                        for k,i in enumerate(idx):details.append({'network':net,'component':component,'left':left,'right':right,'method':method,'variable':variable,'row_1based':int(i)+1,'reference_delta':ref[k],'model_delta':pred[k],'reference_derivative':ref[k]/h,'model_derivative':pred[k]/h,'baseline_offset':av[k]-rv[k],'status':row['status']})
    save(ROOT/'paper/sensitivity-summary.json',rows);csvsave(ROOT/'paper/sensitivity-summary.csv',rows);csvsave(ROOT/'paper/sensitivity-details.csv',details);save(ROOT/'paper/reference-constraint-changes.json',sets)
    stable=[]
    for r in rows:
        if r['left']!=1 or abs(r['h']-.005)>1e-8:continue
        other=next(s for s in rows if all(s[k]==r[k] for k in ['network','component','method','variable']) and s['left']==1 and abs(s['h']-.01)<1e-8)
        stable.append({**{k:r[k] for k in ['network','component','method','variable']},'h005_RMSE':r['response_derivative_RMSE'],'h010_RMSE':other['response_derivative_RMSE'],'h005_direction_percent':r['direction_agreement_percent'],'h010_direction_percent':other['direction_agreement_percent'],'h005_status':r['status'],'h010_status':other['status']})
    save(ROOT/'paper/step-size-check.json',stable)
    print('SENSITIVITY',len(rows),'comparisons; failed-iterate secants explicitly labeled')

if __name__=='__main__':
    if sys.argv[1]=='case3':main_diagnosis();case3()
    elif sys.argv[1]=='sensitivity':sensitivity();main_diagnosis()
