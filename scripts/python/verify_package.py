"""Bounded package verification with a commit-linked run record; no training."""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]


def command(args):
    proc = subprocess.run(args,cwd=ROOT,capture_output=True,text=True)
    return {'command':args,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='results/verification/2026-10-21-package.json')
    parser.add_argument('--upstream',type=Path)
    args=parser.parse_args()
    record={'run_id':'2026-10-21-package-verification','started_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'source/protocol/toy verification only; no solver/model study',
            'python':sys.version,'platform':platform.platform(),
            'code_commit':command(['git','rev-parse','HEAD'])['stdout'].strip(),
            'dirty_tree_at_start':command(['git','status','--porcelain'])['stdout'],
            'checks':[],'failures':[]}
    # Parse tracked/public JSON and local links, not generated data or virtualenvs.
    folders=['docs','manifests','configs','results/templates']
    for folder in folders:
        for path in (ROOT/folder).rglob('*.json'):
            try:json.loads(path.read_text(encoding='utf-8-sig'))
            except Exception as exc:record['failures'].append(f'{path.relative_to(ROOT)}: {exc}')
    mdpaths=list((ROOT/'docs').rglob('*.md'))+list((ROOT/'paper').rglob('*.md'))+[ROOT/'README.md',ROOT/'HANDOFF.md']
    for path in mdpaths:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8-sig')):
            if '://' in target or target.startswith('#'):continue
            destination=(path.parent/unquote(target.strip('<>').split('#')[0])).resolve()
            if not destination.exists():record['failures'].append(f'Broken local link {path.relative_to(ROOT)} -> {target}')
    commands=[[sys.executable,'-B','-m','unittest','discover','-s','tests','-v'],
              [sys.executable,'-B','scripts/python/matpower_test.py'],
              [sys.executable,'-B','scripts/python/gridsfm_selfcheck.py']]
    if args.upstream:
        commands[-1] += ['--upstream',str(args.upstream.resolve()),'--lora']
    for cmd in commands:
        result=command(cmd);record['checks'].append(result)
        if result['exit_code']:record['failures'].append('Command failed: '+' '.join(cmd))
    record['input_file_sha256']={}
    for pattern in ('scripts/python/*.py','scripts/matlab/*.m','tests/*.py','configs/*.json','environments/*'):
        for path in ROOT.glob(pattern):
            if path.is_file():record['input_file_sha256'][str(path.relative_to(ROOT)).replace('\\','/')]=hashlib.sha256(path.read_bytes()).hexdigest()
    record['finished_utc']=datetime.now(timezone.utc).isoformat()
    record['status']='passed' if not record['failures'] else 'failed'
    out=ROOT/args.output;out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError('Use a new verification output path; retain failures')
    out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':record['status'],'output':str(out),'failures':record['failures']},indent=2))
    raise SystemExit(0 if record['status']=='passed' else 1)


if __name__=='__main__':main()
