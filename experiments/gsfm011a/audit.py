"""Experiment11A: bounded read-only pipeline and original-physics audit; no fitting/OPF sweeps."""
import os,sys,pathlib,json,hashlib,copy,subprocess,datetime,importlib.metadata,platform
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XDG_CACHE_HOME='/private/tmp/gsfm011a-20261022-audit/cache')
ROOT=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');WORK=pathlib.Path('/private/tmp/gsfm011a-20261022-audit');OUT=WORK/'results';OUT.mkdir(exist_ok=True)
release=sys.argv[1]
MICRO='1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6';NEW='517a07531ea55a11bd81a89a6c6879695a2ba4b4'
SRC=WORK/'microsoft-source' if release=='microsoft-v1.1' else ROOT/'work/GSFM-006-source-517a075'
CKPT=ROOT.parent/'GridSFM/model/checkpoints/gridsfm_open_v1.1.pt' if release=='microsoft-v1.1' else ROOT/'data/checkpoints/GSFM-006-gridsfm_open_v2.pt'
sys.path[:0]=[str(SRC/'model'),str(ROOT/'scripts/python')]
import numpy as np,torch,gridsfm
from gridsfm import load_model,predict,load_pyg_json,prepare_for_inference
from gridsfm_convert import convert,canonical_hash
from physics_metrics import evaluate,branch_flows
from matpower_case import read_case
from pypower.makeYbus import makeYbus
try:
 from gridsfm.loss import _flows_rx_bidir
except ModuleNotFoundError:
 _flows_rx_bidir=None
import pypower.makeYbus as ymod

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def stats(r):return dict(max_abs_P_MW=float(abs(r.real).max()),mean_abs_P_MW=float(abs(r.real).mean()),max_abs_Q_MVAr=float(abs(r.imag).max()),mean_abs_Q_MVAr=float(abs(r.imag).mean()))
def branch_residual(c,s,sf=None,st=None):
 if sf is None:sf,st=branch_flows(c,s['vm'],s['va_deg'])
 ids={int(b[0]):i for i,b in enumerate(c['bus'])};r=np.array([complex(-b[2],-b[3])-complex(b[4],-b[5])*s['vm'][i]**2 for i,b in enumerate(c['bus'])])
 for g,p,q in zip(c['gen'],s['pg_mw'],s['qg_mvar']):
  if g[7]>0:r[ids[int(g[0])]]+=complex(p,q)
 for b,f,t in zip(c['branch'],sf,st):r[ids[int(b[0])]]-=f;r[ids[int(b[1])]]-=t
 return r

def ybus_check(c,s):
 ids={int(b[0]):i for i,b in enumerate(c['bus'])};b=np.array(c['bus'],dtype=float);e=np.array(c['branch'],dtype=float);b[:,0]=range(len(b));e[:,0]=[ids[int(x[0])] for x in c['branch']];e[:,1]=[ids[int(x[1])] for x in c['branch']]
 Y,Yf,Yt=makeYbus(c['baseMVA'],b,e);V=np.array(s['vm'])*np.exp(1j*np.deg2rad(s['va_deg']));inj=np.array([-complex(x[2],x[3]) for x in c['bus']])
 for g,p,q in zip(c['gen'],s['pg_mw'],s['qg_mvar']):
  if g[7]>0:inj[ids[int(g[0])]]+=complex(p,q)
 r=inj-c['baseMVA']*V*np.conj(Y@V);rb=branch_residual(c,s);sf,st=branch_flows(c,s['vm'],s['va_deg']);f=c['baseMVA']*V[e[:,0].astype(int)]*np.conj(Yf@V);t=c['baseMVA']*V[e[:,1].astype(int)]*np.conj(Yt@V)
 err=max(float(abs(np.array(sf)-f).max()),float(abs(np.array(st)-t).max()));diff=float(abs(r-rb).max());assert diff<1e-6 and err<1e-6,(diff,err)
 return dict(equation='Cg(Pg+jQg)-(Pd+jQd)-baseMVA*V*conj(Ybus*V); Ybus includes bus shunts exactly once',reference_residual=stats(r),branch_sum_residual=stats(rb),max_complex_residual_checker_disagreement_MVA=diff,max_both_end_branch_flow_disagreement_MVA=err,Ybus_nonzeros=Y.nnz,implementation=str(pathlib.Path(ymod.__file__)),implementation_sha256=sha(ymod.__file__))

