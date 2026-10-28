"""Copy and hash completed local evidence; no scientific execution or publication."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

R = Path(__file__).resolve().parents[2]
O = R / 'results/comparisons/GSFM-020/20261026-local-operating-conditions'
D = R.parents[1] / 'outputs/GSFM-020'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')

assert not D.exists(), 'Refuse replacing an existing delivered snapshot'
assert json.loads((O/'final-verification.json').read_text())['status'] == 'PASS'
assert json.loads((O/'mechanisms/confirmation-independent-review.json').read_text())['status'] == 'PASS'
previous=json.loads((O/'prior-tracked-sha256.json').read_text())
for relative, expected in previous.items():
    assert sha(R/relative) == expected, relative

paths={R/p for p in subprocess.check_output(['git','ls-files'],cwd=R,text=True).splitlines() if (R/p).is_file()}
paths.update(p for p in (R/'experiments/gsfm020').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.update(p for p in O.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.add(R/'data/source/matpower-8.1/case300.m')
for source in sorted(paths):
    target=D/'study'/source.relative_to(R)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    assert sha(source)==sha(target)

prefix='study/results/comparisons/GSFM-020/20261026-local-operating-conditions/'
report=(R/'experiments/gsfm020/REPORT.md').read_text(encoding='utf-8')
report=report.replace('../../results/comparisons/GSFM-020/20261026-local-operating-conditions/',prefix)
report=report.replace('(REPRODUCE.md)','(reproduce.md)')
(D/'report.md').write_text(report,encoding='utf-8',newline='\n')
shutil.copy2(R/'experiments/gsfm020/REPRODUCE.md',D/'reproduce.md')
table=(O/'comparison-table.md').read_text(encoding='utf-8')
for name in ['live-table.md','method-summary.csv']:
    table=table.replace('('+name+')','('+prefix+name+')')
(D/'comparison-table.md').write_text(table,encoding='utf-8',newline='\n')
shutil.copy2(O/'method-summary.csv',D/'all-method-metrics.csv')
shutil.copy2(O/'final-verification.json',D/'final-verification.json')
shutil.copy2(O/'mechanisms/confirmation-checks.json',D/'confirmation-checks.json')

completed=dt.datetime.now(dt.timezone.utc)
started=dt.datetime.fromisoformat('2026-10-26T16:45:13+00:00')
assert completed < started+dt.timedelta(hours=5)
save(D/'delivery-status.json',{
    'status':'COMPLETED_LOCAL_ONLY','snapshot_created_UTC':completed.isoformat(),
    'preserved_start_UTC':started.isoformat(),'elapsed_minutes_at_snapshot':(completed-started).total_seconds()/60,
    'deadline_UTC':(started+dt.timedelta(hours=5)).isoformat(),
    'discovery_inputs':20,'confirmation_inputs':6,'AC_references_accepted':24,'AC_references_UNKNOWN':2,
    'DC_own_law_passes':26,'native_model_joint_passes':0,'native_model_points':52,
    'diagnostic_actual_forwards':19,'diagnostic_worker_invocations':21,'diagnostic_pre_forward_failures':2,
    'previous_tracked_files_preserved':len(previous),'publication_or_correspondence':False,
    'new_experiment_directory':'study/experiments/gsfm020',
    'runtimes_and_checkpoint_binaries_included':False,
    'archive_scope':'Complete prior tracked study snapshot plus all new experiment code and evidence; no .git or runtime caches.'})

# Check the new reports' relative links, without crawling historical documents.
checked_links=[]
for p in [D/'report.md',D/'comparison-table.md',D/'reproduce.md',D/'study/experiments/gsfm020/REPORT.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','#')):
            continue
        dest=(p.parent/target.split('#')[0]).resolve()
        assert dest.is_file(), (str(p),target)
        checked_links.append({'document':str(p.relative_to(D)),'target':target})

files={p.relative_to(D).as_posix():sha(p) for p in sorted(D.rglob('*')) if p.is_file()}
save(D/'artifact-manifest.json',{'algorithm':'SHA-256','files':files,
     'excluded_self_and_archive':True,'file_count':len(files),
     'note':'Manifest excludes itself and later package-verification.json; archive contains this manifest and all listed files.'})
archive=D/'GSFM-020-evidence.zip'
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in sorted([*files,'artifact-manifest.json']):
        z.write(D/rel,rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,expected in files.items():
        assert hashlib.sha256(z.read(rel)).hexdigest()==expected,rel
    assert hashlib.sha256(z.read('artifact-manifest.json')).hexdigest()==sha(D/'artifact-manifest.json')
save(D/'package-verification.json',{
    'status':'PASS','completed_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),
    'archive_file':archive.name,'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,
    'all_archived_file_hashes_verified':True,'manifest_file_count':len(files),
    'prior_tracked_file_count':len(previous),'relative_report_links_checked':checked_links})
print(json.dumps({'status':'PASS','output_directory':str(D),'file_count':len(files),
                 'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive)},indent=2))
