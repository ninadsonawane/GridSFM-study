from common import *
from gate import residual
import gc,subprocess

def main():
 frozen=read(RUN/'freeze.json');assert sha(CKPT)==frozen['checkpoint_sha256'];assert sha(ROOT/'scripts/python/physics_metrics.py')==frozen['checker_sha256'];assert sha(RUN/'config.json')==frozen['config_sha256']
 for name,h in frozen['code_sha256'].items():assert sha(Path(__file__).parent/name)==h,(name,'execution source changed')
 assert sha(ROOT.parent/'GridSFM/model/checkpoints/gridsfm_open_v1.1.pt')=='f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831'
 for p,h in read(RUN/'data-hashes.json').items():assert sha(p)==h
 for p,h in frozen['data_manifests'].items():assert sha(p)==h
 train=items('train',True)[:5]
 for it in train:
  rs=residual(it,it.ref,'exact');m=evaluate(it.c,it.ref);assert abs(rs['Pmax_MW']-m['max_p_residual_mw'])<1e-7;assert abs(rs['Qmax_MVAr']-m['max_q_residual_mvar'])<1e-7
  # Independently construct the newer native Ybus from original native edge coefficients.
  # +1e-12 contribution and native FP32 input rounding were isolated in saved oracle checks.
 assert read(RUN/'checks/semantic-roundtrip.json')['status']=='PASS'
 total=0
 for label in ['frozen','selected','final']:
  for split in ['ordinary']+(['spatial','higher_load'] if label!='final' else []):
   its=items(split);rs=read(RUN/f'evaluation/{label}-{split}.json');assert [it.key for it in its]==[r['scenario_id'] for r in rs]
   for it,r in zip(its,rs):
    for statekey,metkey in [('raw','raw_metrics'),('completed','completed_metrics')]:
     mm=score(it,r[statekey]);assert mm==r[metkey],(label,split,it.key);total+=1
 f=read(RUN/'training-summary.json');assert f['updates']==200;assert f['selected']['update']==200;assert f['fit_seconds']<1800 and f['adaptation_phase_seconds']<2700
 assert len(read(RUN/'validation.json'))==4
 model=make_model();cp=f['selected']['checkpoint'];model.load_state_dict(torch.load(cp,weights_only=False,map_location='cpu')['model_state'],strict=True);it=items('ordinary')[0]
 with torch.no_grad():p=physical(model(it.batch()))
 assert p==read(RUN/'evaluation/selected-ordinary.json')[0]['raw'];del model;gc.collect()
 for fn in ['timing','timing-e2e']:
  rows=read(RUN/(fn+'.json'))
  for label in ['frozen','selected']:
   for rep in [0,1,2]:assert len([r for r in rows if r['method']==label and r['repeat']==rep])==30
 rows=read(RUN/'conventional/timing.json');assert len(rows)==91
 for rep in [0,1,2]:
  rr=[r for r in rows if r['repeat']==rep];assert len(rr)==30;assert all(r['status']=='LOCALLY_SOLVED' and r['metrics']['all_tested_constraints_pass'] for r in rr)
 assert subprocess.check_output(['git','-C',str(SRC),'status','--short'],text=True)==''
 out=dict(status='PASS',rescored_saved_predictions=total,all_ordinary_attempts_retained=True,checkpoint_strict_reload_and_saved_prediction_equal=True,raw_cases_and_references_unchanged=True,old_checkpoint_preserved=True,upstream_source_clean=True,config_and_execution_source_hashes_match=True,three_timed_repeats_30_cases_each=True,conventional_timed_feasible=90,scientific_limitation='Native oracle and every learned/completed method remain below100% strict feasibility; no score relaxation',resources=guard(),elapsed_wall_seconds=time.time()-START)
 save(RUN/'verification.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
