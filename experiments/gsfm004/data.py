"""Generate fixed, accepted-only development streams; retain every attempted solve."""
from common import *
import selectors,collections
class LabelServer:
    def __init__(self):self.proc=None;self.start()
    def start(self):
        self.err=(RUN/'data/solver-stderr.log').open('a')
        self.proc=subprocess.Popen(['/Users/ninadsonawane/julia/bin/julia','--startup-file=no','--project='+str(MODEL/'power_grid/US/topology_solver_pipeline'),str(Path(__file__).with_name('label_server.jl'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1)
        sel=selectors.DefaultSelector();sel.register(self.proc.stdout,selectors.EVENT_READ)
        if not sel.select(30):self.close(kill=True);raise RuntimeError('Julia label server startup timeout')
        assert self.proc.stdout.readline().strip()=='READY';sel.close()
    def request(self,req):
        deadline();self.proc.stdin.write(json.dumps(req)+'\n');self.proc.stdin.flush();sel=selectors.DefaultSelector();sel.register(self.proc.stdout,selectors.EVENT_READ)
        if not sel.select(30):
            sel.close();self.close(kill=True);self.start();return {'status':'WALL_TIMEOUT_30S','solver_failure_is_infeasibility':False}
        line=self.proc.stdout.readline();sel.close()
        if not line:return {'status':'SERVER_EXITED','solver_failure_is_infeasibility':False}
        return json.loads(line)
    def close(self,kill=False):
        if self.proc and self.proc.poll() is None:
            if kill:self.proc.kill()
            else:self.proc.stdin.write('{"quit":true}\n');self.proc.stdin.flush()
            self.proc.wait(timeout=10)
        self.err.close()
def write_m(c,p):
    ss=['function mpc = candidate',"mpc.version = '2';",f'mpc.baseMVA = {c["baseMVA"]};']
    for k in ['bus','gen','branch','gencost']:
        ss.append(f'mpc.{k} = [');ss+=[' '.join(format(v,'.17g') for v in row)+';' for row in c[k]];ss.append('];')
    p.write_text('\n'.join(ss)+'\n')
def label(server,c,sid,split,factors,extra=None):
    path=RUN/'data/candidates'/sid;path.mkdir(parents=True,exist_ok=False)
    save(path/'input.json',c);save(path/'factors.json',factors);write_m(c,path/'candidate.m')
    t=time.perf_counter();resp=server.request({'matpower_path':str(path/'candidate.m'),'result_path':str(path/'solver-result.json'),'log_path':str(path/'solver.log')})
    rec={'scenario_id':sid,'split':split,'status':resp['status'],'accepted':False,'elapsed_seconds':time.perf_counter()-t,'input_sha256':sha(path/'input.json'),'factor_sha256':sha(path/'factors.json'),'path':str(path),**(extra or {})}
    if resp['status'] in ['LOCALLY_SOLVED','OPTIMAL']:
        raw=read(path/'solver-result.json');sol=raw['solution'];s={'vm':[sol['bus'][str(int(b[0]))]['vm'] for b in c['bus']],'va_deg':[math.degrees(sol['bus'][str(int(b[0]))]['va']) for b in c['bus']],'pg_mw':[sol['gen'][str(i+1)]['pg']*100 for i in range(len(c['gen']))],'qg_mvar':[sol['gen'][str(i+1)]['qg']*100 for i in range(len(c['gen']))]}
        metrics=evaluate(c,s);save(path/'reference-metrics.json',metrics);save(path/'reference.json',s)
        if metrics['all_tested_constraints_pass']:
            rec['accepted']=True;labels={**s,'objective':raw['objective'],'accepted_feasible':True,**{k:metrics[k] for k in ['pf_mw','qf_mvar','pt_mw','qt_mvar']}}
            save(path/'labeled.pyg.json',convert(c,labels))
        else:rec['rejection']='independent physical gate'
    else:rec['rejection']='solver failure/unknown, not infeasibility label'
    save(path/'record.json',rec);return rec
def regions(base):
    positive=sorted(int(b[0]) for b in base['bus'] if b[2]>0);adj={int(b[0]):set() for b in base['bus']}
    for b in base['branch']:
        if b[10]:adj[int(b[0])].add(int(b[1]));adj[int(b[1])].add(int(b[0]))
    def bfs(c):
        dist={c:0};q=collections.deque([c])
        while q:
            u=q.popleft()
            for v in sorted(adj[u]):
                if v not in dist:dist[v]=dist[u]+1;q.append(v)
        return dist
    centers=[positive[0]];dists=[bfs(centers[0])]
    while len(centers)<4:
        c=min((b for b in positive if b not in centers),key=lambda b:(-min(d[b] for d in dists),b));centers.append(c);dists.append(bfs(c))
    size=math.ceil(len(positive)/4)
    return {'definition_N':'number of positive-Pd buses','positive_bus_count':len(positive),'region_size':size,'centers':centers,'memberships':[sorted(positive,key=lambda b:(d[b],b))[:size] for d in dists]}
def main():
    (RUN/'data').mkdir(parents=True,exist_ok=True)
    if (RUN/'data/manifest.json').exists():raise RuntimeError('Existing data must be reused, not regenerated')
    base=read(BASE/'case300-input.json');reg=regions(base);save(RUN/'data/regions.json',reg)
    manifests={};seen={content_hash(base)};server=LabelServer()
    try:
        streams=[('smoke_train',8,3002026,.90,1.03,32),('smoke_validation',4,None,.90,1.03,24),('train',50,30401,.90,1.03,150),('validation',10,30402,.90,1.03,30),('ordinary',10,30403,.90,1.03,30),('higher_load',10,30405,1.035,1.06,30)]
        smoke_rng=np.random.Generator(np.random.PCG64(3002026));smoke_attempts=0
        for split,n,seed,lo,hi,cap in streams:
            rng=smoke_rng if split.startswith('smoke') else np.random.Generator(np.random.PCG64(seed));recs=[];accepted=0
            for i in range(cap):
                if accepted>=n:break
                if split.startswith('smoke') and smoke_attempts>=32:break
                if split.startswith('smoke'):smoke_attempts+=1
                globalfactor=float(rng.uniform(lo,hi));jit=rng.uniform(.98,1.02,len(base['bus']));factors=globalfactor*jit;c=copy.deepcopy(base)
                for b,original,f in zip(c['bus'],base['bus'],factors):b[2]=original[2]*f;b[3]=original[3]*f
                hc=content_hash(c)
                if hc in seen:raise RuntimeError('Duplicate scenario encountered')
                seen.add(hc);sid=f'{split}-{i:03d}'
                rec=label(server,c,sid,split,{'seed':seed if seed else 3002026,'global_scale':globalfactor,'bus_jitter':jit.tolist(),'actual_combined_factors':factors.tolist(),'bus_order':[int(b[0]) for b in base['bus']]})
                recs.append(rec);accepted+=int(rec['accepted'])
                if (i+1)%10==0 or accepted==n:log('labels_progress',split=split,accepted=accepted,attempted=len(recs))
            manifests[split]=recs;save(RUN/'data/partial-manifest.json',manifests)
            if split in ['train','validation','smoke_train','smoke_validation'] and accepted<n:raise RuntimeError(f'{split}: accepted count shortfall {accepted}/{n}')
        recs=[];pairs=[r for r in manifests['ordinary'] if r['accepted']][:10]
        for j,original in enumerate(pairs):
            c=read(Path(original['path'])/'input.json');eligible=[i for i,b in enumerate(c['bus']) if b[2]>0];region=set(reg['memberships'][j%4]);u=np.array([1. if int(c['bus'][i][0]) in region else -1. for i in eligible]);A=np.array([[c['bus'][i][k] for i in eligible] for k in [2,3]],dtype=float);norms=np.linalg.norm(A,axis=1);An=A[norms>0]/norms[norms>0,None];_,s,Vh=np.linalg.svd(An,full_matrices=False);tol=1e-12*s[0];Vr=Vh[s>tol];d=u-Vr.T@(Vr@u)
            if max(abs(d))<1e-10:recs.append({'scenario_id':f'spatial-{j:03d}','accepted':False,'status':'DEGENERATE','pair_id':original['scenario_id']});continue
            sign=1 if (j//4)%2==0 else -1;f=1+sign*.10*d/max(abs(d));before=np.array([[b[2],b[3]] for b in c['bus']]);total_before=before.sum(axis=0)
            for i,ff in zip(eligible,f):c['bus'][i][2]*=float(ff);c['bus'][i][3]*=float(ff)
            after=np.array([[b[2],b[3]] for b in c['bus']]);delta=after-before;res=after.sum(axis=0)-total_before;scale=np.maximum(1,np.abs(before).sum(axis=0));assert np.all(abs(res)<=1e-8*scale)
            extra={'pair_id':original['scenario_id'],'region_index':j%4,'rank':int(sum(s>tol)),'singular_values':s.tolist(),'svd_tolerance':float(tol),'P_Q_total_difference':res.tolist(),'demand_absolute_moved_MW_MVAr':(np.abs(delta).sum(axis=0)/2).tolist(),'region_net_change_MW_MVAr':delta[[int(b[0]) in region for b in c['bus']]].sum(axis=0).tolist()}
            combined=np.ones(300);combined[eligible]=f
            rec=label(server,c,f'spatial-{j:03d}','spatial',{'seed':30404,'seed_note':'deterministic SVD projection; no random draws required','region':j%4,'actual_factors':combined.tolist(),'eligible_indices':eligible},extra);recs.append(rec)
        manifests['spatial']=recs;save(RUN/'data/manifest.json',manifests)
        counts={k:{'accepted':sum(r['accepted'] for r in rs),'attempted':len(rs)} for k,rs in manifests.items()};save(RUN/'data/counts.json',counts);log('DATA_COMPLETE',counts=counts)
    finally:server.close()
if __name__=='__main__':main()
