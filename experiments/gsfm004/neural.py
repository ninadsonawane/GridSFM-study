"""Controlled regression objectives and original-precision physics for GSFM-004.

The released supervised formula is reproduced with its helpers. Both KCL arms
share float64 original parameters and aggregation; only z² treatment differs.
The installed model is never edited. The disconnected feasibility/stress tail
is skipped by a process-local, source-derived method override.
"""
from common import *
import torch,inspect,ast,textwrap,types,gc
from torch import nn
from gridsfm import load_model,batch_data_list,GridTransformerBackbone,GridSFMLoRAModel,LoRAConfig
from gridsfm_adapter import to_data
import gridsfm.model as model_module
import gridsfm.blocks as blocks_module
from gridsfm.loss import _per_graph_mean,PER_ELEM_CAP,build_feasible_masks,_gather_flow_inputs
from gridsfm.blocks import _slack_or_mean_anchor
CKPT=MODEL/'model/checkpoints/gridsfm_open_v1.1.pt'
HEADS=('head_theta','head_V','head_Pg','head_Qg')
def assert_finite(x,where):
    if isinstance(x,torch.Tensor):
        if x.numel() and not torch.isfinite(x).all():raise FloatingPointError('nonfinite '+where)
    elif isinstance(x,dict):
        for k,v in x.items():assert_finite(v,where+'.'+str(k))
    elif isinstance(x,(tuple,list)):
        for i,v in enumerate(x):assert_finite(v,where+'.'+str(i))
def sanitizer_guard():
    if getattr(model_module,'_gsfm004_guarded',False):return
    original=blocks_module._nan_to_zero
    def guard(x,sub_value=0.):assert_finite(x,'before output sanitizer');return original(x,sub_value)
    blocks_module._nan_to_zero=guard;model_module._nan_to_zero=guard;model_module._gsfm004_guarded=True
def disable_auxiliary_tail(m):
    source=textwrap.dedent(inspect.getsource(GridTransformerBackbone._predict_and_write));tree=ast.parse(source);fn=tree.body[0]
    stop=next(i for i,node in enumerate(fn.body) if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='_compute_flows')
    fn.body=fn.body[:stop+1]+ast.parse("data.feas_logit = torch.zeros(n_graphs, dtype=V.dtype, device=V.device)").body
    ast.fix_missing_locations(tree);namespace=dict(model_module.__dict__);exec(compile(tree,'<GSFM004 regression-only tail>','exec'),namespace)
    m._predict_and_write=types.MethodType(namespace['_predict_and_write'],m)
    return hashlib.sha256(source.encode()).hexdigest()
def make_model(arm,guard=True):
    seed_all(11)
    if guard:sanitizer_guard()
    if arm=='R':
        blob=torch.load(CKPT,weights_only=True,map_location='cpu');base=GridTransformerBackbone(**(blob['metadata'].get('arch') or {}))
        assert set(base.state_dict())==set(blob['state_dict'])
        assert all(base.state_dict()[k].shape==v.shape for k,v in blob['state_dict'].items())
        assert not torch.equal(base.state_dict()['head_theta.0.weight'],blob['state_dict']['head_theta.0.weight']) if 'head_theta.0.weight' in blob['state_dict'] else True
    else:base=load_model(CKPT,device='cpu')
    disable_auxiliary_tail(base)
    if arm=='L':
        m=GridSFMLoRAModel(base);m.add_adapter(LoRAConfig(rank=2,alpha=2.,dropout=0.),name='pilot')
        for head in HEADS:getattr(base,head).requires_grad_(True)
    else:
        m=base
        if arm in ['H','F']:
            for p in m.parameters():p.requires_grad_(False)
            if arm=='H':
                for head in HEADS:getattr(m,head).requires_grad_(True)
    base.head_feas.requires_grad_(False)
    m.eval() if arm=='F' else m.train()
    return m
def trainable_manifest(m,arm):
    names=[(n,p.numel()) for n,p in m.named_parameters() if p.requires_grad]
    return {'arm':arm,'trainable':sum(c for n,c in names),'total':sum(p.numel() for p in m.parameters()),'names':names,'head_feas_frozen':all(not p.requires_grad for n,p in m.named_parameters() if 'head_feas' in n),'initialization':'fresh architecture random seed11' if arm=='R' else 'pinned pretrained checkpoint; independent reload'}
