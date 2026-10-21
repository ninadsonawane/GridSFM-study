"""Cheap baselines followed by at most six matched seed11 fits and held-out development scoring."""
from neural import *
import psutil,threading,traceback
class MemoryMonitor:
    def __init__(self):self.peak=0;self.minimum_available=2**64;self.stop_reason=None;self.finished=threading.Event();self.thread=threading.Thread(target=self.loop,daemon=True);self.thread.start()
    def loop(self):
        while not self.finished.is_set():
            try:
                proc=psutil.Process();rss=proc.memory_info().rss+sum(p.memory_info().rss for p in proc.children(recursive=True));avail=psutil.virtual_memory().available;self.peak=max(self.peak,rss);self.minimum_available=min(self.minimum_available,avail)
                if rss>32*2**30:self.stop_reason='RSS exceeded32GiB'
                if avail<12*2**30:self.stop_reason='available memory below12GiB'
            except psutil.Error:pass
            self.finished.wait(.2)
    def stop(self):self.finished.set();self.thread.join()
def metric_rows(method,seed,split,checkpoint_name,updates,rows,meta):
    return [{'method':method,'seed':seed,'split':split,'checkpoint':checkpoint_name,'actual_updates':updates,**r,**meta} for r in rows]
def cheap_baselines(train,valid,slices):
    X=np.array([[b[2] for b in it.case['bus']]+[b[3] for b in it.case['bus']] for it in train]);Y=np.array([encode_state(it.ref) for it in train]);xm=X.mean(axis=0);xs=X.std(axis=0);mask=xs>1e-12;Xz=(X[:,mask]-xm[mask])/xs[mask];ym=Y.mean(axis=0);ys=Y.std(axis=0);outmask=ys>1e-12;Yz=np.zeros_like(Y);Yz[:,outmask]=(Y[:,outmask]-ym[outmask])/ys[outmask]
    def features(item):
        a=np.r_[[b[2] for b in item.case['bus']],[b[3] for b in item.case['bus']]];return (a[mask]-xm[mask])/xs[mask]
    def predict_nearest(it):return train[int(np.argmin(np.sum((Xz-features(it))**2,axis=1)))].ref
    candidates=[];start=time.perf_counter();proc=psutil.Process();rss0=proc.memory_info().rss
    for alpha in [.01,1.,100.]:
        # Dual ridge, an explicit unpenalized intercept and training-only scalers.
        xbar=Xz.mean(axis=0);ybar=Yz.mean(axis=0);xc=Xz-xbar;yc=Yz-ybar;W=xc.T@np.linalg.solve(xc@xc.T+alpha*np.eye(len(train)),yc)
        def ridge(it,W=W,xbar=xbar,ybar=ybar):
            y=((features(it)-xbar)@W+ybar)*np.where(outmask,ys,1)+ym;y[~outmask]=ym[~outmask];return decode_vector(y)
        rows=[score(it.case,ridge(it),it.ref) for it in valid];key=(*val_score(rows),-alpha);candidates.append((key,alpha,W,xbar,ybar))
    winner=min(candidates,key=lambda x:x[0]);_,alpha,W,xbar,ybar=winner;fit_seconds=time.perf_counter()-start
    save(RUN/'baselines/ridge-selection.json',{'alpha':alpha,'candidates':[{'alpha':a,'validation_key':k} for k,a,*_ in candidates],'fit_seconds_including3_validation_candidates':fit_seconds,'input_columns':int(mask.sum()),'dropped_constant_input_columns':int((~mask).sum()),'constant_output_columns':int((~outmask).sum()),'preprocessing_fit_split':'train only','extra_tuning_budget':3})
    np.savez(RUN/'baselines/linear-models.npz',xm=xm,xs=xs,mask=mask,ym=ym,ys=ys,outmask=outmask,W=W,xbar=xbar,ybar=ybar)
    def predict_ridge(it):
        y=((features(it)-xbar)@W+ybar)*np.where(outmask,ys,1)+ym;y[~outmask]=ym[~outmask];return decode_vector(y)
    allrows=[]
    for name,fn in [('nearest',predict_nearest),('ridge',predict_ridge)]:
        for split,items in slices.items():
            preds=[];rows=[]
            for it in items:
                deadline();p=fn(it);r=score(it.case,p,it.ref);r.update(scenario_id=it.record['scenario_id'],pair_id=it.record.get('pair_id'));rows.append(r);preds.append({'scenario_id':it.record['scenario_id'],'prediction':p,'metrics':r})
            save(RUN/f'baselines/{name}-{split}.json',preds);allrows+=metric_rows(name,None,split,'baseline',0,rows,{'trainable_parameters':int(W.size) if name=='ridge' else 0,'training_seconds':fit_seconds if name=='ridge' else 0.,'peak_RSS_bytes':max(rss0,proc.memory_info().rss),'stop_reason':None})
    frozen=make_model('F')
    for split,items in slices.items():
        rows,_=evaluate_model(frozen,items,RUN/f'baselines/frozen-{split}.json');allrows+=metric_rows('frozen',None,split,'pretrained-v1.1',0,rows,{'trainable_parameters':0,'training_seconds':0.,'peak_RSS_bytes':proc.memory_info().rss,'stop_reason':None})
    del frozen;gc.collect();save(RUN/'baselines/rows.json',allrows);log('EXPERIMENT1_COMPLETE',ridge_alpha=alpha,rows=len(allrows));return allrows
