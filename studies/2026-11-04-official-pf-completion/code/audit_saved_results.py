"""Read-only scientific audit of saved evidence; no inference, PF or OPF solve."""
import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import sys


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def compare(a, b, context):
    if isinstance(a, dict):
        for k, v in a.items():
            compare(v, b[k], context + '/' + k)
    elif isinstance(a, list):
        assert len(a) == len(b), context
        for i, (v, w) in enumerate(zip(a, b)):
            compare(v, w, context + '/' + str(i))
    elif isinstance(a, bool) or a is None or isinstance(a, str):
        assert a == b, (context, a, b)
    else:
        assert math.isfinite(float(a)) and math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-9), (context, a, b)


def csv_compare(expected, path):
    with path.open(newline='', encoding='utf-8-sig') as f:
        saved = list(csv.DictReader(f))
    assert len(saved) == len(expected), str(path)
    for i, (a, b) in enumerate(zip(expected, saved)):
        assert set(a) == set(b), str(path)
        for k, v in a.items():
            if v is None:
                assert b[k] == '', (str(path), i, k)
            elif isinstance(v, bool):
                assert b[k] == str(v), (str(path), i, k)
            else:
                compare(v, float(b[k]), f'{path.name}/{i}/{k}')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prior', required=True, type=pathlib.Path)
    p.add_argument('--source', required=True, type=pathlib.Path)
    p.add_argument('--base-checkpoint', type=pathlib.Path)
    p.add_argument('--adapted-checkpoint', type=pathlib.Path)
    args = p.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(args.prior / 'experiments/loading'), str(args.prior / 'scripts/python')]
    from study import evaluate
    from electrical import terms
    import numpy as np

    inventory = read(args.prior / 'artifact-sha256.json')
    for name, expected in inventory.items():
        assert sha(args.prior / name) == expected, name
    e = read(root / 'manifests/execution.json')
    for name, expected in e['code_sha256'].items():
        assert sha(root / 'code' / name) == expected, name
    for name, expected in e['official_source_files'].items():
        assert sha(args.source / name) == expected, name
    for checkpoint, override in [(e['frozen_checkpoint'], args.base_checkpoint), (e['adapted_checkpoint'], args.adapted_checkpoint)]:
        assert sha(override or pathlib.Path(checkpoint.get('local_path', checkpoint.get('checkpoint_path')))) == checkpoint.get('sha256', checkpoint.get('checkpoint_sha256'))
    specs = e['scenarios']
    assert len(specs) == len({s['id'] for s in specs}) == 59
    counts = collections.Counter()
    converged = collections.Counter()
    angle_counts = collections.Counter()
    largest_stamp_difference = 0.
    for spec in specs:
        d = args.prior / 'results' / spec['id']
        for filename, key in [('input.json','input_sha256'), ('newer-base-v2-native.json','reused_v2_state_sha256'), ('newer-base-v2-prepared-used.pt','reused_prepared_graph_sha256')]:
            assert sha(d / filename) == spec[key], spec['id'] + '/' + filename
        c = read(d / 'input.json')
        ref = read(d / 'ac-native.json') if (d / 'ac-native.json').exists() else None
        if ref:
            reference_metric, *_ = evaluate(c, ref, 'AC-OPF', ref)
            assert reference_metric['AC_joint_pass']
        counts['checked_reused_AC'] += int(ref is not None)
        for target in sorted((root / 'results' / spec['id']).iterdir()):
            if not target.is_dir():
                continue
            state, status, saved = [read(target / name) for name in ['state.json','status.json','metrics.json']]
            metric, bus, gen, branch = evaluate(c, state, saved['method'], ref)
            compare(metric, saved, spec['id'] + '/' + target.name)
            for name, rows in [('bus',bus),('generator',gen),('branch',branch)]:
                csv_compare(rows, target / (name + '.csv'))
            cross = terms(c, state)['crosscheck_MW_MVAr']
            largest_stamp_difference = max(largest_stamp_difference, cross)
            assert not metric['AC_joint_pass']
            counts[target.name] += 1
            angle_counts[(spec['id'], saved['method'])] = (metric['constraints']['branch_angle_deg'] or {}).get('violating_count', 0)
            off = np.array([g[7] <= 0 for g in c['gen']])
            assert np.all(np.asarray(state['pg_mw'])[off] == 0) and np.all(np.asarray(state['qg_mvar'])[off] == 0)
            if target.name == 'adapted-native':
                continue
            assert status['source_commit'] == e['source_pin']
            assert status['adapter_sha256'] == e['code_sha256']['adapter.py']
            assert status['input_sha256'] == spec['input_sha256']
            assert status['preset'] == e['preset']
            assert status['iterations'] <= 40
            assert status['converged'] == saved['PF_converged']
            assert status['converged'] == (status['norm_history_pu'][-1] < e['preset']['tol'])
            assert status['maximum_fixed_Pg_change_MW'] < 1e-9
            assert status['maximum_fixed_voltage_change_pu'] < 1e-12
            native = read(root / 'results' / spec['id'] / 'adapted-native/state.json') if target.name.startswith('adapted') else read(d / 'newer-base-v2-native.json')
            balancing = set(status['completion_balancing_buses'])
            fixed = [i for i,g in enumerate(c['gen']) if g[7] > 0 and int(g[0]) not in balancing]
            assert max(abs(np.asarray(state['pg_mw'])[fixed] - np.asarray(native['pg_mw'])[fixed]), default=0) < 1e-9
            controlled_buses = {int(g[0]) for g in c['gen'] if g[7] > 0}
            controlled = [i for i,b in enumerate(c['bus']) if int(b[0]) in controlled_buses and b[1] in [2,3]]
            assert max(abs(np.asarray(state['vm'])[controlled] - np.asarray(native['vm'])[controlled]), default=0) < 1e-12
            converged[target.name] += int(status['converged'])
    assert counts == {'checked_reused_AC':57,'frozen-exact':59,'frozen-official':59,'adapted-native':15,'adapted-exact':15,'adapted-official':15}, counts
    assert converged == {'frozen-exact':4,'frozen-official':4,'adapted-exact':15,'adapted-official':15}, converged
    angles = read(root / 'paper/angle-violation-locations.json')
    observed = collections.Counter((x['scenario'],x['method']) for x in angles)
    assert observed == +angle_counts
    with (root / 'paper/scenario-method-coverage.csv').open(newline='') as f:
        coverage = list(csv.DictReader(f))
    assert len(coverage) == len({(r['id'],r['method']) for r in coverage}) == 531
    assert sum(r['attempted']=='True' for r in coverage) == 399
    assert sum(r['status']=='UNAVAILABLE_COMPATIBLE_WEIGHTS' for r in coverage) == 132
    assert sum(r['status']=='FAILED_FINITE_ITERATE' for r in coverage) == 110
    assert sum(r['status']=='UNKNOWN' for r in coverage) == 2
    sense = read(root / 'paper/sensitivity-summary.json')
    assert len(sense) == 270
    assert collections.Counter(r['status'] for r in sense) == {'CHECKED_REFERENCE_PAIR':162,'FAILED_ITERATE_SECANT_NOT_OPERATING_RESPONSE':108}
    assert {r['variable'] for r in sense} == {'vm','pg_mw','qg_mvar'}
    assert {(r['left'],r['right']) for r in sense} == {(1.,1.005),(1.,1.01),(1.01,1.02)}
    for left,right in [(1.,1.005),(1.,1.01),(1.01,1.02)]:
        selected = {r['method']:r for r in sense if r['network']=='case500goc' and r['component']=='Q' and r['variable']=='qg_mvar' and (r['left'],r['right'])==(left,right)}
        a,b = selected['V2-adapted-native'],selected['V2-adapted+official-PF']
        assert b['direction_agreement_percent'] > a['direction_agreement_percent']
        assert b['response_derivative_RMSE'] > a['response_derivative_RMSE']
    plots = read(root / 'paper/figures/metric-plot-index.json')
    with (root / 'paper/all-metrics.csv').open(newline='') as f:
        all_metrics = {(r['id'],r['method']):r for r in csv.DictReader(f)}
    assert len(plots) == len({p['metric'] for p in plots}) == 36
    for plot in plots:
        for key in ['pdf','png']:
            assert (root / 'paper/figures' / plot[key]).is_file()
        assert plot['plotted_points_with_path_duplicates'] == len(plot['data'])
        for point in plot['data']:
            raw = all_metrics[(point['scenario'],point['method'])][plot['metric']]
            expected = {'True':1.,'False':0.}.get(raw)
            expected = float(raw) if expected is None else expected
            compare(expected, point['value'], 'plot/' + plot['metric'])
    case3 = read(root / 'paper/figures/case3-plot-index.json')
    assert set(s['id'] for s in specs if s['group'].startswith('case3')) == {sid for plot in case3 for sid in plot['scenarios']}
    report = {'status':'PASS','audit_kind':'saved-state re-evaluation and immutable provenance; no model/PF/OPF reruns',
              'prior_payload_hashes_verified':len(inventory),'source_files_verified':len(e['official_source_files']),
              'frozen_execution_files_verified':len(e['code_sha256']),'new_states_rescored':163,
              'detail_tables_compared':489,'largest_independent_equation_difference_MVA':largest_stamp_difference,
              'counts':dict(counts),'PF_converged':dict(converged),'all_new_joint_AC_passes':0,
              'scenario_stage_slots':531,'attempted':399,'unavailable':132,'failed_finite_PF':110,
              'sensitivity_rows':270,'failed_PF_secants_excluded':108,'metric_figures':36,'case3_inputs_plotted':14,
              'all_three_Q_intervals_direction_improves_but_RMSE_worsens':True,'angle_violation_rows_checked':len(angles)}
    (root / 'publication/scientific-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
