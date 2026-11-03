import os,sys,pathlib,time,copy,traceback,contextlib,io
os.environ.update(PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='4')
from electrical import *
from pypower.rundcopf import rundcopf
from pypower.ppoption import ppoption
D=pathlib.Path(sys.argv[1]);c=read(D/'input.json');B,F,pb,pf,err=dc_matrices(c);ids,b,e,f,t=matrices(c);options=ppoption(VERBOSE=0,OUT_ALL=0,OPF_ALG_DC=200,PDIPM_MAX_IT=150,PDIPM_FEASTOL=1e-10,PDIPM_GRADTOL=1e-9,PDIPM_COMPTOL=1e-9,COST_MULT=1.0);ppc={k:np.array(c[k],float) if k in ['bus','gen','branch','gencost'] else c[k] for k in ['version','baseMVA','bus','gen','branch','gencost']}
# MATPOWERv2 permits omitted optional generator fields; PYPOWER infers v1 from width<21.
# Zero-extend only absent optional fields at solver boundary; preserve input matrices.
original_gen_width=ppc['gen'].shape[1]
if original_gen_width<21:ppc['gen']=np.pad(ppc['gen'],((0,0),(0,21-original_gen_width)),constant_values=0.)
from pypower.loadcase import loadcase
canonical=loadcase(copy.deepcopy(ppc));assert np.array_equal(canonical['branch'],np.array(c['branch']));assert np.array_equal(canonical['gen'][:,:original_gen_width],np.array(c['gen']))
save(D/'dc-input-adapter-audit.json',{'status':'PASS','original_generator_columns':original_gen_width,'solver_generator_columns':21 if original_gen_width<21 else original_gen_width,'optional_missing_generator_columns_zero_extended_only':True,'original_all_fields_and_branch_angles_preserved':True,'reason':'PYPOWER loadcase infers v1 from<21 gen columns even with dict version2; zero-extension preserves MATPOWERv2 semantics'})
stream=io.StringIO();start=time.perf_counter()
try:
 with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):res=rundcopf(copy.deepcopy(ppc),options)
 save(D/'dc-raw.json',res);assert np.array_equal(res['bus'][:,0],np.array(c['bus'])[:,0]);assert np.array_equal(res['gen'][:,0],np.array(c['gen'])[:,0]);assert np.array_equal(res['branch'][:,:13],np.array(c['branch']));assert np.array_equal(res['gencost'],np.array(c['gencost']))
 angle=res['bus'][:,8];flows=c['baseMVA']*(F@np.deg2rad(angle)+pf);assert max(abs(flows-res['branch'][:,13]))<1e-6
 s={'pg_mw':res['gen'][:,1].tolist(),'qg_mvar':None,'vm':None,'va_deg':angle.tolist(),'pf_mw':flows.tolist(),'pt_mw':(-flows).tolist()};save(D/'dc-native.json',s);summary,*_=score(c,s,'DC-OPF');save(D/'dc-status.json',{'solver_success':bool(res['success']),'status':'CONVERGED' if res['success'] else 'FAILED_UNKNOWN','iterations':res['raw']['output'].get('iterations'),'message':res['raw']['output'].get('message'),'objective':res['f'],'seconds':time.perf_counter()-start,'makeBdc_manual_disagreement':err,'options':options,'independent_DC_constraints_pass':summary['native_DC_constraints_pass']})
except AssertionError:
 save(D/'dc-failure.json',{'status':'PIPELINE_GATE_FAILED','traceback':traceback.format_exc()});raise
except Exception:save(D/'dc-failure.json',{'status':'FAILED_UNKNOWN','traceback':traceback.format_exc(),'seconds':time.perf_counter()-start})
finally:(D/'dc.log').write_text(stream.getvalue())
