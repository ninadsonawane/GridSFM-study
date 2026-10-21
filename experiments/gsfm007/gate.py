from common import *
import gc

def main():
 assert read(RUN/'prepare-complete.json')['status']=='PASS';server=Server();checks={};seeds=[]
 for net in ['case300','pglib118']:
  tr=dataset(net,'train');cfg=recipe(net,tr);save(RUN/f'config-{net}.json',cfg);m=make_model(11);pool=ClosurePool(0,'superlu');fn,fh=official_forward(m,tr[:5],cfg,pool,{});rows=[]
  for it in tr[:5]:
   guard();assert score(it,it.ref)['all_tested_constraints_pass'];c=it.c;obj=it.obj
   assert obj['metadata']['bus_external_ids']==[int(b[0]) for b in c['bus']];assert obj['metadata']['gen_source_rows']==list(range(len(c['gen'])))
   # Source conversion has exact decimal inputs before native FP32 storage.
   for fam in ['ac_line','transformer']:
    for ri,fe in zip(obj['metadata'][fam+'_source_rows'],obj['grid']['edges'][fam]['features']):
     br=c['branch'][ri];assert fe[4:6]==br[2:4] if fam=='ac_line' else fe[2:4]==br[2:4];assert (fe[6] if fam=='ac_line' else fe[4])==br[5]/100
   oracle,meta=completion(it,it.ref);rows.append(dict(id=it.key,reference=score(it,it.ref),oracle=score(it,oracle),oracle_PF=meta['converged']))
  probe=tr[0];sm=[]
  for ep in [1,25]:
   m.zero_grad(set_to_none=True);t=time.perf_counter();loss,diag=fn([probe.key],tol=curriculum_tol(ep,25,.1,1e-8),wc=32.,train_mode=True);finite(loss,'smoke loss');loss.backward();gs=[]
   for name,p in m.named_parameters():
    if p.grad is not None:finite(p.grad,name);gs.append(name)
   sm.append(dict(epoch=ep,seconds=time.perf_counter()-t,gradient_tensors=len(gs),diag=diag,loss=float(loss.detach())))
  opt=build_optimizer(m,cfg['train']);torch.nn.utils.clip_grad_norm_(m.parameters(),1);opt.step();m.eval()
  with torch.no_grad():raw=physical(m(probe.batch()))
  cp=RUN/f'checks/{net}-smoke.pt';cp.parent.mkdir(parents=True,exist_ok=True);torch.save(m.state_dict(),cp);new=make_model(22);new.load_state_dict(torch.load(cp,weights_only=True),strict=True)
  with torch.no_grad():assert physical(new(probe.batch()))==raw
  altered=copy.deepcopy(probe.obj);altered['solution']={'nodes':{'bus':[[999,999]]*len(probe.c['bus']),'generator':[[999,999]]*len(probe.c['gen'])}};d=prepare_for_inference(load_obj(altered))
  with torch.no_grad():assert physical(new(batch_data_list([d])))==raw
  # Original problem and explicit distinct label-free starts; capture live Ipopt iteration zero.
  pilots=dataset('case300','ordinary')[:5] if net=='case300' else tr[:5]
  if net=='case300' and not pilots:raise ValueError('missing development pilot')
  consumption=[]
  for ix,it in enumerate(pilots):
   de=server.request(it,RUN/f'pilot/{net}/{ix}-default',remaining=30,capture=ix==0);assert de.get('metrics',{}).get('all_tested_constraints_pass'),de
   s=dict(vm=[1.0]*len(it.c['bus']),va_deg=[0.0]*len(it.c['bus']),pg_mw=[g[1] for g in it.c['gen']],qg_mvar=[g[2] for g in it.c['gen']]);wa=server.request(it,RUN/f'pilot/{net}/{ix}-explicit',s,30,capture=ix==0);assert wa.get('metrics',{}).get('all_tested_constraints_pass'),wa
   rawr=read(wa['result_path']);starts=rawr['initial_starts'];assert all(abs(starts['vm'][str(int(b[0]))]-1)<1e-12 for b in it.c['bus'])
   if ix==0:
    live=rawr['iteration_zero_primal']['actual_internal_unscaled_primal'];devr=read(de['result_path']);d_live=devr['iteration_zero_primal']['actual_internal_unscaled_primal'];delta=max(abs(live['pg'][k]-d_live['pg'][k]) for k in live['pg']);assert delta>1e-4
    constraints=rawr['network_fields'];assert len(constraints['branch'])==len(it.c['branch']);assert all(abs(constraints['branch'][str(j+1)].get('rate_a',0)-b[5]/100)<1e-10 for j,b in enumerate(it.c['branch']))
    assert all(abs(constraints['branch'][str(j+1)]['angmin']-math.radians(b[11]))<1e-10 and abs(constraints['branch'][str(j+1)]['angmax']-math.radians(b[12]))<1e-10 for j,b in enumerate(it.c['branch']))
    consumption.append(dict(id=it.key,live_start_diff_max_Pg_pu=delta,requested_start_exact=True,live_bound_projection_logged=True,default=de['result_path'],explicit=wa['result_path']))
  checks[net]=dict(status='PASS',reference_rows=rows,smokes=sm,optimizer_reload_exact=True,label_independence=True,source_function_sha256=fh,start_consumption=consumption,parameters=sum(p.numel() for p in m.parameters()),disconnected_prediction_heads=['head_theta','head_Qg','head_feas'],controls='all online Pg predictions; non-slack Pg + PV/slack Vm consumed by PF; no Q-limit switching',rated_branches=sum(b[5]>0 for b in tr[0].c['branch']),fixed_P_zero_regulators=sum(g[8]==g[9]==0 for g in tr[0].c['gen']))
  pool.shutdown();del m,new,opt,fn;gc.collect();log('GATE_NETWORK_PASS',network=net)
 server.close();save(RUN/'checks/gate.json',dict(status='PASS',networks=checks,resources=guard(),UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()));log('GATE_ALL_PASS')
if __name__=='__main__':
 try:main()
 except Exception:(RUN/'gate-failure.txt').write_text(traceback.format_exc());raise
