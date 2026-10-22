import pathlib,json,hashlib,sys,copy,os
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study'); W=pathlib.Path('/private/tmp/gsfm011c1-20261022'); O=pathlib.Path(os.environ.get('GSFM011C1_OUTPUT',str(R/'results/comparisons/GSFM-011C-1/20261022-loading-only'))); E=R/'experiments/gsfm011c1';assert not (O/'run-status.json').exists(),'Refusing to overwrite completed attempts; set GSFM011C1_OUTPUT to a fresh directory';E.mkdir(parents=True,exist_ok=True);O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'scripts/python'));from matpower_case import read_case
src=R/'results/inference/2026-10-21-base-cases/case300.m';c=read_case(src);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(src)=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5'
scales=[.8,.9,.95,1.03,1.06,1.1];inputs=[]
for v in scales:
 ident=f'load-{v:.2f}';d=O/ident;d.mkdir(exist_ok=True);cc=copy.deepcopy(c)
 for b,orig in zip(cc['bus'],c['bus']):
  b[2]=orig[2]*v;b[3]=orig[3]*v
  assert b[:2]+b[4:]==orig[:2]+orig[4:]
 for k in ['gen','branch','gencost']:assert cc[k]==c[k]
 p=d/'case300.m';lines=['function mpc = case300',"mpc.version = '2';",f"mpc.baseMVA = {c['baseMVA']};"]
 for k in ['bus','gen','branch','gencost']:
  lines += [f'mpc.{k} = [']+[' '.join(format(x,'.17g') for x in row)+';' for row in cc[k]]+['];']
 p.write_text('\n'.join(lines)+'\n');assert read_case(p)==cc
 (d/'input.json').write_text(json.dumps(cc,indent=2)+'\n');inputs.append({'id':ident,'scale':v,'case_sha256':sha(p),'input_sha256':sha(d/'input.json'),'only_Pd_Qd_changed':True})
# Reuse audited 11B implementations via explicit, inspectable parameterization.
base=(R/'experiments/gsfm011b/run_baselines.py').read_text();base=base.replace("W=pathlib.Path('/private/tmp/gsfm011b-20261022');OUT=W/'results'", "W=pathlib.Path('/private/tmp/gsfm011b-20261022');OUT=pathlib.Path(sys.argv[1])")
a="source=ROOT/'results/inference/2026-10-21-base-cases/case300.m';assert sha(source)=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5';c=read_case(source);save(OUT/'input.json',c)";assert a in base;base=base.replace(a,"source=OUT/'case300.m';c=read_case(source);assert c==json.loads((OUT/'input.json').read_text())")
pre,rest=base.split('# Exactly one conventional default AC solve',1);ac,dc=rest.split('# Exactly one DC-OPF solve.',1)
(E/'run_ac.py').write_text(pre+'# Exactly one conventional default AC solve'+ac)
(E/'run_dc.py').write_text(pre+'# Exactly one DC-OPF solve.'+dc)
model=(R/'experiments/gsfm011b/run_model.py').read_text().replace("OUT=W/'results'","OUT=pathlib.Path(sys.argv[2])")
(E/'run_model.py').write_text(model)
evalcode=(R/'experiments/gsfm011b/evaluate.py').read_text().replace("O=W/'results'","O=pathlib.Path(sys.argv[1])").replace('no 11C','six-point loading-only 11C-1')
(E/'evaluate.py').write_text(evalcode)
freeze={'experiment':'11C-1','status':'FROZEN_BEFORE_RUNS','study_code_commit':'1f8ab6645bc20be808d5d40d20f3d73f0856f6de','scales_in_fixed_order':scales,'inputs':inputs,'original_case_sha256':sha(src),'base_reused_directory':str(R/'results/comparisons/GSFM-011B/20261022-original-case300'),'base_artifact_inventory_sha256':sha(R/'results/comparisons/GSFM-011B/20261022-original-case300/artifact-inventory.json'),'thresholds':{'P_Q_balance_MW_MVAr':.001,'Pg_Qg_bounds_MW_MVAr':.001,'Vm_bounds_pu':.0001,'angle_deg':.001},'default_settings':'Exact 11B settings; no clipping override; CPU; no PF completion/repair/training; no model selection','scripts_sha256':{str(p.relative_to(R)):sha(p) for p in E.glob('*.py')},'failed_reference_policy':'No approximation error if AC reference does not pass; retain numerical failure as UNKNOWN; continue scoring native model states'}
(O/'frozen-protocol.json').write_text(json.dumps(freeze,indent=2)+'\n');print(O)
