"""Mandatory correctness/mechanism checks and six disposable throughput smokes."""
from neural import *
import psutil,resource
from gridsfm import predict,load_pyg_json,prepare_for_inference
from gridsfm.loss import compute_loss,kcl_residual_loss,_flows_rx_bidir
def vector_grad(loss,params,retain=True):
    grads=torch.autograd.grad(loss,params,retain_graph=retain,allow_unused=True)
    return torch.cat([(torch.zeros_like(p) if g is None else g).detach().flatten() for p,g in zip(params,grads)])
def norm(v):return float(torch.linalg.vector_norm(v.double()))
def cosine(a,b):return float(torch.dot(a.double(),b.double())/max(norm(a)*norm(b),1e-30))
def mechanism_checks():
    stage=RUN/'checks';stage.mkdir(exist_ok=True);seed_all();items=load_split('smoke_train');val=load_split('smoke_validation');item=items[0]
    original=load_model(CKPT,device='cpu');original.eval()
    with torch.no_grad():old=original(item.batch());oldv=encode_state(physical_state(old))
    del original,old;gc.collect();m=make_model('S');out=m(item.batch());newv=encode_state(physical_state(out));assert np.array_equal(oldv,newv),'auxiliary tail changed regression outputs'
    audit={'forward_tail_regression_bitwise_equal':True,'original_precision_parameters':True,'no_synthetic_negatives':True,'rated_branch_masks':0,'dtype':'backboneFP32; shared C/E original-parameter physicsFP64','reference_checks':{},'unit_checks':{},'mechanism':{},'label_checks':{}}
    # Clean features are prepared before any labels are attached.
    clean=to_data(convert(item.case),training=False)
    for nt in clean.node_types:assert torch.equal(clean[nt].x,item.data[nt].x),nt
    assert torch.equal(clean.g_ctx,item.data.g_ctx)
    altered=copy.deepcopy(item.obj);altered['solution']['nodes']['bus']=[[.123,.9] for _ in range(300)]
    altered['solution']['nodes']['generator']=[[1.,2.] for _ in range(69)]
    ad=to_data(altered,training=True)
    for nt in ad.node_types:assert torch.equal(ad[nt].x,item.data[nt].x)
    with torch.no_grad():clean_out=m(batch_data_list([clean]));altered_out=m(batch_data_list([ad]))
    assert np.array_equal(encode_state(physical_state(clean_out)),encode_state(physical_state(altered_out)))
    assert tuple(item.data['bus'].y.shape)==(300,2) and tuple(item.data['generator'].y.shape)==(69,2)
    expected=np.array([[math.radians(a),v] for a,v in zip(item.ref['va_deg'],item.ref['vm'])]);assert np.allclose(item.data['bus'].y.numpy(),expected,atol=1e-7)
    expected=np.c_[np.array(item.ref['pg_mw'])/100,np.array(item.ref['qg_mvar'])/100];assert np.allclose(item.data['generator'].y.numpy(),expected,atol=1e-6)
    both=batch_data_list([items[0].data.clone(),items[1].data.clone()]);assert bool(build_feasible_masks(both)['gmask'].all())
    with torch.no_grad():multi=m(both);single=m(items[1].batch())
    err=float(torch.max(torch.abs(multi['bus'].pred[300:]-single['bus'].pred)));assert err<2e-3,err
    audit['label_checks']={'prepared_features_invariant_to_labels':True,'predictions_invariant_to_altered_labels':True,'target_order':'bus(theta radians,V pu),generator(Pg,Qg systempu)','feasible_masks':'all accepted feasible','two_graph_max_bus_prediction_difference':err,'fresh_batch_copies':True}
    out=m(item.batch());sup,parts=objective(out,item.physics,'S');kp,kq=item.physics.kcl(out,'stock');ep,eq=item.physics.kcl(out,'exact');cl=torch.log1p(kp)+torch.log1p(kq);el=torch.log1p(ep)+torch.log1p(eq)
    oracle,oracle_parts=compute_loss(out,lambda_feas=0,lambda_stress_feas=0,lambda_kcl_p=0,lambda_kcl_q=0)
    assert torch.allclose(sup,oracle,atol=1e-6,rtol=1e-6),(sup,oracle)
    assert all(oracle_parts[k]==0 for k in ['L_br_p','L_br_q','L_therm','L_therm_lim'])
    params=[p for p in m.parameters() if p.requires_grad];vectors={}
    for label,loss in [('supervised_cost',sup),('stock_KCL',cl),('exact_KCL',el),('total_C',sup+cl),('total_E',sup+el)]:
        v=vector_grad(loss,params);assert_finite(v,label+' grad');vectors[label]=v
    audit['mechanism']={'raw_supervised_cost':parts,'raw_stock_kcl_p':float(kp.detach()),'raw_stock_kcl_q':float(kq.detach()),'raw_exact_kcl_p':float(ep.detach()),'raw_exact_kcl_q':float(eq.detach()),'weighted_stock_kcl':float(cl.detach()),'weighted_exact_kcl':float(el.detach()),'gradient_norms':{k:norm(v) for k,v in vectors.items()},'gradient_cosines':{a+'__'+b:cosine(vectors[a],vectors[b]) for a,b in [('stock_KCL','exact_KCL'),('supervised_cost','stock_KCL'),('supervised_cost','exact_KCL'),('total_C','total_E')]},'normalization':{'P_capacity_pu':item.physics.cp,'Q_capacity_pu':item.physics.cq,'worst_tilt':.8,'mean_weight':.2,'worst_margin':.01,'compression':'log1p each KCL component; coefficients1'}}
    # Directional parameter probes use smoke data only and restore original tensors exactly.
    originals=[p.detach().clone() for p in params];directional={}
    start_score=score(item.case,physical_state(out),item.ref)
    for label in ['supervised_cost','stock_KCL','exact_KCL']:
        grad=vectors[label];offset=0;gradnorm=max(norm(grad),1e-30)
        with torch.no_grad():
            for p,orig in zip(params,originals):n=p.numel();p.copy_(orig-1e-4*grad[offset:offset+n].reshape_as(p)/gradnorm);offset+=n
            probe=m(item.batch());scores=score(item.case,physical_state(probe),item.ref)
            for p,orig in zip(params,originals):p.copy_(orig)
        directional[label]={'step_l2':1e-4,'before_max_P_MW':start_score['max_p_residual_mw'],'after_max_P_MW':scores['max_p_residual_mw'],'before_max_Q_MVAr':start_score['max_q_residual_mvar'],'after_max_Q_MVAr':scores['max_q_residual_mvar']}
    audit['mechanism']['directional_probes']=directional
    del vectors,originals,params,out,m,sup,cl,el,kp,kq,ep,eq,oracle;gc.collect()
    # Reference and units checks operate on original float64 states, no neural rounding.
    c=read(BASE/'case300-input.json');ref=read(BASE/'case300-reference.json');pred=read(BASE/'case300-prediction.json')
    for name,s in [('reference',ref),('frozen_prediction',pred)]:
        ph=Physics(c);T=lambda a:torch.tensor(a,dtype=torch.float64);theta=T(np.deg2rad(s['va_deg']));V=T(s['vm']);pg=T(np.array(s['pg_mw'])/100);qg=T(np.array(s['qg_mvar'])/100)
        rp,rq=ph.residual(theta,V,pg,qg,'exact');sp,sq=ph.residual(theta,V,pg,qg,'stock');ind=evaluate(c,s)
        err=max(abs(float(rp.abs().max()*100)-ind['max_p_residual_mw']),abs(float(rq.abs().max()*100)-ind['max_q_residual_mvar']));assert err<1e-6,err
        phi=ph.phi;flows=_flows_rx_bidir(theta,V,ph.i,ph.j,ph.r,ph.x,ph.b,ph.b,ph.tau,phi)
        z=V.new_zeros(300);fP=z.scatter_add(0,ph.i,flows[0]).scatter_add(0,ph.j,flows[2]);fQ=z.scatter_add(0,ph.i,flows[1]).scatter_add(0,ph.j,flows[3]);oracleP=fP-(z.scatter_add(0,ph.gbus,pg)-ph.pd-ph.gs*V**2);oracleQ=fQ-(z.scatter_add(0,ph.gbus,qg)-ph.qd+ph.bs*V**2)
        assert torch.allclose(sp,oracleP,atol=1e-10) and torch.allclose(sq,oracleQ,atol=1e-10)
        audit['reference_checks'][name]={'exact_max_P_MW':float(rp.abs().max()*100),'exact_max_Q_MVAr':float(rq.abs().max()*100),'stock_max_P_MW':float(sp.abs().max()*100),'stock_max_Q_MVAr':float(sq.abs().max()*100),'independent_disagreement_MW_MVAr':err}
        if name=='reference':
            vv=V.clone().requires_grad_();tt=theta.clone().requires_grad_();pp=pg.clone().requires_grad_();qq=qg.clone().requires_grad_();rrp,rrq=ph.residual(tt,vv,pp,qq,'exact');smooth=(rrp.square()+rrq.square()).mean();gr=torch.autograd.grad(smooth,[tt,vv,pp,qq]);audit['reference_checks'][name]['smooth_exact_squared_residual_gradient_norm']=float(torch.sqrt(sum(g.square().sum() for g in gr)))
    for basemva in [25,100,400]:
        new=copy.deepcopy(c);new['baseMVA']=basemva
        for b in new['branch']:b[2]*=basemva/100;b[3]*=basemva/100;b[4]*=100/basemva
        a=evaluate(c,pred);b=evaluate(new,pred);err=max(abs(a[k]-b[k]) for k in ['max_p_residual_mw','max_q_residual_mvar','generation_cost_per_hour']);assert err<1e-6;save(stage/f'units-{basemva}.json',{'baseMVA':basemva,'exact_invariance_max_difference':err});audit['unit_checks'][str(basemva)]=err
    save(RUN/'operator-audit.json',audit)
