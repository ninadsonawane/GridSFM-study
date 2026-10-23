from pathlib import Path
import json,subprocess,sys,time
R=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');E=R/'experiments/gsfm015';O=R/'results/comparisons/GSFM-015/20261023-load-location-charging';PY=str(R.parent/'GridSFM/model/.venv/bin/python')
for x in json.loads((O/'all-scenarios.json').read_text())['scenarios']:
 if 'reused_from' not in x:continue
 for rel in ['microsoft-v1.1','newer-base-v2']:
  d=O/x['id'];assert not(d/(rel+'-clamps.json')).exists();cmd=[PY,'-B',str(E/'run_model.py'),rel,str(d)];t=time.perf_counter();p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);(d/(rel+'-worker.log')).write_text(p.stdout+'\nSTDERR\n'+p.stderr);assert p.returncode==0,(x['id'],rel,p.stdout,p.stderr);print('REUSED SOLVERS; NATIVE EQUALITY AND CLAMP CAPTURE PASS',x['id'],rel,round(time.perf_counter()-t,2),flush=True)
print('SIX REUSED INPUTS COMPLETE',flush=True)
