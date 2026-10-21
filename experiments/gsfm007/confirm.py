from common import *
import gc,signal

class Ridge:
 def __init__(self,z):self.z=z
 def eval(self):return self
 def __call__(self,d):
  z=self.z;lx=d['load'].x.double().numpy();link=d['load','load_link','bus'].edge_index[1].numpy();X=np.zeros((d['bus'].x.shape[0],2));np.add.at(X,link,lx[:,:2]*100);x=np.r_[X[:,0],X[:,1]];xz=(x[z['xm_mask']]-z['xm'][z['xm_mask']])/z['xs'][z['xm_mask']];yz=(xz-z['xbar'])@z['W']+z['ybar'];y=yz*z['ys']+z['ym'];ng=d['generator'].x.shape[0];vm=np.ones(len(X));vm[z['ctrl_bus']]=y[ng:];d['generator'].pred=torch.tensor(np.c_[y[:ng]/100,np.zeros(ng)],dtype=torch.float64);d['bus'].pred=torch.tensor(np.c_[np.zeros(len(X)),vm],dtype=torch.float64);return d

def ridge_tune(net,tr,va,cfg):
 p=RUN/f'ridge/{net}';p.mkdir(parents=True,exist_ok=True);t=time.perf_counter();X=np.array([[b[2] for b in it.c['bus']]+[b[3] for b in it.c['bus']] for it in tr]);Y=np.array([it.ref['pg_mw']+[it.ref['vm'][i] for i in it.case.ctrl_bus] for it in tr]);xm=X.mean(0);xs=X.std(0);mask=xs>1e-12;xs=np.where(mask,xs,1);ym=Y.mean(0);ys=Y.std(0);ys=np.where(ys>1e-12,ys,1);xz=(X[:,mask]-xm[mask])/xs[mask];yz=(Y-ym)/ys;xb=xz.mean(0);yb=yz.mean(0);xc=xz-xb;yc=yz-yb;pool=ClosurePool(0,'superlu');scores=[];selected=None
 for alpha in [.01,1.,100.]:
  z=dict(xm=xm,xs=xs,xm_mask=mask,ym=ym,ys=ys,xbar=xb,ybar=yb,W=xc.T@np.linalg.solve(xc@xc.T+alpha*np.eye(len(tr)),yc),ctrl_bus=tr[0].case.ctrl_bus,alpha=alpha);np.savez(p/f'alpha-{alpha}.npz',**z);model=Ridge(z);fn,_=official_forward(model,tr+va,cfg,pool,{});v=val_epoch(model,fn,va);v.update(alpha=alpha,eligible=v['fraction_converged']>=.99,path=str(p/f'alpha-{alpha}.npz'));scores.append(v)
  if v['eligible'] and (selected is None or v['score']<=selected['score']):selected=v
 choice=selected or scores[1];summary=dict(status='SELECTED' if selected else 'SELECTION_FAILED',selected=selected,diagnostic_fixed_alpha1=None if selected else choice,chosen_path=choice['path'],candidates=scores,tuning_seconds=time.perf_counter()-t,controls_unclipped=True,PQ_initial_voltage='1pu; ridge predicts only PV/slack Vm');save(p/'summary.json',summary);pool.shutdown();return summary

def region_map(base):
 pos=sorted(int(b[0]) for b in base['bus'] if b[2]>0);adj={int(b[0]):set() for b in base['bus']}
 for b in base['branch']:
  if b[10]:adj[int(b[0])].add(int(b[1]));adj[int(b[1])].add(int(b[0]))
 def bfs(c):
  ds={c:0};q=collections.deque([c])
  while q:
   a=q.popleft()
   for b in sorted(adj[a]):
    if b not in ds:ds[b]=ds[a]+1;q.append(b)
  return ds
 cs=[pos[0]];ds=[bfs(cs[0])]
 while len(cs)<4:
  c=min((b for b in pos if b not in cs),key=lambda b:(-min(d[b] for d in ds),b));cs.append(c);ds.append(bfs(c))
 return dict(centers=cs,memberships=[sorted(pos,key=lambda b:(d[b],b))[:math.ceil(len(pos)/4)] for d in ds])

