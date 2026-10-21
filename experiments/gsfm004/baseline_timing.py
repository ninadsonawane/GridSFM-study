"""Fill missing cheap-baseline setup timing/RSS, without another tuning search."""
from common import *
import psutil,resource
mode=sys.argv[1];assert mode in ['nearest','ridge'];deadline();proc=psutil.Process();t=time.perf_counter()
manifest=read(RUN/'data/manifest.json');records=[r for r in manifest['train'] if r['accepted']]
cases=[read(Path(r['path'])/'input.json') for r in records];refs=[read(Path(r['path'])/'reference.json') for r in records]
X=np.array([[b[2] for b in c['bus']]+[b[3] for b in c['bus']] for c in cases]);Y=np.array([encode_state(s) for s in refs]);xm=X.mean(0);xs=X.std(0);mask=xs>1e-12;Xz=(X[:,mask]-xm[mask])/xs[mask];preprocessing_seconds=time.perf_counter()-t
if mode=='ridge':
    alpha=read(RUN/'baselines/ridge-selection.json')['alpha'];ym=Y.mean(0);ys=Y.std(0);outmask=ys>1e-12;Yz=np.zeros_like(Y);Yz[:,outmask]=(Y[:,outmask]-ym[outmask])/ys[outmask];xbar=Xz.mean(0);ybar=Yz.mean(0);xc=Xz-xbar;yc=Yz-ybar;W=xc.T@np.linalg.solve(xc@xc.T+alpha*np.eye(len(records)),yc)
    stored=np.load(RUN/'baselines/linear-models.npz');assert np.array_equal(W,stored['W']);effective=int((mask.sum()+1)*outmask.sum())
else:effective=0
result={'method':mode,'status':'COMPLETE','standalone_fit_including_input_read_seconds':time.perf_counter()-t,'input_read_and_input_preprocessing_seconds':preprocessing_seconds,'peak_process_tree_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'available_memory_bytes':psutil.virtual_memory().available,'trainable_parameters_effective':effective,'tuning_repeated':False,'same_ridge_coefficients_bitwise':True if mode=='ridge' else None,'measurement_context':'standalone NumPy-only process; includes imports in peak RSS; distinct from neural resident-data process; no accuracy retuning'}
save(RUN/f'baselines/{mode}-timing-audit.json',result);log('BASELINE_TIMING_AUDIT',**result)
