from common import *
from elastic_loss import elastic_loss,curriculum_tol
from loss import control_loss
from optim import build_optimizer,build_scheduler
import gc,subprocess

def cfg_build(train):
 cfg=yaml.safe_load((SRC/'finetune_model/config/case500_goc_finetune.yaml').read_text());cfg['runtime']['device']='cpu';cfg['train'].update(batch=1,seed=11);cfg['closure']['workers']=0
 cfg['study']=dict(max_updates=200,max_fit_seconds=1800,max_adaptation_phase_seconds=2700,source_config='case500_goc_finetune.yaml',schedule='50 cases per epoch, preserve original horizons: LR400 epochs; tol25 epochs; do not compress to4 epochs',selection='aggregate available-generator absolute Pg error / aggregate |referencePg| *100 + 1000*control-voltage MAE in pu; exact tie chooses earlier update; initial not eligible',source_checkout=str(SRC),base_checkpoint=str(CKPT),dtype='FP32 backbone/native features, FP64 closure arithmetic from native FP32 inputs',export_adapter='capability-range affine distribution at each generator bus; no clipping; output only',development_comparison=True)
 cfg['resolved_topk']=dict(pg=max(1,round(.0435*69)),v=max(1,round(.0254*len(train[0].case.ctrl_bus))))
 nominal=np.mean([np.sum(abs(t.case.cp1)*t.case.Pmax+t.case.cp2*t.case.Pmax**2) for t in train]);cfg['resolved_cost_scale']=1/max(nominal,1e-9)
 return cfg

def controls_val(m,vs):
 m.eval();ne=de=ve=0.;nv=0
 with torch.no_grad():
  for it in vs:
   out=m(it.batch());pg=out['generator'].pred[:,0].double();v=out['bus'].pred[:,1].double();ctrl=it.case.ctrl_bus
   ne+=float(abs(pg-it.pg_gt).sum());de+=float(abs(it.pg_gt).sum());ve+=float(abs(v[ctrl]-it.vm_gt[ctrl]).sum());nv+=len(ctrl)
 return dict(pg_percent=100*ne/max(de,1e-9),Vctrl_MAE_pu=ve/max(nv,1),selection_score=100*ne/max(de,1e-9)+1000*ve/max(nv,1))

def eval_model(m,its,label):
 m.eval();rows=[]
 with torch.no_grad():
  for it in its:
   guard();t=time.perf_counter();out=m(it.batch());raw=physical(out);ti=time.perf_counter()-t;t=time.perf_counter();s,d=completion(it,raw);tc=time.perf_counter()-t
   row=dict(scenario_id=it.key,raw=raw,completed=s,raw_metrics=score(it,raw),completed_metrics=score(it,s),completion=d,model_seconds=ti,completion_seconds=tc,preprocessing_seconds=it.prep_s)
   rows.append(row)
 save(RUN/f'evaluation/{label}.json',rows);log('EVALUATED',label=label,n=len(rows),converged=sum(r['completion']['converged'] for r in rows),strict_feasible=sum(r['completed_metrics']['all_tested_constraints_pass'] for r in rows));return rows

