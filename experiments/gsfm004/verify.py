"""Final artifact/protocol verification, reusing saved electrical acceptance evidence."""
from common import *
import ast,csv
def main():
    manifest=read(RUN/'data/manifest.json');fits=read(RUN/'training-summary.json');summary=read(RUN/'summary.json');base=read(BASE/'case300-input.json');seen=set();counts={}
    for split,records in manifest.items():
        counts[split]={'accepted':sum(r['accepted'] for r in records),'attempted':len(records)}
        for rec in records:
            if rec['status']=='DEGENERATE':continue
            p=Path(rec['path']);assert sha(p/'input.json')==rec['input_sha256'];assert sha(p/'factors.json')==rec['factor_sha256'];c=read(p/'input.json');h=content_hash(c);assert h not in seen;seen.add(h)
            for k in ['gen','branch','gencost']:assert c[k]==base[k],(rec['scenario_id'],k)
            for a,b in zip(c['bus'],base['bus']):assert a[:2]+a[4:]==b[:2]+b[4:]
            if rec['accepted']:
                metrics=read(p/'reference-metrics.json');raw=read(p/'solver-result.json');assert metrics['all_tested_constraints_pass'];assert abs(metrics['generation_cost_per_hour']-raw['objective'])<=1e-8*max(1,abs(raw['objective']))
            else:assert rec['status'] not in ['LOCALLY_SOLVED','OPTIMAL'] or rec.get('rejection')=='independent physical gate'
    assert counts['train']['accepted']==50 and counts['validation']['accepted']==10
    assert counts['ordinary']['accepted']==10 and counts['spatial']['accepted']==10 and counts['higher_load']['accepted']==10
    assert len(fits)==6 and {r['arm'] for r in fits}==set('SCEHLR')
    order=read(RUN/'training-order.json')['scenario_ids'];checkpoint_steps=[]
    for fit in fits:
        assert fit['actual_updates']==200 and fit['status']=='COMPLETE';assert fit['training_seconds_including_validation_checkpointing']<1500;assert fit['process_tree_peak_RSS_bytes']<32*2**30;assert fit['minimum_available_memory_bytes']>=12*2**30
        trace=[json.loads(l) for l in (RUN/'training'/fit['arm']/'train-trace.jsonl').read_text().splitlines()];assert len(trace)==200;assert [r['scenario_id'] for r in trace]==order
        assert all(r['loss']['active']['rated_branches']==0 and not r['loss']['active']['feasibility_objective'] and not r['loss']['active']['stress_objective'] for r in trace)
        for r in trace:
            assert math.isfinite(r['loss']['total']);assert math.isfinite(r['gradient']['unclipped_norm']);assert math.isfinite(r['clipping_input_norm'])
        selected=min(fit['validation'],key=lambda r:tuple(r['key']));assert selected['update']==fit['selected_update'];checkpoint_steps.append(list(map(int,fit['checkpoints'])))
    assert all(steps==[0,50,100,150,200] for steps in checkpoint_steps)
    assert len(summary)==45 and all(r['evaluated']==10 for r in summary)
    rawrows=read(RUN/'evaluation/all-rows.json');assert len(rawrows)==450
    assert len(read(RUN/'paired-summary.json'))==150
    old=read(BASE/'provenance.json');assert all(sha(BASE/name)==h for name,h in old['files'].items())
    assert sha(CKPT if 'CKPT' in globals() else MODEL/'model/checkpoints/gridsfm_open_v1.1.pt')=='f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831'
    sources=REPO/'experiments/gsfm004'
    for p in sources.glob('*.py'):ast.parse(p.read_text())
    with (RUN/'summary.csv').open(newline='') as f:
        rows=list(csv.reader(f));assert len(rows)==46 and all(len(r)==len(rows[0]) for r in rows)
    result={'status':'PASS','shared_data_counts':counts,'unique_candidate_inputs':len(seen),'six_main_fits':True,'updates_per_fit':200,'identical_order_all_arms':True,'validation_only_selection_verified':True,'selected_and_fixed_endpoints':True,'summary_rows':45,'paired_rows':150,'strict_feasible_predictions':sum(r['all_tested_constraints_pass'] for r in rawrows),'old_results_and_base_checkpoint_unchanged':True,'all_time_memory_caps_passed':True,'numerical_failures_in_main_fits':0,'resolved_setup_failure':'checks/failure-before-random-default-fix','reused_reference_acceptance_records':True}
    save(RUN/'final-verification.json',result);log('FINAL_VERIFICATION_PASS',summary_rows=45)
if __name__=='__main__':main()
