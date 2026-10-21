from calibrate import *
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

def fit(arm,seed,train,valid,rho):
    deadline()
    if COMPUTE_END-time.time()<1100: return dict(arm=arm,seed=seed,status='SKIPPED',stop_reason='insufficient measured fit/evaluation reserve')
    directory=RUN/f'training/seed-{seed}/{arm}';directory.mkdir(parents=True,exist_ok=False);order=read(RUN/f'orders/seed-{seed}.json')['indices'];model=make_model(arm,seed);manifest=trainable_manifest(model,arm);params=[p for p in model.parameters() if p.requires_grad];optimizer=torch.optim.AdamW(params,lr=1e-4,weight_decay=1e-4);monitor=MemoryMonitor();start=time.perf_counter();validation=[];paths={};updates=0;trace=[];reason=None
    initial_model_hash=content_hash({n:hashlib.sha256(p.detach().numpy().tobytes()).hexdigest() for n,p in model.state_dict().items()})
    def snapshot(step):
      rows,_=evaluate_model(model,valid,directory/f'validation-{step:04d}.json');path=directory/f'step-{step:04d}.pt';checkpoint(model,optimizer,arm,step,path,order);paths[step]=str(path)
      validation.append(dict(update=step,key=(*val_score(rows),step),checkpoint=str(path)));save(directory/'validation-trace.json',validation)
      if seed==11 and arm=='E' and step in [0,200,500,1000]:save(directory/f'operator-probe-{step:04d}.json',probes(model,train[:5],True,rho or 1.))
      log('FIT_CHECKPOINT',seed=seed,arm=arm,update=step,score=validation[-1]['key'][0],elapsed_seconds=time.perf_counter()-start)
    try:
      snapshot(0)
      for step in range(1,1001):
        deadline()
        if time.perf_counter()-start>=900:reason='15-minute fit cap';break
        if monitor.stop_reason:reason=monitor.stop_reason;break
        it=train[order[step-1]];t=time.perf_counter();model.train();optimizer.zero_grad(set_to_none=True);out=model(it.batch());loss,parts=objective(out,it.physics,arm,rho or 1.);loss.backward();grads=check_gradients(model);clip=torch.nn.utils.clip_grad_norm_(params,1.);optimizer.step();updates=step
        record=dict(update=step,scenario_id=it.record['scenario_id'],update_seconds=time.perf_counter()-t,loss=parts,gradient=grads,clipping_input_norm=float(clip),was_clipped=bool(clip>1.),rss_bytes=psutil.Process().memory_info().rss,available_bytes=psutil.virtual_memory().available);trace.append(record)
        with (directory/'train-trace.jsonl').open('a') as f:f.write(json.dumps(record,allow_nan=False)+'\n')
        if step%50==0:snapshot(step)
      if updates not in paths:snapshot(updates)
      selected=min(validation,key=lambda x:tuple(x['key']));model.eval();before=physical_state(model(valid[0].batch()));load_checkpoint(model,paths[updates]);assert before==physical_state(model(valid[0].batch()))
      result=dict(arm=arm,seed=seed,status='COMPLETE' if updates==1000 else 'PARTIAL',actual_updates=updates,selected_update=selected['update'],selected_checkpoint=selected['checkpoint'],checkpoints=paths,validation=validation,training_seconds=time.perf_counter()-start,median_seconds_per_update=float(np.median([x['update_seconds'] for x in trace])),p95_seconds_per_update=float(np.percentile([x['update_seconds'] for x in trace],95)),clipping_fraction=float(np.mean([x['was_clipped'] for x in trace])),peak_RSS_bytes=monitor.peak,minimum_available_bytes=monitor.minimum_available,stop_reason=reason,initial_model_hash=initial_model_hash,reload_equivalence=True,**manifest)
    except Exception as e:
      reason=repr(e);save(directory/'failure.json',dict(error=reason,traceback=traceback.format_exc(),updates=updates));checkpoint(model,optimizer,arm,updates,directory/'failure.pt',order);result=dict(arm=arm,seed=seed,status='FAILED',actual_updates=updates,stop_reason=reason,checkpoints=paths,training_seconds=time.perf_counter()-start,peak_RSS_bytes=monitor.peak)
    finally:
      monitor.stop();del model,optimizer,params
      if 'out' in locals():del out,loss
      gc.collect()
    save(directory/'summary.json',result);log('FIT_COMPLETE',seed=seed,arm=arm,status=result['status'],updates=updates,selected=result.get('selected_update'),seconds=result['training_seconds']);return result

def main():
    assert read(RUN/'checks.json')['status']=='PASS'
    if (RUN/'training').exists():raise RuntimeError('Existing worker/fits must not restart')
    calibration=read(RUN/'calibration.json');rho=calibration['rho'];manifest=read(OLD/'data/manifest.json');train=load_split('train',manifest);valid=load_split('validation',manifest);fits=[]
    for seed,arms in [(11,['S','C','E','C_m']),(22,['C','E','C_m','S']),(33,['E','C_m','S','C'])]:
      for arm in arms:
        if arm=='C_m' and rho is None:continue
        result=fit(arm,seed,train,valid,rho);fits.append(result);save(RUN/'training-summary.json',fits)
        if result['status']=='FAILED' or ('memory' in (result.get('stop_reason') or '') or 'RSS' in (result.get('stop_reason') or '')):raise RuntimeError('Failed fit or memory stop; retained state')
    checkpoint_rows=[]
    for fitrow in fits:
      for k,path in fitrow.get('checkpoints',{}).items():checkpoint_rows.append(dict(seed=fitrow['seed'],arm=fitrow['arm'],update=int(k),path=path,sha256=sha(path)))
    save(RUN/'freeze.json',dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),config_sha256=sha(RUN/'config.json'),calibration_sha256=sha(RUN/'calibration.json'),metric_code_sha256=sha(REPO/'scripts/python/physics_metrics.py'),baseline_sha256=sha(OLD/'baselines/linear-models.npz'),training_summary_sha256=sha(RUN/'training-summary.json'),checkpoints=checkpoint_rows,selected=[dict(seed=x['seed'],arm=x['arm'],update=x.get('selected_update'),path=x.get('selected_checkpoint')) for x in fits],fresh_evaluation_opened=False))
    log('EXPERIMENT6_COMPLETE',fits=len(fits),completed=sum(x['status']=='COMPLETE' for x in fits),freeze_sha256=sha(RUN/'freeze.json'))
if __name__=='__main__':main()
