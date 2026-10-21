from common import *
import gc

def checkpoint(m,opt,step,path,order):
 torch.save(dict(model_state=m.state_dict(),optimizer_state=opt.state_dict(),update=step,python_rng=random.getstate(),torch_rng=torch.get_rng_state(),numpy_rng=np.random.get_state(),order=order),path)
def train_one(net,ss,global_start):
 tr=dataset(net,'train');va=dataset(net,'validation');cfg=read(RUN/f'config-{net}.json');cfg['train']['seed']=ss;m=make_model(ss);opt=build_optimizer(m,cfg['train']);scheduler=build_scheduler(opt,cfg['train']);pool=ClosurePool(0,'superlu');warm={};fn,fh=official_forward(m,tr+va,cfg,pool,warm);p=RUN/f'fits/{net}-s{ss}';p.mkdir(parents=True,exist_ok=False);save(p/'config.json',cfg);start=time.perf_counter();update=0;selected=None;trace=[];vals=[];saved={};checkpoint(m,opt,0,p/'initial.pt',[])
 try:
  for epoch in range(1,31):
   indices=list(range(len(tr)));random.shuffle(indices);m.train()
   for ix in indices:
    guard()
    if time.perf_counter()-start>=1500 or time.perf_counter()-global_start>=7200:break
    it=tr[ix];t=time.perf_counter();opt.zero_grad(set_to_none=True);loss,d=fn([it.key],tol=curriculum_tol(epoch,25,.1,1e-8),wc=32.,train_mode=True);finite(loss,'fit loss');loss.backward()
    disconnected=[]
    for name,param in m.named_parameters():
     if param.grad is not None:finite(param.grad,name)
     elif epoch==1 and update==0:disconnected.append(name)
    gn=float(torch.nn.utils.clip_grad_norm_(m.parameters(),1.));assert math.isfinite(gn);opt.step();update+=1;r=dict(epoch=epoch,update=update,scenario_id=it.key,seconds=time.perf_counter()-t,lr=opt.param_groups[0]['lr'],tol=curriculum_tol(epoch,25,.1,1e-8),total_loss=float(loss.detach()),gradient_norm=gn,**d,**guard())
    trace.append(r)
    with (p/'trace.jsonl').open('a') as ff:ff.write(json.dumps(r)+'\n')
    if update==1:save(p/'parameter-audit.json',dict(total=sum(q.numel() for q in m.parameters()),requires_grad=sum(q.numel() for q in m.parameters() if q.requires_grad),no_gradient_names=disconnected,training_seed=ss,initial_checkpoint=sha(CKPT)))
    if update in [200,1250,1500]:checkpoint(m,opt,update,p/f'update-{update}.pt',indices);saved[update]=str(p/f'update-{update}.pt')
   scheduler.step()
   if update%len(tr)==0 and update:
    v=val_epoch(m,fn,va);v.update(update=update,epoch=epoch,eligible=v['fraction_converged']>=.99);vals.append(v)
    if v['eligible'] and (selected is None or v['score']<selected['score']):
     checkpoint(m,opt,update,p/'selected.pt',indices);selected={k:v[k] for k in ['update','epoch','score','fraction_converged']};selected['checkpoint']=str(p/'selected.pt')
    save(p/'validation.json',vals);log('FIT_EPOCH',network=net,seed=ss,update=update,score=v['score'],converged=v['fraction_converged'],selected=selected['update'] if selected else None,fit_seconds=time.perf_counter()-start)
   if time.perf_counter()-start>=1500 or time.perf_counter()-global_start>=7200 or update>=1500:break
  final=p/f'update-{update}.pt'
  if not final.exists():checkpoint(m,opt,update,final,[])
  saved[update]=str(final)
  status=dict(status='COMPLETE' if update==1500 else 'PARTIAL',network=net,seed=ss,updates=update,selected=selected,selection_status='SELECTED' if selected else 'SELECTION_FAILED',final_checkpoint=str(final),checkpoints=saved,fit_seconds=time.perf_counter()-start,resources=guard(),source_function_sha256=fh,validation=vals)
  # Strict reload verifies prediction equality at actual final weights.
  m.eval()
  with torch.no_grad():pred=physical(m(tr[0].batch()))
  m.load_state_dict(torch.load(final,weights_only=False,map_location='cpu')['model_state'],strict=True)
  with torch.no_grad():assert physical(m(tr[0].batch()))==pred
  status['strict_reload_equal']=True;save(p/'summary.json',status);log('FIT_COMPLETE',network=net,seed=ss,updates=update,seconds=status['fit_seconds']);return status
 except Exception:
  checkpoint(m,opt,update,p/f'failure-{update}.pt',[]);(p/'failure.txt').write_text(traceback.format_exc());raise
 finally:pool.shutdown();del m,opt,fn;gc.collect()
def main():
 assert read(RUN/'checks/gate.json')['status']=='PASS';assert not (RUN/'training-start.json').exists();start=time.perf_counter();save(RUN/'training-start.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cap_seconds=7200));summaries=[]
 for ss in [11,22,33]:
  for net in ['case300','pglib118']:
   if time.perf_counter()-start>=7200:summaries.append(dict(network=net,seed=ss,status='NOT_RUN_FIT_CAP'));continue
   summaries.append(train_one(net,ss,start));save(RUN/'training-summary.json',summaries)
 log('ALL_FITS_COMPLETE',seconds=time.perf_counter()-start);save(RUN/'training-duration.json',dict(seconds=time.perf_counter()-start))
if __name__=='__main__':
 try:main()
 except Exception:(RUN/'training-failure.txt').write_text(traceback.format_exc());raise