source=ROOT/'results/inference/2026-10-21-base-cases/case300.m';manifest=json.loads((ROOT/'manifests/matpower-source.json').read_text());assert sha(source)==manifest['files'][0]['sha256'];c=read_case(source)
base=ROOT/'results/inference/2026-10-21-base-cases';saved=json.loads((base/'case300-input.json').read_text());assert all(c[k]==saved[k] for k in ['baseMVA','bus','gen','branch','gencost'])
ref=json.loads((base/'case300-reference.json').read_text());original_metrics=evaluate(c,ref);assert original_metrics['all_tested_constraints_pass']
obj=convert(c);assert obj['metadata']['bus_external_ids']==[int(b[0]) for b in c['bus']];assert obj['metadata']['gen_source_rows']==list(range(69));assert sum(len(obj['grid']['edges'][f]['features']) for f in ['ac_line','transformer'])==411
if release!='microsoft-v1.1':
 for rows in obj['grid']['nodes'].values():
  for row in rows:row.append(1.0)
 for fam in ['ac_line','transformer']:
  for row in obj['grid']['edges'][fam]['features']:row.append(1.0)
# Labels never placed in grid features. Generator PG/QG/VG come from original unsolved matrix.
assert all(row[1]==g[1]/100 and row[4]==g[2]/100 and row[7]==g[5] for row,g in zip(obj['grid']['nodes']['generator'],c['gen']))
variants={'unlabeled':copy.deepcopy(obj),'poisoned_labels':copy.deepcopy(obj),'different_labels':copy.deepcopy(obj)}
variants['poisoned_labels'].update(solution={'nodes':{'bus':[[999.,888.]]*300,'generator':[[777.,666.]]*69}},metadata={'objective':1e100,'other':'ignored labels only'})
variants['different_labels'].update(solution={'nodes':{'bus':[[-123.,-234.]]*300,'generator':[[-345.,-456.]]*69}},metadata={'objective':-1e100})
paths={}
for name,o in variants.items():
 p=WORK/f'{release}-{name}.pyg.json';p.write_text(json.dumps(o));paths[name]=p
 assert o['grid']==obj['grid']
expected='f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831' if release=='microsoft-v1.1' else '9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7'
assert sha(CKPT)==expected
torch.set_num_threads(4);torch.manual_seed(0);m=load_model(CKPT,device='cpu');m.eval();blob=torch.load(CKPT,weights_only=True,map_location='cpu');strict=m.load_state_dict(blob['state_dict'],strict=True)
# Preserve release defaults: newer API uses hard clamp; do NOT copy Exp9/10 sigmoid override.
outputs={name:predict(m,p) for name,p in paths.items()}
for name,o in outputs.items():
 for k,v in o.items():
  if torch.is_tensor(v):assert torch.isfinite(v).all();assert torch.equal(v,outputs['unlabeled'][k]),(name,k)
  elif isinstance(v,(float,int)):
   assert np.isfinite(v) and v==outputs['unlabeled'][k],(name,k)
  else:assert v==outputs['unlabeled'][k],(name,k)
