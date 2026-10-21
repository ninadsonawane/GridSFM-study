"""Locked fresh evaluation, raw predictions and descriptive error localization."""
from neural import *
import csv

def residuals(item,state):
    vals=[torch.tensor(v,dtype=torch.float64) for v in [np.deg2rad(state['va_deg']),state['vm'],np.array(state['pg_mw'])/100,np.array(state['qg_mvar'])/100]]
    ex=np.array([x.numpy()*100 for x in item.physics.residual(*vals,'exact')]);cl=np.array([x.numpy()*100 for x in item.physics.residual(*vals,'stock')]);return ex,cl

def localize(item,pred,method,seed,endpoint):
    ex,cl=residuals(item,pred);c=item.case;ref=item.ref;ids={int(b[0]):i for i,b in enumerate(c['bus'])};reg=read(OLD/'data/regions.json');adj={i:[] for i in range(300)}
    for k,b in enumerate(c['branch']):
      if b[10] and b[2]**2+b[3]**2<1e-6:
        for bus in [int(b[0]),int(b[1])]:adj[ids[bus]].append(k+1)
    rows=[];top=set(np.argsort(abs(ex[0]))[-10:].tolist()+np.argsort(abs(ex[1]))[-10:].tolist());slack=next(i for i,b in enumerate(c['bus']) if b[1]==3)
    for i in sorted(top,key=lambda i:-max(abs(ex[0,i]),abs(ex[1,i]))):
      bid=int(c['bus'][i][0]);rows.append(dict(method=method,seed=seed,endpoint=endpoint,scenario_id=item.record['scenario_id'],original_bus_id=bid,area=int(c['bus'][i][6]),regions=[j for j,m in enumerate(reg['memberships']) if bid in m],exact_outgoing_minus_injection_P_MW=float(ex[0,i]),exact_Q_MVAr=float(ex[1,i]),stock_P_MW=float(cl[0,i]),stock_Q_MVAr=float(cl[1,i]),Vm_pred=pred['vm'][i],Vm_ref=ref['vm'][i],angle_error_deg=wrap_degrees((pred['va_deg'][i]-pred['va_deg'][slack])-(ref['va_deg'][i]-ref['va_deg'][slack])),adjacent_clamped_branch_rows=adj[i],incident_branches=[dict(row=k+1,from_bus=int(b[0]),to_bus=int(b[1]),r=b[2],x=b[3],b=b[4],tap=b[8],shift_deg=b[9]) for k,b in enumerate(c['branch']) if bid in [int(b[0]),int(b[1])]],generator_errors=[dict(row=j+1,P_error_MW=pred['pg_mw'][j]-ref['pg_mw'][j],Q_error_MVAr=pred['qg_mvar'][j]-ref['qg_mvar'][j]) for j,g in enumerate(c['gen']) if int(g[0])==bid]))
    metrics=evaluate(c,pred);assert abs(max(abs(ex[0]))-metrics['max_p_residual_mw'])<1e-7;assert abs(max(abs(ex[1]))-metrics['max_q_residual_mvar'])<1e-7
    return rows,dict(exact_P_max_MW=float(max(abs(ex[0]))),exact_Q_max_MVAr=float(max(abs(ex[1]))),stock_P_max_MW=float(max(abs(cl[0]))),stock_Q_max_MVAr=float(max(abs(cl[1]))),same_state_max_operator_difference_P_MW=float(max(abs(ex[0]-cl[0]))),same_state_max_operator_difference_Q_MVAr=float(max(abs(ex[1]-cl[1]))),top_bus_clamp_adjacent_count=sum(bool(adj[i]) for i in top),top_bus_count=len(top))

