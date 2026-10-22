"""11B one original case300: conventional AC and MATPOWER-equivalent DC only."""
import os,sys,json,pathlib,hashlib,datetime,subprocess,copy,traceback,time,io,contextlib
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='4',MKL_NUM_THREADS='1')
ROOT=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');W=pathlib.Path('/private/tmp/gsfm011b-20261022');OUT=W/'results';sys.path.insert(0,str(ROOT/'scripts/python'))
import numpy as np,scipy.sparse as sp
from matpower_case import read_case
from physics_metrics import evaluate,cost
from pypower.makeBdc import makeBdc
from pypower.rundcopf import rundcopf
from pypower.ppoption import ppoption
from pypower.makeAang import makeAang

def serial(o):
 if isinstance(o,np.ndarray):return o.tolist()
 if isinstance(o,np.generic):return o.item()
 if sp.issparse(o):return {'shape':o.shape,'rows':o.tocoo().row.tolist(),'cols':o.tocoo().col.tolist(),'data':o.tocoo().data.tolist()}
 return str(o)
def save(p,d):pathlib.Path(p).write_text(json.dumps(d,indent=2,default=serial,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
source=ROOT/'results/inference/2026-10-21-base-cases/case300.m';assert sha(source)=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5';c=read_case(source);save(OUT/'input.json',c)
assert len(c['bus'])==300 and len(c['gen'])==69 and len(c['branch'])==411 and not any(b[5] for b in c['branch'])
ids={int(b[0]):i for i,b in enumerate(c['bus'])};bus=np.array(c['bus']);branch=np.array(c['branch']);bus[:,0]=np.arange(300);branch[:,0]=[ids[int(b[0])] for b in c['branch']];branch[:,1]=[ids[int(b[1])] for b in c['branch']]
# Independently construct exactly the pinned MATPOWER8.1 makeBdc stamps.
nb,nl=300,411;rows=np.arange(nl);f=branch[:,0].astype(int);t=branch[:,1].astype(int);C=sp.csr_matrix((np.r_[np.ones(nl),-np.ones(nl)],(np.r_[rows,rows],np.r_[f,t])),shape=(nl,nb));b=branch[:,10]/branch[:,3]/np.where(branch[:,8]!=0,branch[:,8],1);Bf_manual=sp.diags(b)@C;B_manual=C.T@Bf_manual;pf_manual=-b*np.deg2rad(branch[:,9]);pb_manual=C.T@pf_manual
B,Bf,pb,pf=makeBdc(100,bus,branch)
err=[float(abs(a-bb).max()) for a,bb in [(B.toarray(),B_manual.toarray()),(Bf.toarray(),Bf_manual.toarray()),(pb,pb_manual),(pf,pf_manual)]];assert max(err)<1e-12
# Algebra-only single-branch probe exercises nonzero shift, tap and offline status;
# no extra benchmark case or optimization is generated.
probe=[]
for status in [1,0]:
 eb=np.array([[0,1,.01,.05,.02,0,0,0,1.07,17,status,-360,360.]])
 bb,ff,pp,qq=makeBdc(100,np.array([[0]+[0]*12,[1]+[0]*12],float),eb);want=status/.05/1.07;assert np.allclose(ff.toarray(),[[want,-want]],rtol=0,atol=1e-14);assert abs(qq[0]+want*np.deg2rad(17))<1e-14;probe.append({'status':status,'tap':1.07,'phase_deg':17,'Bf':ff.toarray().tolist(),'Pfinj':qq.tolist()})
Aang,lo,hi,angrows=makeAang(100,branch,nb,ppoption());assert len(angrows)==0;assert all(g[4]<=g[3] and g[9]<=g[8] for g in c['gen']);assert all(row[0]==2 and row[3]==3 and row[4]>=0 for row in c['gencost'])
import pypower.makeBdc as bdmod, pypower.opf_setup as setupmod, pypower.dcopf_solver as dcmod
save(OUT/'dc-equation-audit.json',{'status':'PASS','pinned_MATPOWER_commit':'1a828c7af590714499284e36ee9c81273388c594','pinned_source_sha256':{p.name:sha(p) for p in [W/'makeBdc.m',W/'opf_setup.m',W/'makeAang.m']},'implementation_sha256':{str(p):sha(p) for p in [bdmod.__file__,setupmod.__file__,dcmod.__file__]},'max_matrix_disagreement':err,'equations':'Bbus=Cft.T diag(status/x/tap) Cft; Bf=diag(status/x/tap) Cft; Pfinj=-(status/x/tap)*shift_rad; Pbusinj=Cft.T Pfinj; CgPg-(Pd+Gs)=baseMVA*(Bbus theta+Pbusinj)','generation_cost':'Original quadratic polynomial in MW; same coefficients and Pg bounds; Q costs absent. Positive-semidefinite diagonal Hessian. No cost rescaling/replacement.','native_DC_variables':'Pg and bus angles only; Vm and Qg placeholders in PYPOWER result are not predictions and excluded.','finite_RATE_A_constraints':0,'active_angle_constraints':len(angrows),'original_taps_preserved':True,'nonbenchmark_algebra_probe':probe,'solver':'PYPOWER5.1.21 rundcopf, explicit PIPS QP algorithm200; not assumed equivalent merely from a DCP name'})
# Exactly one conventional default AC solve through the already audited builder.
req={'run_id':'11B-one-case300-AC','method':'default','matpower_file':str(source),'log_path':str(OUT/'ac-solver.log'),'result_path':str(OUT/'ac-result.json'),'load_scale':1.,'remaining_seconds':30.,'capture_internal_iterate':False}
cmd=['/Users/ninadsonawane/julia/bin/julia','--startup-file=no','--history-file=no','--compiled-modules=existing','--project='+str(ROOT.parent/'GridSFM/power_grid/US/topology_solver_pipeline'),str(ROOT/'experiments/gsfm007/solver_server.jl')]
t=time.perf_counter();p=subprocess.run(cmd,input=json.dumps(req)+'\n'+json.dumps({'quit':True})+'\n',capture_output=True,text=True,timeout=120);(OUT/'ac-server-stdout.log').write_text(p.stdout);(OUT/'ac-server-stderr.log').write_text(p.stderr);save(OUT/'ac-command.json',{'command':cmd,'request':req,'returncode':p.returncode,'wall_seconds':time.perf_counter()-t});assert p.returncode==0
raw=json.loads((OUT/'ac-result.json').read_text());assert raw['termination_status']=='LOCALLY_SOLVED',raw['termination_status'];s=raw['solution'];ref={'vm':[s['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[np.rad2deg(s['bus'][str(int(b[0]))]['va']) for b in c['bus']],'pg_mw':[s['gen'][str(i+1)]['pg']*100 for i in range(69)],'qg_mvar':[s['gen'][str(i+1)]['qg']*100 for i in range(69)]};save(OUT/'ac-native.json',ref);m=evaluate(c,ref);save(OUT/'ac-independent-metrics.json',m);assert m['all_tested_constraints_pass'];assert abs(m['generation_cost_per_hour']-raw['objective'])<1e-5
for j,br in enumerate(c['branch'],1):
 actual=raw['network_fields']['branch'][str(j)]
 for key,val in [('br_r',br[2]),('br_x',br[3]),('tap',br[8] or 1),('shift',np.deg2rad(br[9])),('angmin',np.deg2rad(br[11])),('angmax',np.deg2rad(br[12])),('rate_a',0)]:assert abs(actual.get(key,0)-val)<1e-10
 for key in ['pf','qf','pt','qt']:assert abs(s['branch'][str(j)][key]*100-m[key+'_mw' if key in ['pf','pt'] else key+'_mvar'][j-1])<1e-6
print('AC reference independently feasible',flush=True)
# Exactly one DC-OPF solve. Preserve failure/exception and raw container if it fails.
ppc={k:np.array(c[k],dtype=float) if k in ['bus','gen','branch','gencost'] else c[k] for k in c};options=ppoption(VERBOSE=0,OUT_ALL=0,OPF_ALG_DC=200,PDIPM_MAX_IT=150,PDIPM_FEASTOL=1e-10,PDIPM_GRADTOL=1e-9,PDIPM_COMPTOL=1e-9,COST_MULT=1.0);stream=io.StringIO();t=time.perf_counter()
try:
 with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):res=rundcopf(copy.deepcopy(ppc),options)
 # Full raw solver container remains local; includes copies of original Qg/Vm fields.
 save(OUT/'dc-result-raw.json',res);assert bool(res['success']),res.get('raw')
 assert np.array_equal(res['bus'][:,0],np.array(c['bus'])[:,0]);assert np.array_equal(res['gen'][:,0],np.array(c['gen'])[:,0]);assert np.array_equal(res['branch'][:,:2],np.array(c['branch'])[:,:2]);assert np.array_equal(res['gencost'],np.array(c['gencost']))
 va=np.deg2rad(res['bus'][:,8]);pg=res['gen'][:,1];flows=100*(Bf@va+pf);inj=-np.array([bb[2]+bb[4] for bb in c['bus']]);np.add.at(inj,[ids[int(g[0])] for g in c['gen']],pg);mismatch=inj-100*(B@va+pb)
 assert max(abs(mismatch))<1e-3;assert max(abs(flows-res['branch'][:,13]))<1e-6;assert max(abs(res['branch'][:,15]+flows))<1e-6
 assert abs(cost(c,pg,[0]*69)-res['f'])<1e-5
 native={'pg_mw':pg.tolist(),'va_deg':res['bus'][:,8].tolist(),'pf_mw':flows.tolist(),'pt_mw':(-flows).tolist(),'qg_mvar':None,'vm':None,'note':'Qg and Vm are NOT DC predictions. Original/copied or nominal result-container fields intentionally excluded; no AC physical state fabricated.'};save(OUT/'dc-native.json',native)
 save(OUT/'dc-status.json',{'status':'CONVERGED','success':bool(res['success']),'objective_per_hour':res['f'],'iterations':res['raw']['output'].get('iterations'),'solver_raw':res['raw'],'options':options,'wall_seconds':time.perf_counter()-t,'max_DC_P_balance_MW':float(abs(mismatch).max()),'mean_DC_P_balance_MW':float(abs(mismatch).mean())});print('DC converged',res['f'],'max balance',max(abs(mismatch)),flush=True)
except Exception:
 save(OUT/'dc-failure.json',{'status':'FAILED','traceback':traceback.format_exc(),'wall_seconds':time.perf_counter()-t});print('DC failure retained',traceback.format_exc(),flush=True)
finally:(OUT/'dc-solver.log').write_text(stream.getvalue())