def smoke_checks(resume=False):
    stage=RUN/'checks';stage.mkdir(exist_ok=True);seed_all();items=load_split('smoke_train');val=load_split('smoke_validation');item=items[0]
    smokes=[];manifests={}
    if resume and (RUN/'events.jsonl').exists():
        successful={}
        for line in (RUN/'events.jsonl').read_text().splitlines():
            r=json.loads(line)
            if r.get('event')=='SMOKE_COMPLETE' and r.get('status')=='PASS':successful[r['arm']]={k:v for k,v in r.items() if k not in ['event','utc']}
        smokes=list(successful.values())
    passed={r['arm'] for r in smokes}
    oldv=None
    if 'L' not in passed:
        frozen_model=make_model('F')
        with torch.no_grad():oldv=encode_state(physical_state(frozen_model(item.batch())))
        del frozen_model;gc.collect()

    # Each arm has an independent <=120s/20-update smoke. No state carries to main fits.
    for arm in ['S','C','E','H','L','R']:
        if arm in passed:
            model=make_model(arm);manifests[arm]=trainable_manifest(model,arm);del model;gc.collect();continue
        deadline();t0=time.perf_counter();model=make_model(arm);params=[p for p in model.parameters() if p.requires_grad];manifests[arm]=trainable_manifest(model,arm)
        if arm=='L':
            with torch.no_grad():lout=model(item.batch());initial=encode_state(physical_state(lout))
            assert np.array_equal(initial,oldv),'zero LoRA+heads differs from frozen'
        frozen={n:p.detach().clone() for n,p in model.named_parameters() if not p.requires_grad};optimizer=torch.optim.AdamW(params,lr=1e-4,weight_decay=1e-4);trace=[]
        handles=[]
        for name,module in model.named_modules():
            def hook(mod,inputs,outputs,name=name):assert_finite(outputs,'module '+name)
            handles.append(module.register_forward_hook(hook))
        try:
            for step in range(20):
                if time.perf_counter()-t0>=120:break
                deadline();t=time.perf_counter();optimizer.zero_grad(set_to_none=True);out=model(items[step%len(items)].batch());loss,parts=objective(out,items[step%len(items)].physics,arm);loss.backward();grad=check_gradients(model);torch.nn.utils.clip_grad_norm_(params,1.);optimizer.step();rss=psutil.Process().memory_info().rss;avail=psutil.virtual_memory().available
                if rss>32*2**30 or avail<12*2**30:raise MemoryError('memory limit during smoke')
                trace.append({'update':step+1,'seconds':time.perf_counter()-t,'RSS_bytes':rss,'available_memory_bytes':avail,'parts':parts,**grad})
            for n,p in model.named_parameters():
                if n in frozen:assert torch.equal(p.detach(),frozen[n]),'frozen parameter changed '+n
            for handle in handles:handle.remove()
            model.eval();pred_before=evaluate_model(model,val)[0];cp=stage/(arm+'-smoke-checkpoint.pt');checkpoint(model,optimizer,arm,len(trace),cp)
            # Reuse the one resident model, perturb heads, then restore all state.
            with torch.no_grad():next(p for p in model.parameters() if p.requires_grad).add_(.123)
            blob=load_checkpoint(model,cp);pred_after=evaluate_model(model,val)[0]
            assert pred_before==pred_after,'checkpoint reload changed predictions'
            tv=time.perf_counter();evaluate_model(model,val);valtime=time.perf_counter()-tv
            row={'arm':arm,'status':'PASS','updates':len(trace),'elapsed':time.perf_counter()-t0,'p95_update_seconds':float(np.percentile([r['seconds'] for r in trace],95)),'median_update_seconds':float(np.median([r['seconds'] for r in trace])),'four_validation_seconds':valtime,'peak_RSS_bytes':max(r['RSS_bytes'] for r in trace),'reload_equivalence':True,'frozen_parameters_unchanged':True,'intermediate_hooks':True,'sanitizer_inputs_checked':True}
            save(stage/(arm+'-smoke-trace.json'),trace);smokes.append(row);save(RUN/'smoke-progress.json',smokes);log('SMOKE_COMPLETE',**row)
        except Exception as e:
            save(stage/(arm+'-smoke-trace.json'),trace);smokes.append({'arm':arm,'status':'FAIL','reason':repr(e),'updates':len(trace)});save(RUN/'smoke-summary.json',smokes);raise
        finally:
            for handle in handles:handle.remove()
            del model,optimizer,params,frozen
            if 'out' in locals():del out,loss
            if 'blob' in locals():del blob
            gc.collect()
    slow=max(r['p95_update_seconds'] for r in smokes);U=min(200,50*math.floor(900/(50*slow)));validation_estimate=max(r['four_validation_seconds'] for r in smokes)*10/4*(U//50+1)
    if U<50 or validation_estimate>600:raise RuntimeError('throughput gate cannot fit matched U and validation')
    result={'status':'PASS','U':U,'slowest_p95_seconds_per_update':slow,'estimated_validation_seconds_per_fit':validation_estimate,'smoke':smokes,'rule':'min(200,50*floor(900/(50*t))); t slowest smoke p95; no learning outcome used to choose U'}
    save(RUN/'smoke-summary.json',result);save(RUN/'model-manifests.json',manifests);save(RUN/'checks.json',{'status':'PASS','operator_audit':'operator-audit.json','smoke_audit':'smoke-summary.json','shared_data_counts':read(RUN/'data/counts.json'),'U':U});log('GATE_PASS',U=U,slowest_p95=slow)
def main():
    resume='--resume-smoke' in sys.argv
    if not (resume and (RUN/'operator-audit.json').exists()):mechanism_checks()
    smoke_checks(resume)
if __name__=='__main__':
    try:main()
    except Exception as e:
        import traceback
        save(RUN/'checks-failure.json',{'status':'BLOCKED','error':repr(e),'traceback':traceback.format_exc()});log('GATE_BLOCKED',error=repr(e));raise
