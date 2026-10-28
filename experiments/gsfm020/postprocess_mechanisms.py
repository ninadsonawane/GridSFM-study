"""Postprocess completed saved batches only. No model, OPF, PF or repair calls.

Adds explicit constraint locations, actual clamp versus bound activity, local
signed budgets, concentration, and symmetric algebraic error-change attribution.
Only complete batches are included; historical CSV overlays remain labelled.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import pathlib
import sys

import numpy as np
from electrical import branch_flows, csvsave, evaluate, identity, score, terms
from prepare import O, R, read, save, sha

RELEASES = ['microsoft-v1.1', 'newer-base-v2']
FOCUS = {235, 238, 137, 231}
TOL = {'P': 1e-3, 'Q': 1e-3, 'Pg': 1e-3, 'Qg': 1e-3,
       'Vm': 1e-4, 'angle': 1e-3, 'thermal': 1e-3}


def csvread(path):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        return list(csv.DictReader(stream))


def angle_active(branch):
    lo, hi = branch[11:13]
    return ((lo != 0 and lo > -360) or (hi != 0 and hi < 360)
            or (lo != 0 and hi == 0) or (lo == 0 and hi != 0))


def location(c, row):
    area, original = identity(c, row)
    return {'bus_id': int(c['bus'][row][0]), 'area': area, 'original_bus_id': original}


def constraint_rows(c, s, method, sm, buses, branches):
    """One row per violating physical constraint component; counts match score."""
    rows = []
    ids = {int(b[0]): i for i, b in enumerate(c['bus'])}
    for bus in buses:
        for quantity, key in [('P', 'P_residual_MW'), ('Q', 'Q_residual_MVAr')]:
            val = bus[key]
            if val is not None and abs(val) > TOL[quantity]:
                rows.append({'quantity': quantity, 'entity': 'bus', 'row_1based': ids[bus['bus_id']]+1,
                             **location(c, ids[bus['bus_id']]), 'value': val, 'excess': abs(val),
                             'tolerance': TOL[quantity], 'side': 'positive' if val > 0 else 'negative'})
    for quantity, key, lower, upper in [('Pg', 'pg_mw', 9, 8), ('Qg', 'qg_mvar', 4, 3)]:
        if s.get(key) is None:
            continue
        for j, (val, gen) in enumerate(zip(s[key], c['gen'])):
            online = gen[7] > 0
            excess = max(gen[lower]-val, val-gen[upper], 0) if online else abs(val)
            if excess > TOL[quantity]:
                rows.append({'quantity': quantity, 'entity': 'generator', 'row_1based': j+1,
                             **location(c, ids[int(gen[0])]), 'value': val, 'lower': gen[lower],
                             'upper': gen[upper], 'online': online, 'excess': excess,
                             'tolerance': TOL[quantity],
                             'side': ('lower' if val < gen[lower] else 'upper') if online else 'offline_nonzero'})
    if s.get('vm') is not None:
        for j, (val, bus) in enumerate(zip(s['vm'], c['bus'])):
            excess = max(bus[12]-val, val-bus[11], 0)
            if excess > TOL['Vm']:
                rows.append({'quantity': 'Vm', 'entity': 'bus', 'row_1based': j+1,
                             **location(c, j), 'value': val, 'lower': bus[12], 'upper': bus[11],
                             'excess': excess, 'tolerance': TOL['Vm'], 'side': 'lower' if val < bus[12] else 'upper'})
    for j, (branch, flow) in enumerate(zip(c['branch'], branches)):
        if branch[10] <= 0:
            continue
        f, t = ids[int(branch[0])], ids[int(branch[1])]
        common = {'entity': 'branch', 'row_1based': j+1, 'from_bus': int(branch[0]),
                  'to_bus': int(branch[1]), 'from_area': identity(c, f)[0], 'to_area': identity(c, t)[0]}
        if angle_active(branch):
            value = s['va_deg'][f]-s['va_deg'][t]
            lo, hi = branch[11:13]
            excess = max(0, lo-value if lo >= -360 else 0, value-hi if hi <= 360 else 0)
            if excess > TOL['angle']:
                rows.append({**common, 'quantity': 'angle', 'value': value, 'lower': lo, 'upper': hi,
                             'excess': excess, 'tolerance': TOL['angle'], 'side': 'lower' if value < lo else 'upper'})
        if branch[5] > 0 and flow['thermal_excess'] > TOL['thermal']:
            rows.append({**common, 'quantity': 'thermal', 'value': flow['loading_ratio']*branch[5],
                         'upper': branch[5], 'excess': flow['thermal_excess'],
                         'tolerance': TOL['thermal'], 'side': flow['controlling_end'],
                         'unit': 'MW' if method == 'DC-OPF' else 'MVA'})
    keys = {'P': 'P_violating_buses', 'Q': 'Q_violating_buses', 'Pg': 'Pg_violating_count',
            'Qg': 'Qg_violating_count', 'Vm': 'Vm_violating_count', 'angle': 'angle_violating_count',
            'thermal': 'thermal_violating_count'}
    for quantity, key in keys.items():
        if sm[key] is not None:
            assert sum(r['quantity'] == quantity for r in rows) == sm[key], (method, quantity)
    return [dict(method=method, **row) for row in rows]


def clamp_rows(c, path, method):
    rows = []
    for cap in read(path)['captures']:
        variable = 'Vm' if cap['variable'] == 'V' else cap['variable']
        scale = 1 if variable == 'Vm' else c['baseMVA']
        source = list(enumerate(c['bus'])) if variable == 'Vm' else [(j,g) for j,g in enumerate(c['gen']) if g[7] > 0]
        a, z, lo, hi = (np.asarray(cap[k], float) for k in ['input','output','lo','hi'])
        assert len(source) == len(a)
        assert np.array_equal(np.clip(a, lo, hi), z)
        for k, (j, entity) in enumerate(source):
            lower, upper = (entity[12], entity[11]) if variable == 'Vm' else ((entity[9], entity[8]) if variable == 'Pg' else (entity[4], entity[3]))
            actual = bool(a[k] != z[k])
            rows.append({'method': method, 'variable': variable, 'row_1based': j+1,
                         'bus_id': int(entity[0]), 'input': a[k]*scale, 'output': z[k]*scale,
                         'shipped_lower': lo[k]*scale, 'shipped_upper': hi[k]*scale,
                         'physical_lower': lower, 'physical_upper': upper,
                         'actual_clipping': actual, 'material_clipping': abs(a[k]-z[k])*scale > TOL[variable],
                         'clipping_magnitude': abs(a[k]-z[k])*scale,
                         'exactly_at_shipped_lower': bool(z[k] == lo[k]), 'exactly_at_shipped_upper': bool(z[k] == hi[k]),
                         'near_physical_lower': abs(z[k]*scale-lower) <= TOL[variable],
                         'near_physical_upper': abs(z[k]*scale-upper) <= TOL[variable],
                         'at_shipped_bound_without_actual_clipping': bool((z[k] == lo[k] or z[k] == hi[k]) and not actual)})
    return rows


def local_budgets(c, s, method, buses, branches, clamps):
    focus, ranked, concentration, cancellation = [], [], [], []
    cm = {(r['variable'], r['row_1based']): r for r in clamps}
    for quantity, key in [('P','P_residual_MW'), ('Q','Q_residual_MVAr')]:
        if quantity == 'Q' and method == 'DC-OPF':
            continue
        vals = np.array([b[key] for b in buses])
        order = np.argsort(-np.abs(vals), kind='stable')
        total = float(abs(vals).sum())
        for rank, idx in enumerate(order[:10], 1):
            ranked.append({'method': method, 'quantity': quantity, 'rank': rank,
                           **location(c, int(idx)), 'signed_residual': vals[idx], 'absolute_residual': abs(vals[idx]),
                           'fraction_total_absolute': None if total == 0 else abs(vals[idx])/total})
        concentration.append({'method': method, 'quantity': quantity, 'total_absolute': total,
                              'signed_sum': float(vals.sum()), 'global_cancellation_fraction': None if total == 0 else 1-abs(float(vals.sum()))/total,
                              **{f'top{k}_absolute_fraction': None if total == 0 else float(abs(vals[order[:k]]).sum())/total for k in [1,3,5,10]}})
    if method == 'DC-OPF':
        return focus, ranked, concentration, cancellation
    ids = {int(b[0]): i for i,b in enumerate(c['bus'])}
    for i, bus in enumerate(buses):
        for quantity in ['P','Q']:
            suffix = 'MW' if quantity == 'P' else 'MVAr'
            components = {'generation': bus[f'{quantity}g_bus_{suffix}'], 'negative_demand': -bus[f'{quantity}d_{suffix}'],
                          'negative_branch_outgoing': -bus[f'branch_{quantity}_out_{suffix}'],
                          'negative_shunt_consumption': -bus[f'bus_shunt_{quantity}_{suffix}']}
            residual = bus[f'{quantity}_residual_{suffix}']
            assert abs(sum(components.values())-residual) < 1e-6
            positive = sum(max(x,0) for x in components.values())
            negative = sum(min(x,0) for x in components.values())
            denom = positive-negative
            cancellation.append({'method': method, 'quantity': quantity, **location(c,i), **components,
                                 'signed_residual': residual, 'absolute_residual': abs(residual),
                                 'positive_terms_sum': positive, 'negative_terms_sum': negative,
                                 'cancellation_fraction': None if denom == 0 else 1-abs(residual)/denom})
        if bus['original_bus_id'] in FOCUS:
            row = dict(bus)
            clamp = cm.get(('Vm', i+1))
            if clamp:
                row.update({k: clamp[k] for k in ['input','output','actual_clipping','material_clipping','exactly_at_shipped_lower','exactly_at_shipped_upper']})
            focus.append(row)
    return focus, ranked, concentration, cancellation


def motion_arrays(c, s, generator_mask=None):
    slack = next(i for i,b in enumerate(c['bus']) if b[1] == 3)
    angle = np.asarray(s['va_deg'])-s['va_deg'][slack]
    angle = (angle+180)%360-180
    active = np.array([g[7] > 0 for g in c['gen']]) if generator_mask is None else generator_mask
    if s.get('vm') is None:
        return {'Pg': np.asarray(s['pg_mw'])[active], 'angle': angle,
                'Pflow': np.r_[s['pf_mw'], s['pt_mw']]}
    sf,st = map(np.asarray,branch_flows(c,s['vm'],s['va_deg']))
    return {'Pg': np.asarray(s['pg_mw'])[active], 'Qg': np.asarray(s['qg_mvar'])[active],
            'Vm': np.asarray(s['vm']), 'angle': angle, 'Pflow': np.r_[sf.real,st.real]}


def pair_analysis(before, after, method):
    """Symmetric algebraic split; descriptive counterfactual arithmetic, not causality."""
    c0,c1 = before['case'],after['case']
    assert [b[0] for b in c0['bus']] == [b[0] for b in c1['bus']]
    assert [g[0] for g in c0['gen']] == [g[0] for g in c1['gen']]
    s0,s1 = before['states'][method],after['states'][method]
    common_online=np.array([g0[7] > 0 and g1[7] > 0 for g0,g1 in zip(c0['gen'],c1['gen'])])
    a0,a1 = motion_arrays(c0,s0,common_online),motion_arrays(c1,s1,common_online)
    rows=[];budgets=[];severity=[]
    refs = before['ref'] is not None and after['ref'] is not None
    r0 = motion_arrays(c0,before['ref'],common_online) if refs else {}
    r1 = motion_arrays(c1,after['ref'],common_online) if refs else {}
    for variable in a0:
        if len(a0[variable]) != len(a1[variable]) or not len(a0[variable]):
            continue
        x0,x1=a0[variable],a1[variable]
        diff = lambda x,y: (x-y+180)%360-180 if variable == 'angle' else x-y
        row={'method':method,'variable':variable,'compared_components':len(x0),'native_motion_mean_abs':float(abs(diff(x1,x0)).mean()),
             'native_motion_max_abs':float(abs(diff(x1,x0)).max()),'accepted_references_both':refs}
        if refs:
            y0,y1=r0[variable],r1[variable]
            e00,e10,e01,e11=(abs(diff(x,y)) for x,y in [(x0,y0),(x1,y0),(x0,y1),(x1,y1)])
            native=0.5*((e10-e00)+(e11-e01));reference=0.5*((e01-e00)+(e11-e10))
            assert np.max(abs(native+reference-(e11-e00)))<1e-8
            row.update(error_mean_before=float(e00.mean()),error_mean_after=float(e11.mean()),
                       error_mean_change=float((e11-e00).mean()),native_algebraic_contribution=float(native.mean()),
                       reference_algebraic_contribution=float(reference.mean()),reference_motion_mean_abs=float(abs(diff(y1,y0)).mean()),
                       reference_motion_max_abs=float(abs(diff(y1,y0)).max()))
        rows.append(row)
    if method != 'DC-OPF':
        t0,t1=terms(c0,s0),terms(c1,s1)
        for quantity,part in [('P','real'),('Q','imag')]:
            q0=getattr(t0['r'],part);q1=getattr(t1['r'],part)
            change=abs(q1)-abs(q0)
            hotspot=np.array([identity(c0,i)[1] in {235,238} for i in range(len(c0['bus']))])
            severity.append({'method':method,'quantity':quantity,'total_absolute_before':float(abs(q0).sum()),
                             'total_absolute_after':float(abs(q1).sum()),'total_absolute_change':float(change.sum()),
                             'worst_before':float(abs(q0).max()),'worst_after':float(abs(q1).max()),
                             'p95_before':float(np.percentile(abs(q0),95)),'p95_after':float(np.percentile(abs(q1),95)),
                             'buses_severity_increased':int((change>0).sum()),'buses_severity_decreased':int((change<0).sum()),
                             'buses_increased_over_1e_minus6':int((change>1e-6).sum()),
                             'buses_decreased_over_1e_minus6':int((change< -1e-6).sum()),
                             'sum_increases':float(np.maximum(change,0).sum()),'sum_decreases':float(np.minimum(change,0).sum()),
                             'original235_238_bus_count':int(hotspot.sum()),'other_bus_count':int((~hotspot).sum()),
                             'original235_238_total_change':float(change[hotspot].sum()),
                             'original235_238_buses_increased':int((change[hotspot]>1e-6).sum()),
                             'original235_238_buses_decreased':int((change[hotspot]<-1e-6).sum()),
                             'other_buses_increased':int((change[~hotspot]>1e-6).sum()),
                             'other_buses_decreased':int((change[~hotspot]<-1e-6).sum()),
                             'other_buses_total_absolute_before':float(abs(q0[~hotspot]).sum()),
                             'other_buses_total_absolute_after':float(abs(q1[~hotspot]).sum()),
                             'other_buses_total_change':float(change[~hotspot].sum())})
            for i in range(len(c0['bus'])):
                components={key:float(getattr(t1[key]-t0[key],part)[i])*sign for key,sign in [('gen',1),('demand',-1),('out',-1),('shunt',-1)]}
                assert abs(sum(components.values())-(q1[i]-q0[i]))<1e-6
                budgets.append({'method':method,'quantity':quantity,**location(c0,i),'before_signed':q0[i],'after_signed':q1[i],
                                'absolute_severity_change':change[i],'signed_residual_change':q1[i]-q0[i],
                                'generation_change':components['gen'],'negative_demand_change':components['demand'],
                                'negative_branch_outgoing_change':components['out'],'negative_shunt_consumption_change':components['shunt']})
    return rows,budgets,severity


def dc_equality(before, after):
    """Read-only exact comparisons; a Q-only control changes no other matrix field."""
    c0,c1=before['case'],after['case']
    if len(c0['bus']) != len(c1['bus']):
        return None
    matrix_differences={}
    for name in ['bus','gen','branch','gencost']:
        x,y=np.asarray(c0[name]),np.asarray(c1[name])
        if name=='bus':
            x=np.delete(x,3,axis=1);y=np.delete(y,3,axis=1)
        if x.shape!=y.shape:
            matrix_differences[name]={'same_shape':False,'exact_equal':False}
        else:
            matrix_differences[name]={'same_shape':True,'exact_equal':bool(np.array_equal(x,y)),
                                      'max_abs_difference':float(abs(x-y).max()),'different_entries':int((x!=y).sum())}
    a,b=before['states'].get('DC-OPF'),after['states'].get('DC-OPF')
    if a is None or b is None:
        return None
    arrays={}
    for key in ['pg_mw','va_deg','pf_mw','pt_mw']:
        x,y=np.asarray(a[key]),np.asarray(b[key])
        arrays[key]={'exact_equal':bool(np.array_equal(x,y)),'max_abs_difference':float(abs(x-y).max()),
                     'different_entries':int((x!=y).sum())}
    return {'original_input_matrices_identical_except_bus_Qd':all(v['exact_equal'] for v in matrix_differences.values()) and c0['baseMVA']==c1['baseMVA'],
            'matrix_comparison_Qd_omitted':matrix_differences,'native_arrays':arrays,
            'all_four_native_arrays_exact_equal':all(v['exact_equal'] for v in arrays.values())}


def reactive_response(before, after, method):
    a,b=before['states'][method],after['states'][method]
    if a.get('qg_mvar') is None:
        return None
    row={'method':method,'total_Qd_before':sum(x[3] for x in before['case']['bus']),
         'total_Qd_after':sum(x[3] for x in after['case']['bus']),
         'native_total_Qg_before':sum(a['qg_mvar']),'native_total_Qg_after':sum(b['qg_mvar']),
         'native_total_Qg_change':sum(b['qg_mvar'])-sum(a['qg_mvar'])}
    if before['ref'] is not None and after['ref'] is not None:
        row.update(reference_total_Qg_before=sum(before['ref']['qg_mvar']),reference_total_Qg_after=sum(after['ref']['qg_mvar']))
        row['reference_total_Qg_change']=row['reference_total_Qg_after']-row['reference_total_Qg_before']
    if method in RELEASES:
        sets=[]
        for rec in [before,after]:
            cap=next(x for x in read(rec['clamp_paths'][method])['captures'] if x['variable']=='Qg')
            online=[j for j,g in enumerate(rec['case']['gen']) if g[7]>0]
            sets.append({j for k,j in enumerate(online) if cap['input'][k]!=cap['output'][k]})
        common=sets[0]&sets[1]
        row.update(actual_Qg_clipped_count_before=len(sets[0]),actual_Qg_clipped_count_after=len(sets[1]),
                   actual_Qg_clipped_rows_identical=sets[0]==sets[1],
                   Qg_change_on_rows_clipped_both_times=sum(b['qg_mvar'][j]-a['qg_mvar'][j] for j in common))
    return row


def branch_q_decomposition(case, state, j=320):
    """Exact to-end Q identity; algebraic terms, not a model-input ablation."""
    branch=case['branch'][j];ids={int(b[0]):i for i,b in enumerate(case['bus'])}
    f,t=ids[int(branch[0])],ids[int(branch[1])]
    vf,vt=state['vm'][f],state['vm'][t];tau=branch[8] or 1.
    delta=np.deg2rad(state['va_deg'][t]-state['va_deg'][f]+branch[9])
    y=branch[10]/complex(branch[2],branch[3]);g,b=y.real,-y.imag;base=case['baseMVA']
    row={'branch_row_1based':j+1,'from_bus':int(branch[0]),'to_bus':int(branch[1]),
         'series_r_pu':branch[2],'series_x_pu':branch[3],'total_charging_b_pu':branch[4],
         'Vm_from':vf,'Vm_to':vt,'tap_magnitude':tau,'effective_to_minus_from_angle_deg':float(np.rad2deg(delta)),
         'Qt_voltage_gap_MVAr':base*b*vt*(vt-vf/tau),
         'Qt_cosine_angle_MVAr':base*b*vt*vf/tau*(1-np.cos(delta)),
         'Qt_sine_angle_MVAr':-base*g*vt*vf/tau*np.sin(delta),
         'Qt_charging_MVAr':-base*branch[10]*branch[4]/2*vt**2}
    row['Qt_components_sum_MVAr']=sum(row[k] for k in ['Qt_voltage_gap_MVAr','Qt_cosine_angle_MVAr','Qt_sine_angle_MVAr','Qt_charging_MVAr'])
    row['Qt_direct_MVAr']=float(np.imag(branch_flows(case,state['vm'],state['va_deg'])[1][j]))
    assert abs(row['Qt_components_sum_MVAr']-row['Qt_direct_MVAr'])<1e-6
    return row


def replay_baseline(root, sources):
    """Use existing diagnostic forwards and independently revalidated historical AC."""
    casepath=root/'bases/300/input.json';refpath=root/'recovered-base/AC-reference-DERIVED-state.json'
    if not refpath.exists():
        return None
    case=read(casepath);ref=read(refpath)['state']
    assert evaluate(case,ref)['all_tested_constraints_pass'];terms(case,ref)
    states={'AC-OPF':ref};clamp_paths={}
    paths=[casepath,refpath]
    for rel in RELEASES:
        folder=root/'diagnostic'/rel/'baseline-cold'
        native=folder/(rel+'-native.json');clamp=folder/(rel+'-clamps.json')
        assert native.exists() and clamp.exists()
        assert sha(folder/'input.json')==sha(casepath)
        states[rel]=read(native);clamp_paths[rel]=clamp;paths.extend([native,clamp])
    for path in paths:
        sources[str(path.relative_to(R))]=sha(path)
    return {'case':case,'states':states,'ref':ref,'spec':{'network':300,'load_scale':1.},
            'clamp_paths':clamp_paths,'evidence':'LOCAL_DIAGNOSTIC_MODEL_FORWARD_WITH_VERIFIED_HISTORICAL_DERIVED_AC_REFERENCE'}


def confirmation_checks(records, paired_severity, motion):
    """Evaluate the frozen claim tests from saved states, retaining counterevidence."""
    names=['CONF-P0935-Q093','CONF-P093-Q0935','CONF-LOC-plus075',
           'CONF-LOC-plus125','CONF-A600-plus040','CONF-A600-minus040']
    missing=[x for x in names if x not in records]
    if missing:
        return {'status':'WAITING_FOR_COMPLETE_CONFIRMATION_BATCH','pending':missing}
    cache={}
    def metrics(name,method):
        if (name,method) not in cache:
            rec=records[name]
            cache[name,method]=score(rec['case'],rec['states'][method],method,rec['ref'])
        return cache[name,method]
    def voltage(name,method,bid):
        rec=records[name];i=next(j for j,b in enumerate(rec['case']['bus']) if int(b[0])==bid)
        row={'Vm_pu':rec['states'][method]['vm'][i]}
        if method in RELEASES:
            cap=next(c for c in read(rec['clamp_paths'][method])['captures'] if c['variable']=='V')
            row.update(preclip_Vm_pu=cap['input'][i],actual_clipping=cap['input'][i]!=cap['output'][i],
                       at_lower=cap['output'][i]==cap['lo'][i],at_upper=cap['output'][i]==cap['hi'][i])
        return row
    def case_view(name,method):
        summary,buses,branches,_=metrics(name,method)
        row={'AC_reference_accepted':records[name]['ref'] is not None,
             'Q_mean_MVAr':summary['Q']['mean'],'Q_p95_MVAr':summary['Q']['p95'],
             'Q_max_MVAr':summary['Q']['max'],'Q_violating_buses':summary['Q_violating_buses'],
             'P_violating_buses':summary['P_violating_buses'],'native_joint_AC_feasible':summary['AC_joint_feasible'],
             'Vm235':voltage(name,method,235),'Vm238':voltage(name,method,238),
             'branch321_Qt_MVAr':branches[320]['Qt_MVAr'],
             'branch321_Qt_algebra':branch_q_decomposition(records[name]['case'],records[name]['states'][method])}
        if summary['approximation'] is not None:
            row['MAE']={key:val['mean'] for key,val in summary['approximation'].items() if val is not None and key in
                        ['Pg_per_generator_MW','Qg_per_generator_MVAr','Vm_pu','aligned_angle_deg','branch_P_MW']}
        return row
    component={}
    base='G300-0.93';p='CONF-P0935-Q093';q='CONF-P093-Q0935'
    for method in RELEASES:
        component[method]={
            'P_only':{'scenario':p,'operating_point':case_view(p,method),
                      'reactive_response':reactive_response(records[base],records[p],method)},
            'Q_only':{'scenario':q,'operating_point':case_view(q,method),
                      'reactive_response':reactive_response(records[base],records[q],method)}}
    vbase=voltage(base,'newer-base-v2',235);vp=voltage(p,'newer-base-v2',235);vq=voltage(q,'newer-base-v2',235)
    component_tests={
        'v2_baseline_lower_clipped':vbase['actual_clipping'] and vbase['at_lower'],
        'v2_P_only_leaves_lower_clamp':not vp['at_lower'],
        'v2_Q_only_stays_lower_clipped':vq['actual_clipping'] and vq['at_lower'],
        'Q_only_DC_four_saved_arrays_exactly_equal':dc_equality(records[base],records[q])['all_four_native_arrays_exact_equal'],
        'P_only_DC_equals_same_P_global_case':dc_equality(records['G300-0.935'],records[p])['all_four_native_arrays_exact_equal']}
    for method in RELEASES:
        rr=component[method]['Q_only']['reactive_response']
        component_tests[method+'_Q_only_AC_Qg_rises_native_Qg_falls']=(rr.get('reference_total_Qg_change',float('nan'))>0 and rr['native_total_Qg_change']<0)
        component_tests[method+'_Q_only_same_Qg_clipped_rows_zero_clipped_row_change']=(rr['actual_Qg_clipped_rows_identical'] and rr['Qg_change_on_rows_clipped_both_times']==0)
    local_names=['LOC-plus050','CONF-LOC-plus075','CONF-LOC-plus125','LOC-plus150']
    local={name:{method:case_view(name,method) for method in RELEASES+['AC-OPF']} for name in local_names}
    local_inputs={}
    baseline=np.asarray(records['G300-1.00-REPLAY']['case']['bus'])
    for name in local_names:
        bus=np.asarray(records[name]['case']['bus']);hot=np.isin(bus[:,0],[235,238])
        local_inputs[name]={'total_P_MW':float(bus[:,2].sum()),'total_Q_MVAr':float(bus[:,3].sum()),
                            'P_total_change_MW':float(bus[:,2].sum()-baseline[:,2].sum()),
                            'Q_total_change_MVAr':float(bus[:,3].sum()-baseline[:,3].sum()),
                            '235_238_PQ_unchanged_exactly':bool(np.array_equal(bus[hot,2:4],baseline[hot,2:4]))}
    local_pairs=[r for r in paired_severity if r['before'] in local_names and r['after'] in local_names and r['quantity']=='Q']
    local_motion=[r for r in motion if r['before'] in local_names and r['after'] in local_names and r['method']=='newer-base-v2']
    area={}
    for name in ['A600-plus025','CONF-A600-plus040','A600-plus075','A600-minus025','CONF-A600-minus040','A600-minus075']:
        accepted=records[name]['ref'] is not None
        area[name]={'AC_reference':'AC_ACCEPTED' if accepted else 'UNKNOWN','methods':{}}
        for method in RELEASES+['DC-OPF','AC-OPF']:
            if method=='AC-OPF' and not accepted:
                continue
            sm,_,branches,_=metrics(name,method)
            ties=[r for r in branches if r['is_tie'] and r['rateA'] is not None]
            assert len(ties)==sm['rated_online_branch_count']==2
            first=ties[0]
            area[name]['methods'][method]={'finite_rated_tie_rows':[r['branch_row_1based'] for r in ties],
                'rating':first['rateA'],'unit':'MW' if method=='DC-OPF' else 'MVA',
                'max_loading':max(r['loading_ratio']*r['rateA'] for r in ties),
                'max_excess':sm['thermal_max_excess_MVA_or_DC_MW'],'violating_count':sm['thermal_violating_count'],
                'first_tie_Pf_MW':first['Pf_MW'],'first_tie_Pt_MW':first['Pt_MW'],
                'first_tie_Qf_MVAr':first['Qf_MVAr'],'first_tie_Qt_MVAr':first['Qt_MVAr'],
                'both_parallel_ties_identical':all(ties[0][k]==ties[1][k] for k in ['Pf_MW','Pt_MW','Qf_MVAr','Qt_MVAr']),
                'native_joint_AC_feasible':sm['AC_joint_feasible'],'native_DC_constraints_pass':sm['native_DC_constraints_pass']}
    feasibility=[]
    for name,rec in records.items():
        if rec['evidence']!='FRESH_FOUR_METHOD_CASE':
            continue
        for method in RELEASES:
            sm=metrics(name,method)[0]
            feasibility.append({'scenario':name,'method':method,'native_joint_AC_feasible':sm['AC_joint_feasible']})
    confirmation_status={name:{'AC_reference_accepted':records[name]['ref'] is not None,
                              'DC_own_equations_pass':metrics(name,'DC-OPF')[0]['native_DC_constraints_pass']} for name in names}
    confirmation_local=[local[name]['newer-base-v2'] for name in ['CONF-LOC-plus075','CONF-LOC-plus125']]
    local_counter=[]
    if not all(row['Q_max_MVAr']>local['LOC-plus050']['newer-base-v2']['Q_max_MVAr'] for row in confirmation_local):
        local_counter.append('At least one intermediate positive location point does not exceed discovery strength0.5 Qmax; do not claim a monotone threshold.')
    if not all(row['Vm235']['at_lower'] for row in confirmation_local):
        local_counter.append('At least one intermediate positive location point is not lower-clamped at Vm235; the tested points bracket a change, not its exact threshold.')
    native_confirmations={name:{method:area[name]['methods'][method]['violating_count'] for method in RELEASES}
                          for name in ['CONF-A600-plus040','CONF-A600-minus040']}
    return {'status':'COMPLETE','scope':'Saved-state scoring only; no inference, solve, repair or threshold change.',
            'confirmation_status':confirmation_status,
            'component_test':{'frozen_expectation':'P-only releases v2 Vm235 lower clamp; Q-only retains it, verified ACQg rises, both nativeQg fall, Qg clipping membership unchanged.',
                              'baseline':base,'baseline_v2_Vm235':vbase,'claim_checks':component_tests,
                              'counterevidence':[key for key,value in component_tests.items() if not value],
                              'observations':component},
            'fixed_total_location_test':{'frozen_expectation':'Quantify onset or sustained nonlocal voltage and imbalance degradation at strength0.75/1.25; no universal monotonic response assumed.',
                'input_checks':local_inputs,'observations':local,'paired_absolute_Q_severity_MVAr':local_pairs,
                'v2_symmetric_error_change_attribution':local_motion,'counterevidence_or_limits':local_counter,
                'attribution_note':'Native/reference error split is symmetric algebra, not identified model causality. Hotspot235/238 totals and all other298 buses are retained separately.'},
            'existing600_tie_test':{'frozen_expectation':'Preserve signed strength0.04 finite-rating result and ACaccepted/UNKNOWN classification; no inference of system infeasibility.',
                'observations':area,'confirmation_native_tie_violating_counts':native_confirmations,
                'counterevidence_or_limits':['Thermal direction or magnitude alone is not a new physical law. Failed AC references atstrength0.075 remainUNKNOWN.',
                                            'DC active-power rating and AC apparent-power rating test different equations; DC success does not establish AC feasibility.']},
            'native_feasibility':{'new_operating_points':len(feasibility),'feasible_count':sum(r['native_joint_AC_feasible'] for r in feasibility),
                                  'feasible_points':[r for r in feasibility if r['native_joint_AC_feasible']]}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=pathlib.Path,default=O)
    parser.add_argument('--out',type=pathlib.Path)
    parser.add_argument('--pair',action='append',default=[],metavar='BEFORE:AFTER',help='Additional explicit pair of saved completed scenarios.')
    parser.add_argument('--pair-config',type=pathlib.Path,default=pathlib.Path(__file__).with_name('mechanism-pairs.json'))
    args=parser.parse_args()
    root=args.root.resolve();out=(args.out or root/'mechanisms').resolve()
    batches=[];records={};sources={};all_constraints=[];all_clamps=[];all_focus=[];all_ranked=[];all_concentration=[];all_cancellation=[];all_branches=[];branch_q=[]
    for planpath in sorted((root/'batches').glob('*/plan.json')):
        verification=planpath.parent/'verification.json'
        if not verification.exists() or read(verification).get('status')!='COMPLETE':
            continue
        plan=read(planpath);batches.append(plan)
        for provenance_path in [planpath,verification]:
            sources[str(provenance_path.relative_to(R))]=sha(provenance_path)
        for item in plan['scenarios']:
            d=root/'cases'/item['id'];c=read(d/'input.json')
            assert sha(d/'input.json')==item['input_sha256']
            status=read(d/'ac-status.json');ref=read(d/'ac-native.json') if status['verified_reference'] else None
            sources[str((d/'ac-status.json').relative_to(R))]=sha(d/'ac-status.json')
            if ref is not None:
                assert evaluate(c,ref)['all_tested_constraints_pass'];terms(c,ref)
            states={}
            for method,filename in [('AC-OPF','ac-native.json'),('DC-OPF','dc-native.json')]+[(rel,rel+'-native.json') for rel in RELEASES]:
                path=d/filename
                if method=='AC-OPF' and ref is None:
                    path=d/'ac-failed-iterate.json'
                if not path.exists():
                    continue
                state=read(path);states[method]=state;sources[str(path.relative_to(R))]=sha(path)
                sm,bu,br,_=score(c,state,method,ref)
                state_status=('AC_ACCEPTED' if ref is not None else 'AC_FAILED_ITERATE_UNKNOWN') if method=='AC-OPF' else read(d/'dc-status.json')['status'] if method=='DC-OPF' else 'NATIVE_RETURNED'
                prefix={'scenario':d.name,'method':method,'reference_valid':ref is not None,'state_status':state_status}
                if method!='DC-OPF':
                    branch_q.append(dict(prefix,**branch_q_decomposition(c,state)))
                row_prefix={k:v for k,v in prefix.items() if k!='method'}
                all_constraints.extend(dict(row_prefix,**r) for r in constraint_rows(c,state,method,sm,bu,br))
                clamps=clamp_rows(c,d/(method+'-clamps.json'),method) if method in RELEASES else []
                if method in RELEASES:
                    sources[str((d/(method+'-clamps.json')).relative_to(R))]=sha(d/(method+'-clamps.json'))
                all_clamps.extend(dict(row_prefix,**r) for r in clamps)
                focus,ranked,concentration,cancellation=local_budgets(c,state,method,bu,br,clamps)
                for dest,rows in [(all_focus,focus),(all_ranked,ranked),(all_concentration,concentration),(all_cancellation,cancellation)]:
                    dest.extend(dict(row_prefix,**r) for r in rows)
                for j,row in enumerate(br):
                    endpoints={row['from_original_id'],row['to_original_id']}
                    if j+1==321 or row['is_tie'] or endpoints.intersection(FOCUS):
                        x=dict(prefix,**{k:v for k,v in row.items() if k!='method'})
                        if state.get('vm') is not None:
                            ids={int(b[0]):i for i,b in enumerate(c['bus'])};f=ids[row['from_bus']];t=ids[row['to_bus']]
                            x.update(Vm_from=state['vm'][f],Vm_to=state['vm'][t],angle_difference_deg=state['va_deg'][f]-state['va_deg'][t])
                        all_branches.append(x)
            records[d.name]={'case':c,'states':states,'ref':ref,'spec':item,'clamp_paths':{rel:d/(rel+'-clamps.json') for rel in RELEASES},'evidence':'FRESH_FOUR_METHOD_CASE'}
            sources[str((d/'input.json').relative_to(R))]=sha(d/'input.json')
    if not batches:
        print('WAIT: no complete batch; no postprocessing conclusions generated.')
        return
    newcase_ids=list(records);auxiliary=[]
    baseline=replay_baseline(root,sources)
    if baseline is not None:
        records['G300-1.00-REPLAY']=baseline;auxiliary.append('G300-1.00-REPLAY')
    motion=[];paired=[];pair_severity=[];pairs=[];dc_pairs=[];reactive=[];pending=[]
    for plan in batches:
        groups={}
        for item in plan['scenarios']:
            groups.setdefault(item['network'],[]).append(item['id'])
        for ids in groups.values():
            pairs.extend((ids[i],ids[i+1]) for i in range(len(ids)-1))
    for requested in args.pair:
        pair=tuple(requested.split(':'))
        assert len(pair)==2 and all(x in records for x in pair),('Pair must name two complete saved scenarios',requested)
        if pair not in pairs:
            pairs.append(pair)
    if args.pair_config.exists():
        config=read(args.pair_config)
        sources[str(args.pair_config.resolve().relative_to(R))]=sha(args.pair_config)
        for pair in config['pairs']:
            pair=tuple(pair)
            if not all(x in records for x in pair):
                pending.append(pair)
            elif pair not in pairs:
                pairs.append(pair)
    for before,after in pairs:
        dc=dc_equality(records[before],records[after])
        if dc is not None:
            dc_pairs.append(dict(before=before,after=after,**dc))
        for method in sorted(set(records[before]['states'])&set(records[after]['states'])):
            response=reactive_response(records[before],records[after],method)
            if response is not None:
                reactive.append(dict(before=before,after=after,before_evidence=records[before]['evidence'],after_evidence=records[after]['evidence'],**response))
            if method=='AC-OPF':
                continue
            rr,bb,ss=pair_analysis(records[before],records[after],method)
            prefix={'before':before,'after':after,'before_evidence':records[before]['evidence'],'after_evidence':records[after]['evidence']}
            motion.extend(dict(prefix,**r) for r in rr);paired.extend(dict(prefix,**r) for r in bb)
            pair_severity.extend(dict(prefix,**r) for r in ss)
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in [('constraint-locations',all_constraints),('bound-clipping-activity',all_clamps),('focus-buses',all_focus),
                      ('top-residual-buses',all_ranked),('residual-concentration',all_concentration),('signed-bus-budgets',all_cancellation),
                      ('focus-branches',all_branches),('native-reference-motion',motion),('paired-local-budgets',paired),
                      ('paired-severity-summary',pair_severity)]:
        csvsave(out/(name+'.csv'),rows)
    csvsave(out/'reactive-response.csv',reactive)
    csvsave(out/'branch321-physics-decomposition.csv',branch_q)
    save(out/'dc-native-equality.json',dc_pairs)
    save(out/'confirmation-checks.json',confirmation_checks(records,pair_severity,motion))
    hist=R/'results/diagnosis/GSFM-011D/20261022-saved-states'
    for filename,target,select in [('fixed-bus-loading-terms.csv','historical-focus-buses.csv',lambda r:int(r['bus_id']) in FOCUS),
                                   ('incident-branches.csv','historical-branch321.csv',lambda r:int(r['branch_row_1based'])==321)]:
        path=hist/filename;rows=[dict(evidence='HISTORICAL_CSV_ONLY_NOT_FRESH_FORWARD',**r) for r in csvread(path) if float(r['loading']) in [.9,.95] and select(r)]
        csvsave(out/target,rows);sources[str(path.relative_to(R))]=sha(path)
    for codepath in [pathlib.Path(__file__),pathlib.Path(__file__).with_name('electrical.py'),R/'scripts/python/physics_metrics.py']:
        sources[str(codepath.relative_to(R))]=sha(codepath)
    save(out/'manifest.json',{'scope':'Postprocessing saved completed batches only; no new input, inference, solve or repair.',
                             'created_UTC':dt.datetime.now(dt.timezone.utc).isoformat(),'completed_batches':[b['batch'] for b in batches],
                             'cases':newcase_ids,'auxiliary_baselines':auxiliary,'pairs':pairs,'pending_config_pairs':pending,'thresholds':TOL,'source_sha256':sources,'code_sha256':sha(pathlib.Path(__file__)),
                             'notes':['Constraint-location counts checked against audited score for every saved method.',
                                      'Near physical bound uses fixed feasibility tolerance; exactly at shipped bound uses captured FP32 bound equality. Neither establishes actual clipping.',
                                      'Actual clipping means captured input differs from unmodified captured output; material clipping additionally exceeds fixed feasibility tolerance.',
                                      'Native/reference split is symmetric algebraic error-change attribution, not causal identification.',
                                      'Adjacent preregistered cases are paired for descriptive inspection; these pairs do not establish isolated causality if inputs vary in more than one factor.',
                                      'Historical overlays are reduced saved CSV evidence, not freshly recovered raw returned dictionaries.']})
    print(json.dumps({'status':'COMPLETE','completed_batches':len(batches),'cases':len(newcase_ids),'auxiliary_baselines':auxiliary,'pairs':len(pairs),'pending_config_pairs':len(pending),'out':str(out)}))


if __name__=='__main__':
    main()