class Physics:
    def __init__(self,c):
        self.case=c;self.base=float(c['baseMVA']);ids={int(b[0]):i for i,b in enumerate(c['bus'])}
        self.i=torch.tensor([ids[int(b[0])] for b in c['branch']],dtype=torch.long);self.j=torch.tensor([ids[int(b[1])] for b in c['branch']],dtype=torch.long)
        self.gbus=torch.tensor([ids[int(g[0])] for g in c['gen']],dtype=torch.long)
        T=lambda a:torch.tensor(a,dtype=torch.float64)
        self.r=T([b[2] for b in c['branch']]);self.x=T([b[3] for b in c['branch']]);self.b=T([b[4]/2 for b in c['branch']]);self.tau=T([b[8] or 1 for b in c['branch']]);self.phi=T([math.radians(b[9]) for b in c['branch']]);self.pd=T([b[2]/self.base for b in c['bus']]);self.qd=T([b[3]/self.base for b in c['bus']]);self.gs=T([b[4]/self.base for b in c['bus']]);self.bs=T([b[5]/self.base for b in c['bus']]);self.cp=float(sum(abs(g[8]) for g in c['gen']))/self.base;self.cq=float(sum(abs(g[3]) for g in c['gen']))/self.base
        if not torch.all(torch.isfinite(self.r*self.r+self.x*self.x)) or torch.any(self.r*self.r+self.x*self.x==0):raise ValueError('invalid original branch impedance')
        self.rated=sum(b[5]>0 for b in c['branch']);assert self.rated==0
    def residual(self,theta,V,Pg,Qg,mode='exact'):
        theta,V,Pg,Qg=[v.double() for v in (theta,V,Pg,Qg)];z2=self.r*self.r+self.x*self.x
        if mode=='stock':z2=z2.clamp_min(1e-6)
        elif mode!='exact':raise ValueError(mode)
        g=self.r/z2;b=-self.x/z2;Vi=V[self.i];Vj=V[self.j];d=theta[self.i]-theta[self.j]-self.phi;co=torch.cos(d);si=torch.sin(d);tau=self.tau
        pf=Vi*Vi*g/tau**2-Vi*Vj/tau*(g*co+b*si);qf=-Vi*Vi*(b+self.b)/tau**2+Vi*Vj/tau*(b*co-g*si)
        pt=Vj*Vj*g-Vi*Vj/tau*(g*co-b*si);qt=-Vj*Vj*(b+self.b)+Vi*Vj/tau*(b*co+g*si)
        zero=V.new_zeros(len(self.case['bus']));flowp=zero.scatter_add(0,self.i,pf).scatter_add(0,self.j,pt);flowq=zero.scatter_add(0,self.i,qf).scatter_add(0,self.j,qt)
        pg=zero.scatter_add(0,self.gbus,Pg);qg=zero.scatter_add(0,self.gbus,Qg)
        return flowp-(pg-self.pd-self.gs*V**2),flowq-(qg-self.qd+self.bs*V**2)
    def kcl(self,batch,mode):
        bp=batch['bus'].pred;gp=batch['generator'].pred;rp,rq=self.residual(bp[:,0],bp[:,1],gp[:,0],gp[:,1],mode)
        def agg(r,cap):
            nr=(r/max(cap,1e-6)).abs();return .8*(nr-.01).clamp_min(0).max()+.2*nr.mean()
        return agg(rp,self.cp),agg(rq,self.cq)
class Item:
    def __init__(self,record):
        self.record=record;self.path=Path(record['path']);self.case=read(self.path/'input.json');self.ref=read(self.path/'reference.json');self.obj=read(self.path/'labeled.pyg.json');self.data=to_data(self.obj,training=True);self.physics=Physics(self.case)
    def batch(self):return batch_data_list([self.data.clone()])
def load_split(name,manifest=None):
    manifest=manifest or read(RUN/'data/manifest.json');return [Item(r) for r in manifest[name] if r['accepted']]
