"""Study mapping around the unchanged author Newton kernel. No training or repair."""
from paths import *
import copy, hashlib, json, numpy as np, torch
import closure
from gridsfm.data import load_pyg_json
from pypower.bustypes import bustypes
from study import read, save, evaluate
from electrical import matrices, makeYbus

PIN = '517a07531ea55a11bd81a89a6c6879695a2ba4b4'
PRESET = dict(tol=1e-5, max_iter=40, backtrack=True, backend='superlu')
torch.set_num_threads(4)

def case_for(scenario, exact=False, supported_roles=True):
    d = PRIOR/'results'/scenario
    original = read(d/'input.json')
    graph = load_pyg_json(d/'newer-base-v2-input.pyg.json')
    c = closure.extract_case(graph)
    mapping = read(d/'newer-base-v2-input.pyg.json')['metadata']
    ids,b,e,f,t = matrices(original)
    g = np.asarray(original['gen'],float)
    gm = g.copy(); gm[:,0] = [ids[int(v)] for v in g[:,0]]
    old_ref = c.ref.copy()
    if supported_roles:
        c.ref,c.pv,c.pq = bustypes(b,gm)
        c.pvpq = np.sort(np.r_[c.pv,c.pq])
        c.ctrl_bus = np.sort(np.r_[c.ref,c.pv])
    if exact:
        active = e[:,10]>0
        ee=e[active]; c.f=f[active]; c.t=t[active]
        c.y=1/(ee[:,2]+1j*ee[:,3]); c.b_fr=ee[:,4]/2; c.b_to=ee[:,4]/2
        c.tap=np.where(ee[:,8]==0,1,ee[:,8])*np.exp(1j*np.deg2rad(ee[:,9]))
        c.ysh=(b[:,4]+1j*b[:,5])/original['baseMVA']
        c.Pd=b[:,2]/original['baseMVA']; c.Qd=b[:,3]/original['baseMVA']
        c.Ybus=closure.build_ybus(c)
        Y,_,_=makeYbus(original['baseMVA'],b,e)
        assert abs((Y-c.Ybus).toarray()).max()<1e-10
    meta={'original_reference_buses':[int(original['bus'][i][0]) for i in old_ref],
          'completion_balancing_buses':[int(original['bus'][i][0]) for i in c.ref],
          'reference_role_changed':not np.array_equal(c.ref,old_ref),
          'role_policy':'MATPOWER/PYPOWER bustypes first eligible PV fallback' if supported_roles else 'UNMAPPED author extraction diagnostic',
          'physics':'original FP64 matrices' if exact else 'released graph float32 + PI_Z2_EPS=1e-12',
          'gen_source_rows':mapping['gen_source_rows'],
          'input_sha256':hashlib.sha256((d/'input.json').read_bytes()).hexdigest(),
          'graph_sha256':hashlib.sha256((d/'newer-base-v2-input.pyg.json').read_bytes()).hexdigest()}
    return original,c,meta