def train_model(train,val,cfg):
 t0=time.perf_counter();m=make_model();opt=build_optimizer(m,cfg['train']);sched=build_scheduler(opt,cfg['train']);pool=ClosurePool(0,'superlu');warm={};trace=[];vals=[];checkpoints={};path=RUN/'checkpoints';path.mkdir(exist_ok=True)
 # Disposable real optimizer step and strict reload before starting fresh.
 def step(it,ep,update,smoke=False):
  m.train();opt.zero_grad(set_to_none=True);b=m(it.batch());pg=b['generator'].pred[:,0].double();vm=b['bus'].pred[:,1].double();c=it.case
  v0=warm.get(it.key,dc_init_V(c,pg.detach().numpy(),vm.detach().numpy()));tol=curriculum_tol(ep,25,.1,1e-8,'geometric')
  vv,va,merit=close_batch(pg,vm,pool,[c],[v0],tol=tol,max_iter=40,backtrack=True,return_merit=True)
  el,diag=elastic_loss(b,vv,va,pg,10.,10.,cfg['resolved_cost_scale']);ctrl,_,_=control_loss(pg,it.pg_gt,vm,it.vm_gt,torch.ones(len(pg),dtype=torch.bool),torch.tensor(np.isin(np.arange(300),c.ctrl_bus)),cfg['loss'],cfg['resolved_topk']['pg'],cfg['resolved_topk']['v'])
  loss=el+32.*ctrl+170.*merit.sum();finite(loss,'train loss');loss.backward()
  for n,p in m.named_parameters():
   if p.grad is not None:finite(p.grad,'gradient '+n)
  gn=float(torch.nn.utils.clip_grad_norm_(m.parameters(),1.));assert math.isfinite(gn);opt.step()
  for n,p in m.named_parameters():finite(p,'parameter '+n)
  if pool.last_converged[0]:warm[it.key]=vv.detach().numpy()*np.exp(1j*va.detach().numpy())
  else:warm.pop(it.key,None)
  return dict(update=update,epoch=ep,tol=tol,total_loss=float(loss.detach()),control_loss=float(ctrl.detach()),merit=float(merit.detach().sum()),unclipped_gradient_norm=gn,converged=pool.last_converged[0],iterations=pool.last_iters[0],lr=opt.param_groups[0]['lr'],**diag)
 smoke=step(train[0],1,0,True);m.eval()
 with torch.no_grad():p=physical(m(train[0].batch()))
 torch.save(m.state_dict(),path/'smoke.pt');reload=make_model();reload.load_state_dict(torch.load(path/'smoke.pt',weights_only=True),strict=True)
 with torch.no_grad():assert physical(reload(train[0].batch()))==p
 save(RUN/'checks/optimizer-smoke.json',dict(passed=True,trace=smoke,reload_equal=True));del m,opt,sched,reload;gc.collect()
 m=make_model();opt=build_optimizer(m,cfg['train']);sched=build_scheduler(opt,cfg['train']);warm={};torch.save(m.state_dict(),path/'initial.pt');tfit=time.perf_counter();best=None;selected=None;update=0
 save(RUN/'training-initial-validation.json',controls_val(m,val))
 for ep in range(1,5):
  order=list(range(50));random.shuffle(order)
  for ix in order:
   guard()
   if time.perf_counter()-tfit>=1800 or time.perf_counter()-t0>=2700:break
   update+=1;t=time.perf_counter();r=step(train[ix],ep,update);r.update(scenario_id=train[ix].key,seconds=time.perf_counter()-t,**guard());trace.append(r)
   with (RUN/'training-trace.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
   if update%25==0:log('TRAIN_PROGRESS',update=update,loss=r['total_loss'],seconds=time.perf_counter()-tfit)
  if update%50==0 and update:
   cp=path/f'update-{update}.pt';torch.save(dict(model_state=m.state_dict(),optimizer_state=opt.state_dict(),update=update,python_rng=random.getstate(),torch_rng=torch.get_rng_state()),cp);checkpoints[update]=str(cp);v=controls_val(m,val);v.update(update=update,checkpoint=str(cp));vals.append(v)
   if best is None or v['selection_score']<best:best=v['selection_score'];selected=v
   save(RUN/'validation.json',vals);log('VALIDATION',**v)
  sched.step()
  if update>=200 or time.perf_counter()-tfit>=1800 or time.perf_counter()-t0>=2700:break
 if update not in checkpoints:
  cp=path/f'update-{update}.pt';torch.save(dict(model_state=m.state_dict(),optimizer_state=opt.state_dict(),update=update),cp);checkpoints[update]=str(cp);v=controls_val(m,val);v.update(update=update,checkpoint=str(cp));vals.append(v)
  if best is None or v['selection_score']<best:selected=v
 f=dict(status='COMPLETE' if update==200 else 'PARTIAL',updates=update,selected=selected,final_checkpoint=checkpoints[update],checkpoints=checkpoints,fit_seconds=time.perf_counter()-tfit,adaptation_phase_seconds=time.perf_counter()-t0,validation=vals,resources=guard(),schedule='4 of400 LR epochs and4 of25 tolerance epochs; tol_final='+str(trace[-1]['tol']))
 save(RUN/'training-summary.json',f);pool.shutdown();return m,f

def main():
 start=time.perf_counter();gate=read(RUN/'checks/gate.json');assert gate['status']=='PASS';train=items('train',True);val=items('validation',True);assert len(train)==50 and len(val)==10
 cfg=cfg_build(train);save(RUN/'config.json',cfg)
 # Freeze model/config/adapter/checker and existing case identity BEFORE new outcomes.
 manifests=[OLD/'data/manifest.json',PREV/'data/manifest.json'];save(RUN/'freeze.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checkpoint_sha256=sha(CKPT),code_sha256={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')},config_sha256=sha(RUN/'config.json'),checker_sha256=sha(ROOT/'scripts/python/physics_metrics.py'),data_manifests={str(p):sha(p) for p in manifests},comparison='previously viewed development cases, no retuning'))
 ordinary=items('ordinary');model=make_model();eval_model(model,ordinary,'frozen-ordinary');del model;gc.collect()
 model,f=train_model(train,val,cfg)
 endpoints={'selected':f['selected']['checkpoint'],'final':f['final_checkpoint']}
 for label,cp in endpoints.items():
  model.load_state_dict(torch.load(cp,weights_only=False,map_location='cpu')['model_state'],strict=True);model.eval();eval_model(model,ordinary,label+'-ordinary')
 # One excluded warmup and3 sequential30-case repeats for new frozen and selected.
 timing=[]
 for label in ['frozen','selected']:
  if label=='frozen':model=make_model()
  else:model.load_state_dict(torch.load(f['selected']['checkpoint'],weights_only=False,map_location='cpu')['model_state'],strict=True)
  for repeat in [-1,0,1,2]:
   with torch.no_grad():
    its=ordinary[:1] if repeat==-1 else ordinary
    for it in its:
     guard();tt=time.perf_counter();out=model(it.batch());raw=physical(out);tm=time.perf_counter()-tt;tt=time.perf_counter();_,d=completion(it,raw);tc=time.perf_counter()-tt;timing.append(dict(method=label,repeat=repeat,scenario_id=it.key,model_seconds=tm,completion_seconds=tc,total_cached_seconds=tm+tc,converged=d['converged']))
  log('TIMING_COMPLETE',method=label)
 save(RUN/'timing.json',timing)
 # Optional existing shifts, no additional fitting or selection.
 for label in ['frozen','selected']:
  if label=='frozen':model=make_model()
  else:model.load_state_dict(torch.load(f['selected']['checkpoint'],weights_only=False,map_location='cpu')['model_state'],strict=True)
  for split in ['spatial','higher_load']:eval_model(model,items(split),label+'-'+split)
 save(RUN/'execution.json',dict(status='COMPLETE',elapsed_runner_seconds=time.perf_counter()-start,wall_seconds_since_original_start=time.time()-START,resources=guard(),N4='NOT RUN: documented projection/refinement implementation absent from pinned public source; no substitute algorithm',source_modified=False));log('RUN_COMPLETE',seconds=time.perf_counter()-start)
if __name__=='__main__':
 try:main()
 except Exception:
  err=traceback.format_exc();(RUN/'execution-failure.txt').write_text(err);log('EXECUTION_FAILURE',traceback=err);raise