def objective(out,physics,arm):
    masks=build_feasible_masks(out);assert bool(masks['gmask'].all());bp=out['bus'].pred;bt=out['bus'].y;gp=out['generator'].pred;gt=out['generator'].y;gb=out['bus'].batch;gg=out['generator'].batch;G=int(out.num_graphs)
    anchored=_slack_or_mean_anchor(out,bt[:,0],G);dt=torch.atan2(torch.sin(bp[:,0]-anchored),torch.cos(bp[:,0]-anchored));Vmean=_per_graph_mean(bt[:,1],gb,G);var=_per_graph_mean((bt[:,1]-Vmean[gb])**2,gb,G);std=var.sqrt().clamp_min(.01)
    cap=lambda x:100*torch.tanh(x/100)
    components={'theta':_per_graph_mean(cap(dt**2),gb,G).mean(),'V':_per_graph_mean(cap(((bp[:,1]-bt[:,1])/std[gb])**2),gb,G).mean(),'Pg':_per_graph_mean(cap((gp[:,0]-gt[:,0])**2),gg,G).mean(),'Qg':_per_graph_mean(cap((gp[:,1]-gt[:,1])**2),gg,G).mean()}
    gx=out['generator'].x;cost=lambda p:(gx[:,8]*p**2+gx[:,9]*p+gx[:,10]).sum();components['cost']=(torch.log1p(cost(gp[:,0]).clamp_min(0))-torch.log1p(cost(gt[:,0]).clamp_min(0)))**2
    raw={};contrib=dict(components)
    if arm in ['C','E']:
        assert G==1
        kp,kq=physics.kcl(out,'stock' if arm=='C' else 'exact');raw={'kcl_p':kp,'kcl_q':kq};contrib['kcl_p']=torch.log1p(kp);contrib['kcl_q']=torch.log1p(kq)
    else:
        raw={'kcl_p':bp.new_zeros(()),'kcl_q':bp.new_zeros(())};contrib['kcl_p']=raw['kcl_p'];contrib['kcl_q']=raw['kcl_q']
    # RATE_A=0 => no eligible released branch masks. No invalid disabled auxiliary work.
    assert physics.rated==0
    loss=sum(contrib.values());assert_finite(loss,'total objective')
    parts={'raw':{k:float(v.detach()) for k,v in {**components,**raw}.items()},'weighted':{k:float(v.detach()) for k,v in contrib.items()},'active':{'feasible_graphs':G,'buses':bp.shape[0],'generators':gp.shape[0],'rated_branches':0,'branch_supervision':0,'feasibility_objective':False,'stress_objective':False},'total':float(loss.detach())}
    return loss,parts
def evaluate_model(model,items,save_path=None):
    previous=model.training;model.eval();rows=[];preds=[];t=time.perf_counter()
    with torch.no_grad():
        for item in items:
            deadline();out=model(item.batch());p=physical_state(out);m=score(item.case,p,item.ref);m['scenario_id']=item.record['scenario_id'];m['pair_id']=item.record.get('pair_id');rows.append(m);preds.append({'scenario_id':item.record['scenario_id'],'prediction':p,'metrics':m})
    model.train(previous)
    if save_path:save(save_path,preds)
    return rows,time.perf_counter()-t
def checkpoint(model,optimizer,arm,update,path,order=None):
    # Full state includes trained heads and LoRA matrices; optimizer/RNG supports resume.
    obj={'arm':arm,'update':update,'model_state':model.state_dict(),'optimizer_state':optimizer.state_dict() if optimizer else None,'torch_rng':torch.get_rng_state(),'numpy_rng':np.random.get_state(),'python_rng':random.getstate(),'order':order,'checkpoint_sha256':sha(CKPT)}
    tmp=Path(str(path)+'.partial');torch.save(obj,tmp);os.replace(tmp,path)
def load_checkpoint(model,path):
    blob=torch.load(path,weights_only=False,map_location='cpu');model.load_state_dict(blob['model_state'],strict=True);return blob
def check_gradients(model):
    count=0;normsq=0.
    for n,p in model.named_parameters():
        if p.grad is not None:
            assert p.requires_grad,n;assert_finite(p.grad,'gradient '+n);count+=1;normsq+=float(p.grad.double().square().sum())
        assert_finite(p,'parameter '+n)
    if not count:raise RuntimeError('no gradients reached trainable parameters')
    return {'gradient_parameter_tensors':count,'unclipped_norm':math.sqrt(normsq)}
