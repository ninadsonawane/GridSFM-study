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