def generate(server):
 from prepare import label
 assert (RUN/'freeze.json').exists() and not (RUN/'confirmation-open.json').exists();save(RUN/'confirmation-open.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),freeze_sha256=sha(RUN/'freeze.json')));bases=read(RUN/'source-cases.json');seen=set()
 def key(c):return hashlib.sha256(json.dumps({k:c[k] for k in ['baseMVA','bus','gen','branch','gencost']},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 for p in (ROOT/'results').rglob('*input.json'):
  try:seen.add(key(read(p)))
  except (KeyError,TypeError):pass
 for p in (RUN/'data').rglob('input.json'):seen.add(key(read(p)))
 manifest={}
 for net in ['case300','pglib118']:
  base=bases[net];reg=region_map(base);save(RUN/f'confirmation/{net}-regions.json',reg);recs=[];ordinary=[]
  for split,ss,lo,hi in [('ordinary',7103003 if net=='case300' else 7101183,.9,1.03),('higher_load',7103005 if net=='case300' else 7101185,1.035,1.06)]:
   rng=np.random.Generator(np.random.PCG64(ss))
   for i in range(30):
    guard();scale=float(rng.uniform(lo,hi));j=rng.uniform(.98,1.02,len(base['bus']));c=copy.deepcopy(base)
    for b,f in zip(c['bus'],scale*j):b[2]*=float(f);b[3]*=float(f)
    h=key(c)
    if h in seen:recs.append(dict(scenario_id=f'{split}-{i:03d}',network=net,split=split,status='DUPLICATE',excluded=True));continue
    seen.add(h);r=label(server,c,net,split,i,dict(seed=ss,global_scale=scale,bus_jitter=j.tolist()));r['excluded']=False;recs.append(r)
    if split=='ordinary':ordinary.append(r)
  for j,r in enumerate(ordinary):
   guard();c=read(Path(r['path'])/'input.json');elig=[i for i,b in enumerate(c['bus']) if b[2]>0];region=set(reg['memberships'][j%4]);u=np.array([1 if int(c['bus'][i][0]) in region else -1 for i in elig],float);A=np.array([[c['bus'][i][k] for i in elig] for k in [2,3]]);norm=np.linalg.norm(A,axis=1);An=A[norm>0]/norm[norm>0,None];_,sv,Vh=np.linalg.svd(An,full_matrices=False);Vr=Vh[sv>1e-12*sv[0]];delta=u-Vr.T@(Vr@u)
   if max(abs(delta))<1e-10:recs.append(dict(scenario_id=f'spatial-{j:03d}',network=net,split='spatial',status='DEGENERATE',excluded=True,pair_id=r['scenario_id']));continue
   fac=1+(1 if (j//4)%2==0 else -1)*.1*delta/max(abs(delta));before=np.array([[b[2],b[3]] for b in c['bus']]);factors=np.ones(len(c['bus']));factors[elig]=fac
   for i,f in zip(elig,fac):c['bus'][i][2]*=float(f);c['bus'][i][3]*=float(f)
   after=np.array([[b[2],b[3]] for b in c['bus']]);drift=(after-before).sum(0);assert max(abs(drift))<1e-7
   h=key(c)
   if h in seen:recs.append(dict(scenario_id=f'spatial-{j:03d}',network=net,split='spatial',status='DUPLICATE',excluded=True,pair_id=r['scenario_id']));continue
   seen.add(h);rec=label(server,c,net,'spatial',j,dict(actual_factors=factors.tolist(),region=j%4));rec.update(excluded=False,pair_id=r['scenario_id'],P_Q_drift=drift.tolist(),moved_MW_MVAr=(abs(after-before).sum(0)/2).tolist());recs.append(rec)
  manifest[net]=recs;save(RUN/'confirmation/manifest.json',manifest);log('CONFIRMATION_GENERATED',network=net,candidates=len(recs),excluded=sum(r['excluded'] for r in recs),reference_feasible=sum(r.get('accepted',False) for r in recs))
 return manifest

def alarm_handler(*args):raise TimeoutError('30s end-to-end deadline')
def online(server,it,model,folder):
 start=time.perf_counter();deadline=start+30;times={};attempts=[];raw=None;pf=None;pfd=None;final=None;fm=None;status='FAILED';fallback=False;signal.signal(signal.SIGALRM,alarm_handler);signal.setitimer(signal.ITIMER_REAL,30)
 try:
  if server.proc.poll() is not None:
   t=time.perf_counter();server.err.close();server.__init__();times['server_restart_seconds']=time.perf_counter()-t
  if model is not None:
   t=time.perf_counter();source_input=read(it.path/'input.json');obj=convert(source_input);append_availability(obj);fresh=load_obj(obj);drop_offline_rows(fresh);fresh=prepare_for_inference(fresh);batch=batch_data_list([fresh]);times['preprocessing_seconds']=time.perf_counter()-t;t=time.perf_counter()
   with torch.no_grad():raw=physical(model(batch))
   times['inference_seconds']=time.perf_counter()-t;t=time.perf_counter();pf,pfd=completion(it,raw);times['PF_seconds']=time.perf_counter()-t
  initial=pf if pfd and pfd['converged'] else None
  if model is not None and initial is None:fallback=True
  for attempt in range(2):
   if attempt and (initial is None or deadline-time.perf_counter()<=.01):break
   if attempt:fallback=True;initial=None
   remain=deadline-time.perf_counter()
   if remain<=.01:break
   t=time.perf_counter();attempt_record=dict(initialization='warm' if initial is not None else 'default',remaining_budget_seconds=remain);attempts.append(attempt_record);rr=server.request(it,Path(folder)/f'attempt-{attempt}',initial,remain,capture=True);times['solver_total_seconds']=times.get('solver_total_seconds',0)+time.perf_counter()-t;attempt_record.update({k:v for k,v in rr.items() if k not in ['state','metrics']})
   if rr.get('result_path'):
    audited=read(rr['result_path']);live=audited.get('iteration_zero_primal',{}).get('actual_internal_unscaled_primal',{});requested=audited.get('initial_starts',{});projection={}
    for name,values in live.items():
     differences=[abs(v-requested[name][k]) for k,v in values.items() if requested.get(name,{}).get(k) is not None];projection[name]=max(differences,default=0)
    attempt_record['max_start_projection_by_variable_pu_rad']=projection
   if rr.get('metrics',{}).get('all_tested_constraints_pass'):
    final=rr['state'];status='FEASIBLE';break
   if 'state' in rr:final=rr['state']
  t=time.perf_counter();fm=score(it,final) if final else None;times['independent_validation_seconds']=time.perf_counter()-t
 except (TimeoutError,FloatingPointError) as exc:
  status='DEADLINE' if isinstance(exc,TimeoutError) else 'NONFINITE';times['failure']=str(exc)
  if isinstance(exc,TimeoutError) and server.proc.poll() is None:server.proc.kill();server.proc.wait()
  if attempts and 'request_seconds' not in attempts[-1]:attempts[-1].update(status=status,failed_attempt_seconds=time.perf_counter()-t)
 finally:signal.setitimer(signal.ITIMER_REAL,0)
 total=time.perf_counter()-start
 if total>30:status='DEADLINE'
 quality=bool(fm and fm['all_tested_constraints_pass'] and total<=30 and fm['signed_cost_gap_percent'] is not None and fm['signed_cost_gap_percent']<=.1)
 row=dict(status=status,total_seconds=total,times=times,fallback=fallback,attempts=attempts,raw_metrics=score(it,raw) if raw and not isinstance(model,Ridge) else None,raw_full_state_available=raw is not None and not isinstance(model,Ridge),control_metrics=dict(Pg_MAE_MW=float(np.mean(abs(np.array(raw['pg_mw'])-it.ref['pg_mw']))),Vctrl_MAE_pu=float(np.mean(abs(np.array(raw['vm'])[it.case.ctrl_bus]-np.array(it.ref['vm'])[it.case.ctrl_bus])))) if raw and it.ref else None,PF_metrics=score(it,pf) if pf else None,PF_converged=pfd['converged'] if pfd else None,PF_iterations=pfd['iterations'] if pfd else None,final_metrics=fm,feasible_within_deadline=bool(fm and fm['all_tested_constraints_pass'] and total<=30),quality_pass=quality,reference_known=it.ref is not None)
 save(Path(folder)/'states.json',dict(raw=raw if not isinstance(model,Ridge) else None,raw_controls=dict(Pg_MW=raw['pg_mw'],control_bus_indices=it.case.ctrl_bus.tolist(),Vctrl_pu=np.array(raw['vm'])[it.case.ctrl_bus].tolist()) if raw else None,native_PF=pf,final=final,metrics=row));return row

def main():
 assert not (RUN/'freeze.json').exists();fits=read(RUN/'training-summary.json');ridge={}
 for net in ['case300','pglib118']:ridge[net]=ridge_tune(net,dataset(net,'train'),dataset(net,'validation'),read(RUN/f'config-{net}.json'))
 # Development-only wrapper pilot before opening confirmation; no tuning from it.
 pilot_server=Server();pilot_rows=[]
 for net in ['case300','pglib118']:
  z=np.load(ridge[net]['chosen_path']);rg=Ridge({k:z[k] for k in z.files});ft=make_model(11);fit=next(f for f in fits if f['network']==net and f['seed']==11);cp=fit['selected']['checkpoint'] if fit.get('selected') else fit['final_checkpoint'];ft.load_state_dict(torch.load(cp,weights_only=False,map_location='cpu')['model_state'],strict=True);ft.eval();frozen=make_model()
  pilots=dataset('case300','ordinary')[:5] if net=='case300' else dataset(net,'train')[:5]
  for it in pilots:
   for label,model in [('conventional',None),('frozen',frozen),('ridge',rg),('FT-seed11-development',ft)]:
    row=online(pilot_server,it,model,RUN/f'pilot-wrapper/{net}/{it.key}/{label}');row.update(network=net,method=label,scenario_id=it.key);pilot_rows.append(row);assert row['feasible_within_deadline'],('wrapper development gate failed',net,it.key,label,row['status'])
  del ft,frozen;gc.collect()
 pilot_server.close();save(RUN/'checks/wrapper-pilot.json',dict(status='PASS',rows=pilot_rows))
 checkpoint_hashes={f['final_checkpoint']:sha(f['final_checkpoint']) for f in fits if 'final_checkpoint' in f}
 checkpoint_hashes.update({f['selected']['checkpoint']:sha(f['selected']['checkpoint']) for f in fits if f.get('selected')})
 data_hashes={str(Path(it.rec['path'])/name):sha(Path(it.rec['path'])/name) for net in ['case300','pglib118'] for split in ['train','validation'] for it in dataset(net,split) for name in ['input.json','reference.json']};save(RUN/'training-data-hashes.json',data_hashes)
 freeze=dict(data_files_sha256=data_hashes,source_case_sha256=sha(RUN/'source-cases.json'),pglib_source_sha256=sha(WORK/'pglib_opf_case118_ieee.m'),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_sha256=sha(ROOT/'docs/experiments/GSFM-007.md'),source_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),source_sha256={p.name:sha(p) for p in Path(__file__).parent.glob('*') if p.is_file()},upstream_commit='517a07531ea55a11bd81a89a6c6879695a2ba4b4',checkpoint_sha256=sha(CKPT),config_sha256={n:sha(RUN/f'config-{n}.json') for n in ['case300','pglib118']},data_sha256={n:sha(RUN/f'data/{n}/manifest.json') for n in ['case300','pglib118']},fits=fits,ridge=ridge,checkpoint_hashes=checkpoint_hashes,checker_sha256=sha(ROOT/'scripts/python/physics_metrics.py'),timing=dict(repeats=3,order_seed=710007,deadline_seconds=30,resident_models=True,cache='resident models, topology/cycle cache; fresh input JSON/schema/graph preparation included in every predictor request; physical case parse/build included in solver; no dual/primal reference reuse',fallback='failed PF -> default; failed warm OPF -> one default retry within remaining same30s'),factorial='first10 ordinary candidate IDs, same native PF with PQ initial magnitude1pu held common across swaps; no reference swaps')
 save(RUN/'freeze.json',freeze);server=Server();manifest=generate(server);allrows=[];models={};loadtime={};rng=np.random.Generator(np.random.PCG64(710007));tphase=time.perf_counter()
 for net in ['case300','pglib118']:
  methods={'conventional':None};t=time.perf_counter();methods['frozen']=make_model();loadtime[net+'-frozen']=time.perf_counter()-t;z=np.load(ridge[net]['chosen_path']);methods['ridge']=Ridge({k:z[k] for k in z.files})
  for f in fits:
   if f['network']!=net or 'final_checkpoint' not in f:continue
   for ep,cp in [('selected',f['selected']['checkpoint'] if f.get('selected') else None),('final',f['final_checkpoint'])]:
    if cp is None:continue
    key=f'FT-s{f["seed"]}-{ep}';t=time.perf_counter();m=make_model(f['seed']);m.load_state_dict(torch.load(cp,weights_only=False,map_location='cpu')['model_state'],strict=True);m.eval();methods[key]=m;loadtime[net+'-'+key]=time.perf_counter()-t
  its=[Item(r) for r in manifest[net] if not r['excluded']];save(RUN/f'confirmation/{net}-cache-cost.json',dict(preparation_seconds=sum(it.prep_s for it in its),n=len(its)))
  for method,model in methods.items():
   row=online(server,its[0],model,RUN/f'online-states/{net}/warmup/{method}');row.update(network=net,method=method,scenario_id=its[0].key,repeat=-1,split=its[0].rec['split']);allrows.append(row)
  for repeat in [0,1,2]:
   for it in its:
    guard()
    if time.perf_counter()-tphase>95*60:log('EVALUATION_CAP');break
    for method in rng.permutation(list(methods)):
     row=online(server,it,methods[method],RUN/f'online-states/{net}/repeat-{repeat}/{it.key}/{method}');row.update(network=net,method=method,scenario_id=it.key,repeat=repeat,split=it.rec['split'],pair_id=it.rec.get('pair_id'));allrows.append(row)
     with (RUN/'online-rows.jsonl').open('a') as ff:ff.write(json.dumps(row)+'\n')
    if (its.index(it)+1)%15==0:log('EVAL_PROGRESS',network=net,repeat=repeat,scenarios=its.index(it)+1,total_records=len(allrows))
   save(RUN/'online-partial.json',allrows)
  # Prespecified 2x2 control substitution, common PQ initial guess isolates controls.
  swaps=[]
  for f in fits:
   if f['network']!=net or not f.get('selected'):continue
   ft=methods[f'FT-s{f["seed"]}-selected'];rg=methods['ridge']
   for it in its:
    if it.rec['split']!='ordinary' or int(it.key.split('-')[-1])>=10:continue
    with torch.no_grad():a=physical(ft(it.batch()));b=physical(rg(it.batch()))
    for pp,vv,tag in [(a,a,'FT_P_FT_V'),(b,b,'ridge_P_ridge_V'),(a,b,'FT_P_ridge_V'),(b,a,'ridge_P_FT_V')]:
     s=copy.deepcopy(pp);s['vm']=[1.]*len(it.c['bus'])
     for i in it.case.ctrl_bus:s['vm'][i]=vv['vm'][i]
     p,d=completion(it,s);swaps.append(dict(seed=f['seed'],scenario_id=it.key,controls=tag,PF_converged=d['converged'],metrics=score(it,p)))
  save(RUN/f'factorial-{net}.json',swaps);del methods;gc.collect()
 save(RUN/'model-loading.json',loadtime);save(RUN/'online-all.json',allrows);server.close();save(RUN/'evaluation-complete.json',dict(status='COMPLETE',seconds=time.perf_counter()-tphase,records=len(allrows),resources=guard()));log('EVALUATION_COMPLETE',records=len(allrows))
if __name__=='__main__':
 try:main()
 except Exception:(RUN/'confirmation-failure.txt').write_text(traceback.format_exc());raise