def main():
    freeze=read(RUN/'freeze.json');assert sha(RUN/'config.json')==freeze['config_sha256'];assert sha(RUN/'calibration.json')==freeze['calibration_sha256'];assert sha(REPO/'scripts/python/physics_metrics.py')==freeze['metric_code_sha256'];assert sha(OLD/'baselines/linear-models.npz')==freeze['baseline_sha256']
    if (RUN/'evaluation/all-rows.json').exists():raise RuntimeError('Preserve existing locked evaluation; do not duplicate')
    fits=read(RUN/'training-summary.json');manifest=read(RUN/'data/manifest.json');slices={k:load_split(k,manifest) for k in ['ordinary','spatial','higher_load']};train=load_split('train',read(OLD/'data/manifest.json'));allrows=[];allloc=[];oprows=[]
    # References undergo the same exact versus stock comparison, without model predictions.
    for split,items in slices.items():
      for item in items:
        _,diag=localize(item,item.ref,'reference',None,'reference');oprows.append(dict(method='reference',seed=None,endpoint='reference',split=split,scenario_id=item.record['scenario_id'],**diag))
    z=np.load(OLD/'baselines/linear-models.npz');X=np.array([[b[2] for b in t.case['bus']]+[b[3] for b in t.case['bus']] for t in train]);Xz=(X[:,z['mask']]-z['xm'][z['mask']])/z['xs'][z['mask']]
    def baseline(item,method):
      x=np.r_[[b[2] for b in item.case['bus']],[b[3] for b in item.case['bus']]];x=(x[z['mask']]-z['xm'][z['mask']])/z['xs'][z['mask']]
      if method=='nearest':return copy.deepcopy(train[int(np.argmin(np.sum((Xz-x)**2,axis=1)))].ref)
      y=((x-z['xbar'])@z['W']+z['ybar'])*np.where(z['outmask'],z['ys'],1)+z['ym'];y[~z['outmask']]=z['ym'][~z['outmask']];return decode_vector(y)
    def collect(method,seed,endpoint,step,split,items,preds,meta):
      rows=[];raw=[];loc=[]
      for item,p in zip(items,preds):
        deadline();r=score(item.case,p,item.ref);r.update(method=method,seed=seed,endpoint=endpoint,update=step,split=split,scenario_id=item.record['scenario_id'],pair_id=item.record.get('pair_id'),joint_log_balance=float(np.log1p(max(r['max_p_residual_mw'],r['max_q_residual_mvar']))),**meta);rows.append(r);raw.append(dict(scenario_id=item.record['scenario_id'],prediction=p,metrics=r))
        if endpoint in ['selected','1000','baseline']:
          ll,diag=localize(item,p,method,seed,endpoint);loc.extend(ll);oprows.append(dict(method=method,seed=seed,endpoint=endpoint,split=split,scenario_id=item.record['scenario_id'],**diag))
      save(RUN/f'evaluation/{method}-{seed}-{endpoint}-{split}.json',raw);save(RUN/f'localization/{method}-{seed}-{endpoint}-{split}.json',loc);return rows
    for method in ['nearest','ridge','frozen']:
      model=make_model('F',11) if method=='frozen' else None
      for split,items in slices.items():
        if model:
          with torch.no_grad():preds=[physical_state(model(it.batch())) for it in items]
        else:preds=[baseline(it,method) for it in items]
        allrows.extend(collect(method,None,'baseline',0,split,items,preds,dict(training_seconds=0.,trainable_parameters=0 if method!='ridge' else int(z['W'].size))))
      del model;gc.collect();log('BASELINE_EVALUATED',method=method)
    for f in fits:
      if f['status'] not in ['COMPLETE','PARTIAL']:continue
      model=make_model(f['arm'],f['seed']);available=f['checkpoints'];endpoints={'selected':f['selected_checkpoint']}
      for step in [1000,200,500]:
        if str(step) in available:endpoints[str(step)]=available[str(step)]
      cache={}
      for endpoint,path in endpoints.items():
        if path not in cache:
          assert sha(path)==next(x['sha256'] for x in freeze['checkpoints'] if x['path']==path);blob=load_checkpoint(model,path);model.eval();preds_by_split={}
          with torch.no_grad():
            for split,items in slices.items():preds_by_split[split]=[physical_state(model(it.batch())) for it in items]
          # A second strict reload must reproduce a saved raw state exactly.
          load_checkpoint(model,path)
          with torch.no_grad():assert preds_by_split['ordinary'][0]==physical_state(model(slices['ordinary'][0].batch()))
          cache[path]=(blob['update'],preds_by_split)
        step,preds=cache[path];meta=dict(training_seconds=f['training_seconds'],peak_RSS_bytes=f['peak_RSS_bytes'],trainable_parameters=f['trainable'],actual_fit_updates=f['actual_updates'],selected_update=f['selected_update'],stop_reason=f['stop_reason'])
        for split,items in slices.items():allrows.extend(collect(f['arm'],f['seed'],endpoint,step,split,items,preds[split],meta))
      del model,cache;gc.collect();save(RUN/'evaluation/partial-rows.json',allrows);log('FIT_EVALUATED',seed=f['seed'],arm=f['arm'])
    save(RUN/'evaluation/all-rows.json',allrows);save(RUN/'localization/operator-comparisons.json',oprows);log('EXPERIMENT7_COMPLETE',rows=len(allrows),strict_feasible=sum(x['all_tested_constraints_pass'] for x in allrows))
if __name__=='__main__':main()
