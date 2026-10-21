"""Final consistency audit without new solver calls, training or selection."""
from common import *
import csv,ast

def main():
    freeze=read(RUN/'freeze.json');config=read(RUN/'config.json');fits=read(RUN/'training-summary.json');rows=read(RUN/'evaluation/all-rows.json');summary=read(RUN/'summary.json');data=read(RUN/'data/manifest.json');cal=read(RUN/'calibration.json')
    assert sha(RUN/'config.json')==freeze['config_sha256'];assert sha(RUN/'calibration.json')==freeze['calibration_sha256'];assert sha(RUN/'training-summary.json')==freeze['training_summary_sha256'];assert sha(REPO/'scripts/python/physics_metrics.py')==freeze['metric_code_sha256'];assert sha(OLD/'baselines/linear-models.npz')==freeze['baseline_sha256']
    assert cal['valid_count']>=16;assert cal['rho']==float(np.median([r['ratio'] for r in cal['examples'] if r['valid']]));assert len(fits)==12;assert all(f['status']=='COMPLETE' and f['actual_updates']==1000 for f in fits)
    assert len({f['initial_model_hash'] for f in fits})==1
    orders={seed:read(RUN/f'orders/seed-{seed}.json')['indices'] for seed in [11,22,33]};assert len({tuple(o) for o in orders.values()})==3
    for seed,order in orders.items():
      assert len(order)==1000
      for i in range(0,1000,50):assert sorted(order[i:i+50])==list(range(50))
    manifest=read(OLD/'data/manifest.json');train=[r for r in manifest['train'] if r['accepted']]
    for f in fits:
      assert f['reload_equivalence'];assert f['peak_RSS_bytes']<32*2**30;assert f['minimum_available_bytes']>=12*2**30;assert f['training_seconds']<=900;assert f['head_feas_frozen']
      path=RUN/f"training/seed-{f['seed']}/{f['arm']}";trace=[json.loads(x) for x in (path/'train-trace.jsonl').read_text().splitlines()];assert len(trace)==1000
      assert [t['scenario_id'] for t in trace]==[train[i]['scenario_id'] for i in orders[f['seed']]]
      assert all(math.isfinite(t['gradient']['unclipped_norm']) and math.isfinite(t['loss']['total']) and t['loss']['active']['rated_branches']==0 and not t['loss']['active']['feasibility_objective'] and not t['loss']['active']['stress_objective'] for t in trace)
      selected=min(f['validation'],key=lambda v:tuple(v['key']));assert selected['update']==f['selected_update'];assert {int(k) for k in f['checkpoints']}==set(range(0,1001,50))
    for record in config['training_cases']:
      old=next(x for x in train if x['scenario_id']==record['scenario_id']);assert sha(Path(old['path'])/'input.json')==record['input_sha256'];assert sha(Path(old['path'])/'reference.json')==record['reference_sha256']
    oldseen={content_hash(read(p)) for p in (REPO/'results').rglob('*input.json') if RUN not in p.parents};seen=set(oldseen);accepted=0;base=read(BASE/'case300-input.json');maxdrift=[0.,0.]
    for split,records in data.items():
      for r in records:
        if not r.get('path'):continue
        p=Path(r['path']);c=read(p/'input.json');h=content_hash(c);assert h not in seen;seen.add(h);assert sha(p/'input.json')==r['input_sha256'];assert sha(p/'factors.json')==r['factor_sha256']
        for k in ['gen','branch','gencost']:assert c[k]==base[k]
        for b,o in zip(c['bus'],base['bus']):assert b[:2]+b[4:]==o[:2]+o[4:]
        if r['accepted']:
          accepted+=1;assert read(p/'reference-metrics.json')['all_tested_constraints_pass']
          ref=read(p/'reference.json');assert evaluate(c,ref)['all_tested_constraints_pass']
        if split=='spatial':
          before=read(Path(next(q for q in data['ordinary'] if q['scenario_id']==r['pair_id'])['path'])/'input.json');d=np.array([[b[2],b[3]] for b in c['bus']])-np.array([[b[2],b[3]] for b in before['bus']]);drift=abs(d.sum(axis=0));maxdrift=np.maximum(maxdrift,drift).tolist();assert max(drift)<1e-7
          for a,b in zip(c['bus'],before['bus']):assert abs(a[2]*b[3]-a[3]*b[2])<1e-7
    assert len(summary)==153;assert len(rows)==sum(s['evaluated'] for s in summary)
    for s in summary:
      ids={r['scenario_id'] for r in rows if (r['method'],r['seed'],r['endpoint'],r['split'])==(s['method'],s['seed'],s['endpoint'],s['split'])};assert ids=={r['scenario_id'] for r in data[s['split']] if r['accepted']}
    for p in (REPO/'experiments/gsfm005').glob('*.py'):ast.parse(p.read_text())
    for name in ['summary.csv','matched-steps.csv','paired-summary.csv']:
      with (RUN/name).open(newline='') as f:
        rr=list(csv.reader(f));assert len({len(x) for x in rr})==1
    for p in (RUN/'figures').glob('*.png'):assert p.stat().st_size>10000
    assert len(list((RUN/'figures').glob('*.png')))==3
    result=dict(status='PASS',twelve_fits=True,updates_each=1000,identical_pretrained_initial_states=True,actual_seed_orders_distinct=True,within_seed_orders_identical=True,initial_rho_training_only=True,selection_validation_only=True,all_fixed_endpoints_saved=True,summary_rows=len(summary),prediction_rows=len(rows),fresh_accepted=accepted,no_duplicate_inputs=True,original_case_fields_preserved=True,reloaded_references_feasible=True,original_train_validation_unchanged=True,baseline_hash_unchanged=True,metric_hash_unchanged=True,all_fit_resource_caps=True,strict_feasible_predictions=sum(r['all_tested_constraints_pass'] for r in rows),spatial_max_total_P_Q_drift=maxdrift,verification_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save(RUN/'verification.json',result);log('FINAL_VERIFICATION_PASS',**result)
if __name__=='__main__':main()
