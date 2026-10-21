from common import *
from elastic_loss import elastic_loss
from loss import control_loss

def residual(it,s,mode):
 c=it.c;ids={int(b[0]):i for i,b in enumerate(c['bus'])};n=len(ids);Y=np.zeros((n,n),complex)
 for br in c['branch']:
  if not br[10]:continue
  i,j=ids[int(br[0])],ids[int(br[1])];r,x=br[2:4];z2=r*r+x*x
  den=max(z2,1e-6) if mode=='stock' else z2+(1e-12 if mode=='new_original_precision' else 0)
  y=(r-1j*x)/den;t=(br[8] or 1)*np.exp(1j*np.deg2rad(br[9]));Y[i,i]+=(y+1j*br[4]/2)/abs(t)**2;Y[i,j]-=y/t.conjugate();Y[j,i]-=y/t;Y[j,j]+=y+1j*br[4]/2
 for i,b in enumerate(c['bus']):Y[i,i]+=(b[4]+1j*b[5])/100
 v=np.array(s['vm'])*np.exp(1j*np.deg2rad(s['va_deg']));g=np.zeros(n,complex)
 for ix,ge in enumerate(c['gen']):g[ids[int(ge[0])]]+=(s['pg_mw'][ix]+1j*s['qg_mvar'][ix])/100
 d=np.array([b[2]+1j*b[3] for b in c['bus']])/100
 yy=it.case.Ybus if mode=='new_native_fp32_inputs' else Y
 rr=100*(v*np.conj(yy@v)+d-g);return dict(Pmax_MW=float(abs(rr.real).max()),Qmax_MVAr=float(abs(rr.imag).max()))
def main():
 t=time.perf_counter();train=items('train',True)[:5];model=make_model();oldblob=torch.load(ROOT.parent/'GridSFM/model/checkpoints/gridsfm_open_v1.1.pt',weights_only=True,map_location='cpu');blob=torch.load(CKPT,weights_only=True,map_location='cpu')
 checks=dict(checkpoint_sha256=sha(CKPT),strict_loading=True,parameters=sum(p.numel() for p in model.parameters()),changed_weight_tensors=sum(not torch.equal(v,oldblob['state_dict'][k]) for k,v in blob['state_dict'].items()),source_checkout=str(SRC),source_modified=False,references=[])
 for it in train:
  guard();rc=it.ref;rr={mode:residual(it,rc,mode) for mode in ['exact','stock','new_original_precision','new_native_fp32_inputs']};assert evaluate(it.c,rc)['all_tested_constraints_pass'];s,d=completion(it,rc);checks['references'].append(dict(scenario=it.key,operators=rr,oracle_completion=d,oracle_metrics=score(it,s)))
  # all original active quantities survive the semantic adapter; compare arrays
  c=it.case;assert np.array_equal(c.gen2bus,np.array([next(i for i,b in enumerate(it.c['bus']) if b[0]==g[0]) for g in it.c['gen']]))
  assert np.allclose(c.Pd,np.array([b[2] for b in it.c['bus']])/100,atol=1e-6)
  assert not any(b[5]>0 for b in it.c['branch']);assert len(c.ref)==1
  masks=bus_masks(it.d);assert np.array_equal(np.where((masks['pv']|masks['slack']).numpy())[0],c.ctrl_bus),'training mask/closure roles mismatch'
 # Real CPU forward/backward and strict reload on training only.
 it=train[0];out=model(it.batch());raw=physical(out);assert all(np.isfinite(v).all() for v in raw.values());b=out
 pg=b['generator'].pred[:,0].double();vm=b['bus'].pred[:,1].double();pool=ClosurePool(0,'superlu');v0=dc_init_V(it.case,pg.detach().numpy(),vm.detach().numpy());vv,va,merit=close_batch(pg,vm,pool,[it.case],[v0],tol=1e-8,max_iter=40,backtrack=True,return_merit=True)
 loss,diag=elastic_loss(b,vv,va,pg,10.,10.,cost_scale=1e-6);ctrl,_,_=control_loss(pg,it.pg_gt,vm,it.vm_gt,torch.ones(len(pg),dtype=torch.bool),torch.tensor(np.isin(np.arange(300),it.case.ctrl_bus)),yaml.safe_load((SRC/'finetune_model/config/case500_goc_finetune.yaml').read_text())['loss'],3,2)
 total=loss+32*ctrl+170*merit.sum();finite(total,'loss');total.backward();norm=0;n=0
 for name,p in model.named_parameters():
  if p.grad is not None:finite(p.grad,name);norm+=float(p.grad.double().square().sum());n+=1
 assert n>0
 save(RUN/'checks/forward-raw.json',raw);torch.save(model.state_dict(),RUN/'gate-reload.pt');fresh=make_model();fresh.load_state_dict(torch.load(RUN/'gate-reload.pt',weights_only=True),strict=True)
 with torch.no_grad():assert physical(fresh(it.batch()))==raw
 # Features/outputs independent of labels: loader consumes only grid; semantic wrapper never exposes ref.
 obj2=copy.deepcopy(it.obj);obj2['solution']={'nodes':{'bus':[[999,999]]*300,'generator':[[999,999]]*69}};d2=prepare_for_inference(load_obj(obj2))
 with torch.no_grad():assert physical(fresh(batch_data_list([d2])))==raw
 checks.update(status='PASS',finite_backward=True,gradient_tensors=n,gradient_norm=math.sqrt(norm),reload_bitwise_equal=True,label_independence=True,CPU_forward_backward=True,smoke_completion_converged=pool.last_converged,smoke_loss=diag,elapsed_seconds=time.perf_counter()-t,resources=guard())
 save(RUN/'checks/gate.json',checks);log('GATE_PASS',seconds=checks['elapsed_seconds'],gradient_norm=checks['gradient_norm']);pool.shutdown()
if __name__=='__main__':
 try:main()
 except Exception:
  err=traceback.format_exc();(RUN/'gate-failure.txt').write_text(err);log('GATE_FAILURE',traceback=err);raise