leak=dict(status='PASS',variants=list(variants),all_returned_tensor_predictions_bitwise_identical=True,scalar_and_layout_outputs_identical_and_finite=True,raw_grid_features_identical=True,original_PG_QG_VG_verified=True,base_input_matrix_equal_to_pinned_unsolved_source=True)
# Directly execute this release's branch reconstruction on the saved feasible reference.
# This is an operator audit, not a new predictive accuracy benchmark or PF solve.
operator={}
for precision in ['native_FP32','original_coefficients_FP64']:
 d=prepare_for_inference(load_pyg_json(paths['unlabeled']))
 if precision=='original_coefficients_FP64':
  for nt,rows in obj['grid']['nodes'].items():
   if rows:d[nt].x=torch.tensor(rows,dtype=torch.float64)
  for fam in ['ac_line','transformer']:d['bus',fam,'bus'].edge_attr=torch.tensor(obj['grid']['edges'][fam]['features'],dtype=torch.float64)
 dt=torch.float32 if precision=='native_FP32' else torch.float64
 d['bus'].pred=torch.stack([torch.tensor(np.deg2rad(ref['va_deg']),dtype=dt),torch.tensor(ref['vm'],dtype=dt)],-1)
 d['generator'].pred=torch.tensor(np.array([ref['pg_mw'],ref['qg_mvar']]).T/100,dtype=dt)
 m._compute_flows(d);sf=np.zeros(411,complex);st=sf.copy();lsf=sf.copy();lst=sf.copy()
 for fam in ['ac_line','transformer']:
  edge=d['bus',fam,'bus'];flows=edge.edge_flow_pred.detach().double().numpy()*100;order=obj['metadata'][fam+'_source_rows'];sf[order]=flows[:,0]+1j*flows[:,1];st[order]=flows[:,2]+1j*flows[:,3]
  fe=edge.edge_attr;idx=edge.edge_index
  from gridsfm.schema import AC_LINE_R_IDX,AC_LINE_X_IDX,AC_LINE_BFR_IDX,AC_LINE_BTO_IDX,TR_R_IDX,TR_X_IDX,TR_BFR_IDX,TR_BTO_IDX,TR_TAP_IDX,TR_SHIFT_IDX
  if fam=='ac_line':ri,xi,bi,bj=AC_LINE_R_IDX,AC_LINE_X_IDX,AC_LINE_BFR_IDX,AC_LINE_BTO_IDX;tau=torch.ones(len(order),dtype=dt);phi=torch.zeros(len(order),dtype=dt)
  else:ri,xi,bi,bj=TR_R_IDX,TR_X_IDX,TR_BFR_IDX,TR_BTO_IDX;tau=fe[:,TR_TAP_IDX];phi=fe[:,TR_SHIFT_IDX]
  lv=(_flows_rx_bidir(d['bus'].pred[:,0],d['bus'].pred[:,1],idx[0],idx[1],fe[:,ri],fe[:,xi],fe[:,bi],fe[:,bj],tau,phi) if _flows_rx_bidir else tuple(edge.edge_flow_pred[:,k] for k in range(4)))
  a=[v.detach().double().numpy()*100 for v in lv];lsf[order]=a[0]+1j*a[1];lst[order]=a[2]+1j*a[3]
 # All operators evaluated on the same precision-rounded state/loads/shunts.
 cc=copy.deepcopy(c);ss=copy.deepcopy(ref)
 if precision=='native_FP32':
  ss['vm']=d['bus'].pred[:,1].double().tolist();ss['va_deg']=np.rad2deg(d['bus'].pred[:,0].double().numpy()).tolist();ss['pg_mw']=(d['generator'].pred[:,0].double().numpy()*100).tolist();ss['qg_mvar']=(d['generator'].pred[:,1].double().numpy()*100).tolist()
  # native coefficients include FP32 loads/shunts, matching model storage
  cc['bus']=[list(b) for b in c['bus']]
  for b in cc['bus']:b[2:6]=[float(np.float32(v/100))*100 for v in b[2:6]]
 exact=branch_residual(c,ref);native=branch_residual(cc,ss,sf,st);loss=branch_residual(cc,ss,lsf,lst)
 operator[precision]={'forward_pi_operator':stats(native),'training_loss_pi_operator':stats(loss),'training_operator_note':'Microsoft stock loss denominator floor1e-6' if _flows_rx_bidir else 'Newer elastic_loss uses the same model branch operator; no gridsfm.loss module in this release','max_forward_minus_original_complex_nodal_MVA':float(abs(native-exact).max()),'note':'Reference state only; coefficient/operation rounding and denominator changes are diagnostics, not an attribution of frozen error.'}