def fit_arm(arm,train,valid,order,U,slow,validation_estimate):
    deadline();remaining=COMPUTE_END-time.time();estimate=min(1500,U*slow+validation_estimate+120)
    if remaining<estimate+180: return {'arm':arm,'status':'SKIPPED','reason':'remaining budget cannot accommodate measured fit plus final evaluation'}
    directory=RUN/'training'/arm;directory.mkdir(parents=True,exist_ok=False);monitor=MemoryMonitor();start=time.perf_counter();model=make_model(arm);manifest=trainable_manifest(model,arm);save(directory/'trainable-manifest.json',manifest);params=[p for p in model.parameters() if p.requires_grad];optimizer=torch.optim.AdamW(params,lr=1e-4,weight_decay=1e-4);trace=[];validation=[];paths={};updates=0;reason=None
    def validate_and_save(step):
        t=time.perf_counter();rows,_=evaluate_model(model,valid,directory/f'validation-{step:03d}.json');key=(*val_score(rows),step);path=directory/f'step-{step:03d}.pt';checkpoint(model,optimizer,arm,step,path,order);paths[step]=str(path);validation.append({'update':step,'key':key,'elapsed_seconds':time.perf_counter()-t,'checkpoint':str(path)});save(directory/'validation-trace.json',validation)
    try:
        validate_and_save(0)
        for step in range(1,U+1):
            deadline()
            if time.perf_counter()-start>=1500:reason='25-minute cap including validation/checkpointing';break
            if monitor.stop_reason:reason=monitor.stop_reason;break
            item=train[order[step-1]];t=time.perf_counter();model.train();optimizer.zero_grad(set_to_none=True);out=model(item.batch());loss,parts=objective(out,item.physics,arm);loss.backward();grads=check_gradients(model);clipped=torch.nn.utils.clip_grad_norm_(params,1.);optimizer.step();updates=step
            trace.append({'update':step,'scenario_id':item.record['scenario_id'],'update_seconds':time.perf_counter()-t,'loss':parts,'gradient':grads,'clipping_input_norm':float(clipped),'rss_bytes':psutil.Process().memory_info().rss,'available_memory_bytes':psutil.virtual_memory().available})
            with (directory/'train-trace.jsonl').open('a') as f:f.write(json.dumps(trace[-1],allow_nan=False)+'\n')
            if step%50==0:validate_and_save(step);log('FIT_CHECKPOINT',arm=arm,update=step,validation_score=validation[-1]['key'][0],elapsed=time.perf_counter()-start)
        if updates not in paths:validate_and_save(updates)
        selected=min(validation,key=lambda v:tuple(v['key']))
        result={'arm':arm,'status':'COMPLETE' if updates==U else 'PARTIAL','actual_updates':updates,'common_U':U,'selected_update':selected['update'],'selected_checkpoint':selected['checkpoint'],'fixed_checkpoint':paths[updates],'checkpoints':paths,'validation':validation,'training_seconds_including_validation_checkpointing':time.perf_counter()-start,'median_seconds_per_update':float(np.median([x['update_seconds'] for x in trace])) if trace else None,'p95_seconds_per_update':float(np.percentile([x['update_seconds'] for x in trace],95)) if trace else None,'process_tree_peak_RSS_bytes':monitor.peak,'minimum_available_memory_bytes':monitor.minimum_available,'stop_reason':reason,**manifest}
    except Exception as e:
        reason=repr(e);save(directory/'failure.json',{'error':reason,'traceback':traceback.format_exc(),'updates':updates});checkpoint(model,optimizer,arm,updates,directory/'failure-resume.pt',order);result={'arm':arm,'status':'FAILED','actual_updates':updates,'common_U':U,'stop_reason':reason,'checkpoints':paths,'training_seconds_including_validation_checkpointing':time.perf_counter()-start,'process_tree_peak_RSS_bytes':monitor.peak,**manifest}
    finally:
        monitor.stop();del model,optimizer,params
        if 'out' in locals():del out,loss
        gc.collect()
    save(directory/'summary.json',result);log('FIT_COMPLETE',arm=arm,status=result['status'],updates=updates,selected=result.get('selected_update'),seconds=result['training_seconds_including_validation_checkpointing']);return result
