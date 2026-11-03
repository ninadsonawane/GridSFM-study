"""Archive every saved extension artifact without rerunning scientific work."""
import argparse
import ast
import collections
import csv
import hashlib
import json
import math
import pathlib
import re
import subprocess
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return not isinstance(value, (float, int)) or math.isfinite(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=pathlib.Path, required=True)
    args = parser.parse_args()
    root = pathlib.Path(__file__).resolve().parents[1]
    repo = root.parents[1]
    pub = root / 'publication'
    prior = args.workspace / 'outputs/GridSFM-loading-study'
    output = args.workspace / 'outputs'
    archive = output / 'GridSFM-official-PF-study-evidence.zip'
    assert not archive.exists(), 'Refuse replacing a published snapshot; use a new name/tag.'

    assert read(pub / 'scientific-audit.json')['status'] == 'PASS'
    paper_audit = read(pub / 'paper-audit.json')
    assert paper_audit['status'] == 'PASS' and sha((root / 'paper/manuscript.pdf').read_bytes()) == paper_audit['PDF_sha256']

    # Check all reused bytes, not just the high-level counts.
    prior_inventory = read(prior / 'artifact-sha256.json')
    for name, expected in prior_inventory.items():
        assert sha((prior / name).read_bytes()) == expected, name
    old_zip = output / 'GridSFM-loading-study-evidence.zip'
    old_digest = sha(old_zip.read_bytes())
    assert old_digest == '185cc64b3e08416c6adae56f6efb00a4781068d920457968ff9c5486ed0414c6'
    execution = read(root / 'manifests/execution.json')
    for name, expected in execution['code_sha256'].items():
        assert sha((root / 'code' / name).read_bytes()) == expected, name
    specs = execution['scenarios']
    assert len(specs) == len({s['id'] for s in specs}) == 59
    for spec in specs:
        source = prior / 'results' / spec['id']
        for name, key in [('input.json', 'input_sha256'),
                          ('newer-base-v2-native.json', 'reused_v2_state_sha256'),
                          ('newer-base-v2-prepared-used.pt', 'reused_prepared_graph_sha256')]:
            assert sha((source / name).read_bytes()) == spec[key], str(source / name)

    stage_counts = collections.Counter()
    convergence = collections.Counter()
    joint_passes = collections.Counter()
    expected_states = set()
    for spec in specs:
        stages = ['frozen-official', 'frozen-exact']
        if spec['network'] == 'case500goc':
            stages += ['adapted-native', 'adapted-official', 'adapted-exact']
        for stage in stages:
            folder = root / 'results' / spec['id'] / stage
            expected_states.add(folder / 'state.json')
            for name in ['state.json', 'status.json', 'metrics.json', 'bus.csv', 'generator.csv', 'branch.csv']:
                assert (folder / name).is_file(), str(folder / name)
            state, status, metric = [read(folder / name) for name in ['state.json', 'status.json', 'metrics.json']]
            assert finite(state), str(folder)
            assert status['scenario'] == metric['scenario'] == spec['id']
            stage_counts[stage] += 1
            if stage != 'adapted-native':
                assert status['source_commit'] == execution['source_pin']
                assert status['input_sha256'] == spec['input_sha256']
                assert status['adapter_sha256'] == execution['code_sha256']['adapter.py']
                convergence[stage] += bool(status['converged'])
                assert metric['PF_converged'] == status['converged']
                assert isinstance(status['norm_history_pu'], list)
            joint_passes[stage] += bool(metric['AC_joint_pass'])
    assert expected_states == set((root / 'results').rglob('state.json'))
    assert sum(stage_counts.values()) == 163
    assert convergence == {'frozen-official': 4, 'frozen-exact': 4, 'adapted-official': 15, 'adapted-exact': 15}
    assert not any(joint_passes.values())
    with (root / 'paper/scenario-method-coverage.csv').open(newline='', encoding='utf-8') as stream:
        coverage = list(csv.DictReader(stream))
    assert len(coverage) == len({(r['id'], r['method']) for r in coverage}) == 531
    assert sum(r['attempted'] == 'True' for r in coverage) == 399
    assert sum(r['status'] == 'UNAVAILABLE_COMPATIBLE_WEIGHTS' for r in coverage) == 132
    assert not any(r['status'] == 'PENDING' for r in coverage)
    summary = read(root / 'paper/summary.json')
    assert (summary['metric_slots'], summary['available_attempted'], summary['pending']) == (531, 399, 0)

    # Publication records that depend on the ZIP digest cannot be inside it.
    sidecars = {'publication/final-artifact-inventory.json', 'publication/final-archive-verification.json',
                'publication/final-release-verification.json', 'publication/final-git-verification.json',
                'publication/GridSFM-official-PF-study-evidence.zip.sha256'}
    files = []
    secret = re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')
    for path in sorted(root.rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if relative in sidecars:
            continue
        data = path.read_bytes()
        assert not secret.search(data), 'Potential secret detected; publication stopped: ' + relative
        assert path.name not in {'.env', 'credentials', 'cookies.sqlite'}, relative
        if path.suffix == '.json':
            json.loads(data)
        if path.suffix == '.py':
            ast.parse(data.decode('utf-8-sig'), filename=relative)
        if path.suffix == '.csv':
            with path.open(newline='', encoding='utf-8-sig') as stream:
                reader = csv.reader(stream)
                first = next(reader)
                assert all(len(row) == len(first) for row in reader), relative
        ignored = subprocess.run(['git', 'check-ignore', '--quiet', '--', str(path)], cwd=repo).returncode == 0
        files.append({'path': relative, 'bytes': len(data), 'sha256': sha(data),
                      'in_git': not ignored, 'in_release_archive': True})
    inventory = {'scope': 'All current extension payload files; publication sidecars listed separately',
                 'status': 'BOUNDED_STUDY_AND_REVIEW_DRAFT_COMPLETE_WITH_EXPLICIT_UNAVAILABLE_STAGES',
                 'archive_root': root.name, 'payload_files': files,
                 'sidecars_excluded_from_archive_payload': sorted(sidecars),
                 'excluded_generated_directories': ['__pycache__'],
                 'external_inputs': 'Prior immutable evidence archive, pinned source/checkpoint downloads and installed dependencies',
                 'coverage': {'unique_inputs': 59, 'new_states': 163, 'slots': 531,
                              'attempted_including_reused': 399, 'unavailable': 132, 'pending_runs': 0},
                 'stage_counts': dict(stage_counts), 'PF_converged': dict(convergence),
                 'AC_joint_passes': dict(joint_passes)}
    save(pub / 'final-artifact-inventory.json', inventory)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as package:
        for entry in files:
            package.write(root / entry['path'], root.name + '/' + entry['path'])
        package.write(pub / 'final-artifact-inventory.json', root.name + '/publication/final-artifact-inventory.json')
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert len(package.namelist()) == len(files) + 1
        for entry in files:
            data = package.read(root.name + '/' + entry['path'])
            assert sha(data) == entry['sha256'], entry['path']
            assert len(data) == entry['bytes']
    digest = sha(archive.read_bytes())
    checksum = digest + '  ' + archive.name + '\n'
    archive.with_suffix('.zip.sha256').write_text(checksum, encoding='ascii', newline='\n')
    (pub / (archive.name + '.sha256')).write_text(checksum, encoding='ascii', newline='\n')
    report = {'status': 'PASS', 'archive': archive.name, 'archive_bytes': archive.stat().st_size,
              'archive_sha256': digest, 'payload_files': len(files), 'archive_files': len(files) + 1,
              'git_payload_files': sum(f['in_git'] for f in files),
              'release_only_payload_files': sum(not f['in_git'] for f in files),
              'prior_inventory_files_verified': len(prior_inventory), 'prior_archive_sha256': old_digest,
              'all_archive_entries_verified_against_exact_local_bytes': True,
              'frozen_code_and_59_input_state_feature_hashes_verified': True,
              'json_csv_python_integrity_checks': 'PASS',
              'numerical_reexecution': False, 'bounded_study_and_review_draft_complete': True, 'submission_ready': False,
              'coverage': inventory['coverage'], 'stage_counts': dict(stage_counts),
              'PF_converged': dict(convergence), 'AC_joint_passes': dict(joint_passes)}
    save(pub / 'final-archive-verification.json', report)
    save(output / 'PF-study-archive-verification.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
