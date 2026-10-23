from pathlib import Path
import json,subprocess
R=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=R/'results/comparisons/GSFM-016/20261024-electrical-mechanisms';E=R/'experiments/gsfm016';PY=str(R.parent/'GridSFM/model/.venv/bin/python')
for x in json.loads((O/'reused-inputs.json').read_text()):
 if 'capture_dir' not in x:continue
 d=R/x['capture_dir']
 for rel in ['microsoft-v1.1','newer-base-v2']:
  assert not(d/(rel+'-clamps.json')).exists();p=subprocess.run([PY,'-B',str(E/'run_model.py'),rel,str(d)],capture_output=True,text=True,timeout=120);(d/(rel+'-worker.log')).write_text(p.stdout+'\nSTDERR\n'+p.stderr);assert p.returncode==0,(x['id'],rel,p.stdout,p.stderr);print('RATED BASELINE NATIVE EQUALITY+CLIP CAPTURE PASS',x['id'],rel,flush=True)
