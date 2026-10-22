"""11B: one frozen forward per version, native shipped clipping; no PF/repair."""
import os,sys,pathlib,json,hashlib,time,math
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XDG_CACHE_HOME='/private/tmp/gsfm011b-20261022/cache')
ROOT=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');W=pathlib.Path('/private/tmp/gsfm011b-20261022');OUT=pathlib.Path(sys.argv[2]);release=sys.argv[1];SRC=W/'microsoft-source' if release=='microsoft-v1.1' else ROOT/'work/GSFM-006-source-517a075';CKPT=ROOT.parent/'GridSFM/model/checkpoints/gridsfm_open_v1.1.pt' if release=='microsoft-v1.1' else ROOT/'data/checkpoints/GSFM-006-gridsfm_open_v2.pt'
sys.path[:0]=[str(SRC/'model'),str(ROOT/'scripts/python')]
import torch
from gridsfm import load_model,predict
from gridsfm_convert import convert
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
c=json.loads((OUT/'input.json').read_text());obj=convert(c)
if release!='microsoft-v1.1':
 for rows in obj['grid']['nodes'].values():
  for row in rows:row.append(1.)
 for fam in ['ac_line','transformer']:
  for row in obj['grid']['edges'][fam]['features']:row.append(1.)
assert 'solution' not in obj;assert obj['metadata']['bus_external_ids']==[int(b[0]) for b in c['bus']];assert obj['metadata']['gen_source_rows']==list(range(69))
p=OUT/(release+'-input.pyg.json');p.write_text(json.dumps(obj));torch.set_num_threads(4);torch.manual_seed(0);m=load_model(CKPT,device='cpu');m.eval();blob=torch.load(CKPT,weights_only=True,map_location='cpu');m.load_state_dict(blob['state_dict'],strict=True)
expected='f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831' if release=='microsoft-v1.1' else '9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7';assert sha(CKPT)==expected;assert m.leaky_alpha==0 and getattr(m,'clip_mode','clamp')=='clamp'
t=time.perf_counter();raw=predict(m,p);elapsed=time.perf_counter()-t;serial={k:v.tolist() if torch.is_tensor(v) else v for k,v in raw.items()};(OUT/(release+'-returned.json')).write_text(json.dumps(serial,indent=2,allow_nan=False)+'\n')
# Save native point immediately, before any accuracy/physics evaluation.
native={'vm':serial['V'],'va_deg':[math.degrees(v) for v in serial['theta']],'pg_mw':[v*100 for v in serial['Pg']],'qg_mvar':[v*100 for v in serial['Qg']]};(OUT/(release+'-native.json')).write_text(json.dumps(native,indent=2,allow_nan=False)+'\n')
meta={'release':release,'source_commit':'1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6' if release=='microsoft-v1.1' else '517a07531ea55a11bd81a89a6c6879695a2ba4b4','source_model_sha256':sha(SRC/'model/gridsfm/model.py'),'checkpoint_path':str(CKPT),'checkpoint_sha256':sha(CKPT),'checkpoint_metadata':blob['metadata'],'clip_mode':getattr(m,'clip_mode','leaky_clip'),'leaky_alpha':m.leaky_alpha,'native_saved_before_evaluation':True,'additional_PF_or_OPF':False,'model_input_has_solution':False,'input_sha256':sha(OUT/'input.json'),'mapping':obj['metadata'],'inference_seconds_descriptive_only':elapsed}
(OUT/(release+'-metadata.json')).write_text(json.dumps(meta,indent=2,allow_nan=False)+'\n');print(release,'native saved; default clipping',meta['clip_mode'],flush=True)
