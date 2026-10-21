"""Training-only initial gradient calibration; no optimizer updates."""
from neural import *
import traceback

def gradient(model,item,mode,weight=1.,total=False):
    model.zero_grad(set_to_none=True);out=model(item.batch());kp,kq=item.physics.kcl(out,mode);k=torch.log1p(kp)+torch.log1p(kq)
    loss=weight*k
    if total:loss=loss+objective(out,item.physics,'S')[0]
    loss.backward();check_gradients(model)
    g=torch.cat([p.grad.detach().flatten().double() if p.grad is not None else torch.zeros(p.numel(),dtype=torch.float64) for p in model.parameters() if p.requires_grad]);return g,dict(kp=float(kp.detach()),kq=float(kq.detach()),kcl=float(k.detach()),loss=float(loss.detach()))
def cosine(a,b):return float(torch.dot(a,b)/(a.norm()*b.norm()))
def probes(model,items,totals=False,rho=1.):
    py=random.getstate();nu=np.random.get_state();to=torch.get_rng_state();mode=model.training;model.eval();rows=[]
    try:
      for it in items:
        deadline();a,ca=gradient(model,it,'stock');b,cb=gradient(model,it,'exact');na=float(a.norm());nb=float(b.norm());valid=all(math.isfinite(x) for x in (na,nb)) and min(na,nb)>1e-12
        row=dict(scenario_id=it.record['scenario_id'],stock=ca,exact=cb,stock_norm=na,exact_norm=nb,valid=valid,ratio=nb/na if valid else None,cosine=cosine(a,b) if valid else None)
        if totals:
          g,c=gradient(model,it,'stock',rho,True);e,ce=gradient(model,it,'exact',1.,True)
          row.update(total_Cm_norm=float(g.norm()),total_E_norm=float(e.norm()),total_cosine=cosine(g,e),Cm_clip_factor=min(1,1/float(g.norm())),E_clip_factor=min(1,1/float(e.norm())))
        rows.append(row)
    finally:random.setstate(py);np.random.set_state(nu);torch.set_rng_state(to);model.train(mode);model.zero_grad(set_to_none=True)
    return rows

def main():
    t=time.time();manifest=read(OLD/'data/manifest.json');train=load_split('train',manifest);assert len(train)==50;model=make_model('C',11);model.eval()
    assert sha(CKPT)=='f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831'
    save(RUN/'config.json',dict(run_id=RUN.name,seeds=[11,22,33],arms=['S','C','E','C_m'],updates=1000,fit_cap_seconds=900,optimizer='AdamW',lr=1e-4,weight_decay=1e-4,clip=1.,batch=1,torch_threads=4,blas_threads=1,physics_precision='float64 original parameters',model_precision='float32',train_manifest_sha256=sha(OLD/'data/manifest.json'),base_checkpoint_sha256=sha(CKPT),metric_code_sha256=sha(REPO/'scripts/python/physics_metrics.py'),training_cases=[dict(scenario_id=it.record['scenario_id'],input_sha256=sha(it.path/'input.json'),reference_sha256=sha(it.path/'reference.json')) for it in train]))
    cfg=read(RUN/'config.json');cfg.update(read(Path(__file__).with_name('recipe.json')));save(RUN/'config.json',cfg)
    it=train[0];out=model(it.batch());s=objective(out,it.physics,'S')[0];c=objective(out,it.physics,'C')[0];e=objective(out,it.physics,'E')[0]
    assert torch.equal(c,objective(out,it.physics,'C_m',1.)[0]);assert torch.equal(s,objective(out,it.physics,'C_m',0.)[0]);assert torch.equal(c,legacy_objective(out,it.physics,'C')[0]);assert torch.equal(e,legacy_objective(out,it.physics,'E')[0])
    params0={k:v.detach().clone() for k,v in model.state_dict().items()};rngstates=[];orders=[]
    for seed in [11,22,33]:
      seed_all(seed);rngstates.append(sha_bytes(torch.get_rng_state().numpy().tobytes()));rng=np.random.Generator(np.random.PCG64(seed));order=[]
      while len(order)<1000:order.extend(rng.permutation(50).tolist())
      orders.append(order);save(RUN/f'orders/seed-{seed}.json',dict(seed=seed,indices=order,scenario_ids=[train[i].record['scenario_id'] for i in order]))
    assert len(set(rngstates))==3 and len({tuple(o) for o in orders})==3
    seed_all(11);rows=probes(model,train[:20]);valid=[x['ratio'] for x in rows if x['valid']];rho=float(np.median(valid)) if len(valid)>=16 else None
    result=dict(status='PASS' if rho else 'CALIBRATION_BLOCKED',rho=rho,valid_count=len(valid),required_valid_count=16,range=[min(valid),max(valid)] if valid else None,training_order='first20 accepted records in original saved manifest order',examples=rows,weight_outside_log1p=True,calibrated_on_validation=False)
    save(RUN/'calibration.json',result)
    if rho:save(RUN/'calibration-total-probes.json',probes(model,train[:5],True,rho))
    assert all(torch.equal(v,model.state_dict()[k]) for k,v in params0.items());(RUN/'checks').mkdir(exist_ok=True);checkpoint(model,None,'C',0,RUN/'checks/reload.pt');p0=physical_state(model(it.batch()));load_checkpoint(model,RUN/'checks/reload.pt');assert p0==physical_state(model(it.batch()))
    save(RUN/'checks.json',dict(status='PASS',reused_checks=str(OLD/'checks.json'),reused_checks_sha256=sha(OLD/'checks.json'),actual_seed_rng_and_order_distinct=True,objective_lambda_zero_equals_S=True,multiplier_one_equals_C=True,C_E_legacy_equal=True,finite_calibration_gradients=True,no_parameter_updates=True,reload_prediction_equivalence=True,calibration_valid_count=len(valid),elapsed_seconds=time.time()-t));log('EXPERIMENT5_COMPLETE',rho=rho,valid=len(valid),seconds=time.time()-t)
def sha_bytes(x):return hashlib.sha256(x).hexdigest()
if __name__=='__main__':
 try:main()
 except Exception as e:save(RUN/'calibration-failure.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
