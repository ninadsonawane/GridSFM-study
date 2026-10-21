from common import *
import gc

def main():
 f=read(RUN/'freeze.json');assert sha(CKPT)==f['checkpoint_sha256'];assert sha(ROOT/'scripts/python/physics_metrics.py')==f['checker_sha256'];assert sha(RUN/'source-cases.json')==f['source_case_sha256'];assert sha(WORK/'pglib_opf_case118_ieee.m')==f['pglib_source_sha256']
 for p,h in f['data_files_sha256'].items():assert sha(p)==h,p
 for net,h in f['config_sha256'].items():assert sha(RUN/f'config-{net}.json')==h
 for p,h in f['checkpoint_hashes'].items():assert sha(p)==h,p
 for p,h in f['source_sha256'].items():assert sha(Path(__file__).parent/p)==h,p
 fits=read(RUN/'training-summary.json');assert len(fits)==6
 for x in fits:
  assert x['updates']==1500 and x['status']=='COMPLETE';assert x['strict_reload_equal'];assert x['fit_seconds']<=1500
  vals=x['validation'];assert len(vals)==30;eligible=[v for v in vals if v['eligible']]
  if x.get('selected'):assert x['selected']['update']==min(eligible,key=lambda v:(v['score'],v['update']))['update']
  assert vals[24]['update']==1250
  p=RUN/f'fits/{x["network"]}-s{x["seed"]}';cfg=read(p/'config.json');assert cfg['train']['lr_horizon']==400
  if x.get('selected'):
   m=make_model(x['seed']);m.load_state_dict(torch.load(x['selected']['checkpoint'],weights_only=False,map_location='cpu')['model_state'],strict=True);it=dataset(x['network'],'train')[0]
   with torch.no_grad():a=physical(m(it.batch()))
   m.load_state_dict(torch.load(x['selected']['checkpoint'],weights_only=False,map_location='cpu')['model_state'],strict=True)
   with torch.no_grad():assert a==physical(m(it.batch()))
   rec=next(r for r in read(RUN/'confirmation/manifest.json')[x['network']] if r['scenario_id']=='ordinary-000' and not r['excluded']);item=Item(rec)
   with torch.no_grad():reloaded=physical(m(item.batch()))
   saved=read(RUN/f"online-states/{x['network']}/repeat-0/ordinary-000/FT-s{x['seed']}-selected/states.json")['raw'];assert reloaded==saved,'saved confirmation prediction not reproduced'
   del m;gc.collect()
 assert read(RUN/'training-duration.json')['seconds']<=7200
 manifest=read(RUN/'confirmation/manifest.json');allrows=read(RUN/'online-all.json');rescored=0
 for net,recs in manifest.items():
  assert len(recs)==90
  for r in recs:
   if r['excluded']:continue
   assert sha(Path(r['path'])/'input.json')==r['input_sha256']
   if r['split']=='spatial':assert max(abs(v) for v in r['P_Q_drift'])<1e-7
  rows=[x for x in allrows if x['network']==net and x['repeat']>=0];names=sorted(set(x['method'] for x in rows));valid=[r for r in recs if not r['excluded']]
  for method in names:
   for rep in [0,1,2]:assert len([r for r in rows if r['method']==method and r['repeat']==rep])==len(valid)
  for r in rows:
   rec=next(x for x in recs if x['scenario_id']==r['scenario_id']);it=Item(rec);saved=read(RUN/f'online-states/{net}/repeat-{r["repeat"]}/{r["scenario_id"]}/{r["method"]}/states.json')
   for stage,key in [('raw','raw_metrics'),('native_PF','PF_metrics'),('final','final_metrics')]:
    if saved.get(stage) is not None:assert score(it,saved[stage])==r[key],(net,r['method'],r['scenario_id'],stage);rescored+=1
   if r['quality_pass']:assert r['feasible_within_deadline'] and r['final_metrics']['signed_cost_gap_percent']<=.1
   if r['fallback']:assert r['method']!='conventional'
 # Both mandatory pilot networks demonstrate live internal starts, not only JuMP metadata.
 assert read(RUN/'checks/gate.json')['status']=='PASS'
 result=dict(status='PASS',saved_states_rescored=rescored,source_data_checkpoint_hashes=True,all_six_fits_complete=True,selection_recomputed=True,all_fixed_candidates_and_three_repeats_covered=True,old_results_untouched=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only','436a9cac85da5634ad78576b26dde35838cf6373','--','results/pilots/GSFM-004','results/pilots/GSFM-005','results/pilots/GSFM-006'],text=True)=='',elapsed_seconds=time.time()-START,resources=guard())
 save(RUN/'verification.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