fixture={'baseMVA':100.,'bus':[[11,3,0,0,3,7,1,1,0,230,1,1.1,.9],[29,1,0,0,2,-4,1,1,0,230,1,1.1,.9]],'gen':[],'branch':[[11,29,.01,.05,.02,0,0,0,1.07,17.,1,-360,360],[11,29,.02,.08,.03,0,0,0,.98,-11.,0,-360,360]]}
fixturestate={'vm':[1.03,.97],'va_deg':[5.,-7.],'pg_mw':[],'qg_mvar':[]};toy=ybus_check(fixture,fixturestate)
from collections import Counter
pairs=Counter(tuple(sorted([int(b[0]),int(b[1])])) for b in c['branch']);counts={'buses':len(c['bus']),'generators':len(c['gen']),'branches':len(c['branch']),'finite_positive_RATE_A':sum(b[5]>0 for b in c['branch']),'online_generators':sum(g[7]>0 for g in c['gen']),'online_branches':sum(b[10]>0 for b in c['branch']),'parallel_pairs':{str(k):v for k,v in pairs.items() if v>1},'negative_P_load_bus_ids':[int(b[0]) for b in c['bus'] if b[2]<0],'negative_Q_load_bus_ids':[int(b[0]) for b in c['bus'] if b[3]<0],'zero_P_and_Q_load_buses':sum(b[2]==b[3]==0 for b in c['bus']),'nonunity_taps':sum(b[8] not in [0,1] for b in c['branch']),'nonzero_phase_shifts':sum(b[9]!=0 for b in c['branch']),'bus_shunts':sum(b[4]!=0 or b[5]!=0 for b in c['bus']),'small_impedance_loss_floor_rows_1based':[i+1 for i,b in enumerate(c['branch']) if b[2]**2+b[3]**2<1e-6]}
try:
 from pypower.rundcopf import rundcopf
 dc={'available':True,'import_pass':True,'callable':callable(rundcopf),'case300_DC_OPF_executed':False,'version':importlib.metadata.version('PYPOWER')}
except Exception as e:dc={'available_source':True,'import_pass':False,'error':repr(e),'case300_DC_OPF_executed':False}
sourcehash={str(p.relative_to(SRC)):sha(p) for p in sorted((SRC/'model/gridsfm').glob('*.py'))}
result={'status':'PASS','audit':'11A setup/pipeline only; no fitting, selection, OPF/PF solves or sweeps','release':release,'source_commit':MICRO if release=='microsoft-v1.1' else NEW,'source_import':str(gridsfm.__file__),'source_files_sha256':sourcehash,'checkpoint_path':str(CKPT),'checkpoint_sha256':sha(CKPT),'checkpoint_arch_metadata':blob['metadata'],'strict_state_dict_load':str(strict),'parameters':sum(p.numel() for p in m.parameters()),'clip_mode':getattr(m,'clip_mode','leaky_clip'),'leaky_alpha':m.leaky_alpha,'independent_branch_prediction_head':False,'native_predict_runs_newton_PF':False,'model_output_fields':list(outputs['unlabeled']),'case_source_path':str(source),'manifest_original_local_path_exists':(ROOT/'data/source/matpower-8.1/case300.m').exists(),'case_source_sha256':sha(source),'case_input_sha256':sha(base/'case300-input.json'),'case_canonical_sha256':canonical_hash(c),'case_counts':counts,'label_independence':leak,'reference_path':str(base/'case300-reference.json'),'reference_sha256':sha(base/'case300-reference.json'),'reference_exact_metrics':{k:v for k,v in original_metrics.items() if not isinstance(v,list)},'reference_original_Ybus_crosscheck':ybus_check(c,ref),'reference_model_operator':operator,'algebra_unit_fixture_phase_tap_shunt_status':toy,'DC_OPF':dc,'environment':{'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'platform':platform.platform()},'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'study_execution_commit':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()}
(OUT/f'{release}.json').write_text(json.dumps(result,indent=2,default=str,allow_nan=False)+'\n')
print(json.dumps({k:result[k] for k in ['status','release','checkpoint_sha256','parameters','clip_mode','leaky_alpha','case_counts','label_independence','reference_original_Ybus_crosscheck','reference_model_operator','DC_OPF']},indent=2))