def complete(scenario, controls, exact=False, supported_roles=True, tol=None):
    original,c,meta=case_for(scenario,exact,supported_roles)
    base=original['baseMVA']; grows=np.asarray(meta['gen_source_rows'],int)
    pg=np.asarray(controls['pg_mw'])[grows]/base
    vm=np.asarray(controls['vm'],float)
    V0=closure.dc_init_V(c,pg,vm)
    # Same forward initialization as ACPFClosure.forward and _forward_worker.
    mag=abs(V0); mag[c.ctrl_bus]=vm[c.ctrl_bus]; V0=mag*np.exp(1j*np.angle(V0))
    preset={**PRESET,**({'tol':tol} if tol is not None else {})}
    result=closure.newton_pf(c,closure.build_Ssp(c,pg),V0,**preset)
    meta.update(source_commit=PIN,preset=preset,tolerance_MW_MVAr=preset['tol']*base,
                converged=bool(result.converged),iterations=result.iters,norm_history_pu=result.norm_hist,
                failure_reason=None if result.converged else ('nonfinite iterate' if not np.isfinite(result.V).all() else 'iteration cap or singular Jacobian'),
                initialization='cold author dc_init_V, predicted full Vm; no AC labels or cross-scenario cache',
                initial_vm=abs(V0).tolist(),initial_va_deg=np.rad2deg(np.angle(V0)).tolist(),
                Q_limit_switching=False,post_completion_clipping=False)
    if not np.isfinite(result.V).all():return None,meta
    inj=result.V*np.conj(c.Ybus@result.V)
    total=inj+(c.Pd+1j*c.Qd)
    Pg=np.asarray(controls['pg_mw'],float).copy(); Qg=np.zeros(len(original['gen']))
    g=np.asarray(original['gen']); on=g[:,7]>0; Pg[~on]=0
    ids={int(b[0]):i for i,b in enumerate(original['bus'])}
    alloc=[]; missing=[]
    for bus in c.ctrl_bus:
        original_rows=np.array([i for i,z in enumerate(g) if on[i] and ids[int(z[0])]==bus],int)
        if not len(original_rows):
            missing.append({'bus_id':int(original['bus'][bus][0]),'unallocated_P_MW':float(total[bus].real*base),'unallocated_Q_MVAr':float(total[bus].imag*base)})
            continue
        qmin=g[original_rows,4]; qrange=g[original_rows,3]-qmin
        qtotal=total[bus].imag*base
        if qrange.sum()>0:Qg[original_rows]=qmin+qrange/qrange.sum()*(qtotal-qmin.sum())
        else:Qg[original_rows]=qtotal/len(original_rows)
        if bus in c.ref:
            Pg[original_rows[0]]=total[bus].real*base-Pg[original_rows[1:]].sum()
        alloc.append({'bus_id':int(original['bus'][bus][0]),'generator_rows_1based':(original_rows+1).tolist(),
                      'recovered_bus_Q_MVAr':float(qtotal),'Qmin_sum':float(qmin.sum()),'Qmax_sum':float(g[original_rows,3].sum()),
                      'is_balancing_bus':bool(bus in c.ref)})
    angle=np.rad2deg(np.angle(result.V)); original_ref=np.flatnonzero(np.array(original['bus'])[:,1]==3)[0]
    angle=angle-angle[original_ref]
    state=dict(vm=abs(result.V).tolist(),va_deg=angle.tolist(),pg_mw=Pg.tolist(),qg_mvar=Qg.tolist())
    slack_rows=np.array([i for i,z in enumerate(g) if on[i] and ids[int(z[0])] in c.ref],int)
    fixed=np.ones(len(g),bool);fixed[slack_rows]=False
    meta.update(allocation=alloc,unallocated_injections=missing,
                maximum_fixed_Pg_change_MW=float(abs(Pg[fixed]-np.asarray(controls['pg_mw'])[fixed]).max()),
                maximum_fixed_voltage_change_pu=float(abs(abs(result.V)[c.ctrl_bus]-vm[c.ctrl_bus]).max()),
                recovered_injection_P_MW=(total.real*base).tolist(),recovered_injection_Q_MVAr=(total.imag*base).tolist(),
                finite_returned=True,physically_supported_mapping=not missing)
    assert meta['maximum_fixed_Pg_change_MW']<1e-9
    assert meta['maximum_fixed_voltage_change_pu']<1e-12
    return state,meta

def score_and_save(folder,scenario,controls,method,exact=False,supported_roles=True,tol=None):
    folder.mkdir(parents=True,exist_ok=True)
    assert not (folder/'status.json').exists(),'Refusing overwrite'
    c=read(PRIOR/'results'/scenario/'input.json')
    refpath=PRIOR/'results'/scenario/'ac-native.json'
    ref=read(refpath) if refpath.exists() else None
    state,meta=complete(scenario,controls,exact,supported_roles,tol)
    meta.update(method=method,scenario=scenario,adapter_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest())
    if state is not None:
        save(folder/'state.json',state)
        metric,bus,gen,branch=evaluate(c,state,method,ref)
        from electrical import csvsave
        for name,rows in [('bus',bus),('generator',gen),('branch',branch)]:csvsave(folder/(name+'.csv'),rows)
        metric.update(scenario=scenario,PF_converged=meta['converged'],mapping_supported=meta['physically_supported_mapping'],
                      successful_AC_operating_point=bool(metric['AC_joint_pass'] and meta['converged'] and meta['physically_supported_mapping']))
        save(folder/'metrics.json',metric)
    save(folder/'status.json',meta)
    return state,meta