def main():
    if (RUN/'training-summary.json').exists() or (RUN/'training').exists():raise RuntimeError('Preserve existing fits; do not start a duplicate worker or restart this run')
    gate=read(RUN/'checks.json');assert gate['status']=='PASS';seed_all();U=gate['U'];smoke=read(RUN/'smoke-summary.json');data=read(RUN/'data/manifest.json');train=load_split('train',data);valid=load_split('validation',data);slices={k:load_split(k,data) for k in ['ordinary','spatial','higher_load']}
    (RUN/'baselines').mkdir(exist_ok=True);allrows=cheap_baselines(train,valid,slices);rng=np.random.Generator(np.random.PCG64(11));order=[]
    while len(order)<U:order.extend(rng.permutation(50).tolist())
    order=order[:U];save(RUN/'training-order.json',{'seed':11,'indices':order,'scenario_ids':[train[i].record['scenario_id'] for i in order]});fits=[]
    for arm in ['S','C','E','H','L','R']:
        fit=fit_arm(arm,train,valid,order,U,smoke['slowest_p95_seconds_per_update'],smoke['estimated_validation_seconds_per_fit']);fits.append(fit);save(RUN/'training-summary.json',fits)
        if fit.get('stop_reason') and ('memory' in fit['stop_reason'] or 'RSS' in fit['stop_reason']):break
    # All fits are complete before evaluating any development-slice learning outcome.
    for fit in fits:
        if fit['status'] not in ['COMPLETE','PARTIAL']:continue
        model=make_model(fit['arm']);evaluated={}
        endpoints={'selected':fit['selected_checkpoint'],'fixed_U':fit['fixed_checkpoint']}
        for endpoint,path in endpoints.items():
            if path in evaluated:
                raw=copy.deepcopy(evaluated[path]);
                for row in raw:row['checkpoint']=endpoint
                allrows.extend(raw);continue
            blob=load_checkpoint(model,path);rows_for_path=[]
            for split,items in slices.items():
                deadline();rows,_=evaluate_model(model,items,RUN/f'evaluation/{fit["arm"]}-{endpoint}-{split}.json')
                meta={'trainable_parameters':fit['trainable'],'training_seconds':fit['training_seconds_including_validation_checkpointing'],'median_seconds_per_update':fit['median_seconds_per_update'],'p95_seconds_per_update':fit['p95_seconds_per_update'],'peak_RSS_bytes':fit['process_tree_peak_RSS_bytes'],'stop_reason':fit['stop_reason']}
                rows_for_path+=metric_rows(fit['arm'],11,split,endpoint,blob['update'],rows,meta)
            evaluated[path]=rows_for_path;allrows.extend(rows_for_path)
        del model,blob;gc.collect();save(RUN/'evaluation/all-rows.json',allrows);log('EVALUATION_COMPLETE',arm=fit['arm'])
    save(RUN/'evaluation/all-rows.json',allrows);log('PILOT_COMPUTE_COMPLETE',fits=len(fits),completed=sum(f['status']=='COMPLETE' for f in fits),rows=len(allrows))
if __name__=='__main__':
    try:main()
    except Exception as e:
        save(RUN/'fit-stage-failure.json',{'error':repr(e),'traceback':traceback.format_exc()});log('FIT_STAGE_FAILURE',error=repr(e));raise
