import sys, json, hashlib
from pathlib import Path
ROOT=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study')
sys.path.insert(0,str(ROOT/'scripts/python'))
from matpower_case import read_case, construct, audit
from gridsfm_convert import convert
out=Path(__file__).parent
src=out/'case300.m'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5'
base=read_case(src)
cfg=json.loads((ROOT/'configs/network-case300x2.json').read_text())
built,mapping=construct(base,cfg)
(out/'construction-map.json').write_text(json.dumps(mapping,indent=2)+'\n')
for name,case in [('case300',base),('case300x2',built)]:
    (out/f'{name}-input.json').write_text(json.dumps(case)+'\n')
    (out/f'{name}.pyg.json').write_text(json.dumps(convert(case))+'\n')
    if name=='case300x2':
        lines=['function mpc = case300x2','mpc.version = \'2\';',f'mpc.baseMVA = {case["baseMVA"]};']
        for key in ['bus','gen','branch','gencost']:
            lines.append(f'mpc.{key} = [')
            lines += [' '.join(format(v,'.17g') for v in row)+';' for row in case[key]]
            lines.append('];')
        (out/'case300x2.m').write_text('\n'.join(lines)+'\n')
    print(name,audit(case)['counts'])
