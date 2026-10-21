"""Independent MATPOWER-parameter checks; Python stdlib, no learned flow head.

This evaluator supports active/inactive branches/generators, pi lines,
off-nominal complex taps, bus shunts, polynomial costs and Q-cost rows.
It rejects unsupported PWL costs/capability curves rather than certifying them.
Input angles are degrees; reported residuals MW/MVAr; flows MVA.
Validate against MATPOWER before scientific use. See tests for toy checks only.
"""
import argparse
import cmath
import json
import math


def wrap_degrees(x):
    return (x + 180.0) % 360.0 - 180.0


def _positive(x):
    return max(0.0, x)


def branch_flows(case, vm, va_deg):
    ids = [int(b[0]) for b in case['bus']]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate bus IDs')
    lookup = {bid: i for i, bid in enumerate(ids)}
    if len(vm) != len(ids) or len(va_deg) != len(ids):
        raise ValueError('voltage length mismatch')
    volt = [m * cmath.exp(1j * math.radians(a)) for m, a in zip(vm, va_deg)]
    sf, st = [], []
    for row in case['branch']:
        f, t = lookup[int(row[0])], lookup[int(row[1])]
        if row[10] == 0:
            sf.append(0j)
            st.append(0j)
            continue
        z = complex(row[2], row[3])
        if abs(z) == 0:
            raise ValueError('zero-impedance active branch needs explicit model')
        y = 1 / z
        bc = 1j * row[4] / 2
        tap = (row[8] or 1.0) * cmath.exp(1j * math.radians(row[9]))
        yff, yft = (y + bc) / abs(tap)**2, -y / tap.conjugate()
        ytf, ytt = -y / tap, y + bc
        sf.append(case['baseMVA'] * volt[f] * (yff * volt[f] + yft * volt[t]).conjugate())
        st.append(case['baseMVA'] * volt[t] * (ytf * volt[f] + ytt * volt[t]).conjugate())
    return sf, st


def cost(case, pg, qg):
    rows, ng = case['gencost'], len(case['gen'])
    if len(rows) not in (ng, 2 * ng):
        raise ValueError('gencost must have ng or 2ng rows')
    total = 0.0
    for i, row in enumerate(rows):
        if int(row[0]) != 2:
            raise ValueError('PWL cost unsupported; do not silently fit polynomial')
        if int(row[3]) != row[3] or row[3] < 1 or len(row) < 4 + int(row[3]):
            raise ValueError('invalid polynomial NCOST')
        if case['gen'][i % ng][7] <= 0:
            continue
        value = pg[i] if i < ng else qg[i - ng]
        coeff = row[4:4 + int(row[3])]
        subtotal = 0.0
        for c in coeff:
            subtotal = subtotal * value + c
        total += subtotal
    return total


def evaluate(case, prediction, thresholds=None):
    limits = {'balance_mva': 1e-3, 'generator_mva': 1e-3,
              'voltage_pu': 1e-4, 'branch_mva': 1e-3, 'angle_deg': 1e-3}
    limits.update(thresholds or {})
    vm, va = prediction['vm'], prediction['va_deg']
    pg, qg = prediction['pg_mw'], prediction['qg_mvar']
    ng, nb = len(case['gen']), len(case['bus'])
    if len(pg) != ng or len(qg) != ng:
        raise ValueError('generator length mismatch')
    if not all(math.isfinite(x) for arr in (vm, va, pg, qg) for x in arr):
        raise ValueError('nonfinite prediction')
    if any(b[1] == 4 for b in case['bus']):
        raise ValueError('isolated type-4 buses require explicit active-set mapping')
    for g in case['gen']:
        if g[9] < 0 and g[8] == 0:
            raise ValueError('dispatchable-load constant power-factor constraint unsupported')
        if len(g) >= 16 and any(g[j] != 0 for j in range(10, 16)):
            raise ValueError('nontrivial generator capability curves unsupported')
    for b in case['branch']:
        if not math.isfinite(b[5]) or b[5] < 0:
            raise ValueError('RATE_A must be finite and nonnegative; zero is unlimited')
    for key in ('A', 'N', 'dcline'):
        if key in case and case[key]:
            raise ValueError('unsupported extra OPF constraints: ' + key)
    sf, st = branch_flows(case, vm, va)
    index = {int(b[0]): i for i, b in enumerate(case['bus'])}
    injection = [complex(-b[2], -b[3]) for b in case['bus']]
    gviol = []
    for j, g in enumerate(case['gen']):
        if g[7] <= 0:
            gviol.extend([abs(pg[j]), abs(qg[j])])
            continue
        injection[index[int(g[0])]] += complex(pg[j], qg[j])
        gviol.extend([_positive(g[9]-pg[j]), _positive(pg[j]-g[8]),
                      _positive(g[4]-qg[j]), _positive(qg[j]-g[3])])
    # GS consumes MW at |V|=1; positive BS injects MVAr, hence -j*BS.
    outgoing = [complex(b[4], -b[5]) * vm[i]**2 for i, b in enumerate(case['bus'])]
    thermal, angles, loading, checked = [], [], [], []
    for k, b in enumerate(case['branch']):
        f, t = index[int(b[0])], index[int(b[1])]
        outgoing[f] += sf[k]
        outgoing[t] += st[k]
        if b[10] == 0:
            continue
        if b[5] > 0:
            checked.append(k)
            thermal.extend([_positive(abs(sf[k])-b[5]), _positive(abs(st[k])-b[5])])
            loading.append(max(abs(sf[k]), abs(st[k]))/b[5])
        # Match MATPOWER's unwrapped angle difference constraints, not shift-subtracted angles.
        delta = va[f] - va[t]
        lo, hi = b[11], b[12]
        active_angle = ((lo != 0 and lo > -360) or (hi != 0 and hi < 360)
                        or (lo != 0 and hi == 0) or (lo == 0 and hi != 0))
        if active_angle:
            if lo >= -360:
                angles.append(_positive(lo - delta))
            if hi <= 360:
                angles.append(_positive(delta - hi))
    residual = [s-o for s, o in zip(injection, outgoing)]
    vviol = [_positive(x) for i, b in enumerate(case['bus']) for x in (b[12]-vm[i], vm[i]-b[11])]
    maxp = max(abs(s.real) for s in residual)
    maxq = max(abs(s.imag) for s in residual)
    out = {
        'max_p_residual_mw': maxp, 'max_q_residual_mvar': maxq,
        'mean_abs_p_residual_mw': sum(abs(s.real) for s in residual)/nb,
        'mean_abs_q_residual_mvar': sum(abs(s.imag) for s in residual)/nb,
        'max_generator_component_violation_mw_or_mvar': max(gviol, default=0),
        'max_voltage_violation_pu': max(vviol, default=0),
        'max_branch_violation_mva': max(thermal, default=0),
        'max_angle_violation_deg': max(angles, default=0),
        'max_rated_branch_loading': max(loading, default=None),
        'rated_active_branch_count': len(checked),
        'unlimited_active_branch_count': sum(b[10] != 0 and b[5] == 0 for b in case['branch']),
        'generation_cost_per_hour': cost(case, pg, qg),
        'pf_mw': [s.real for s in sf], 'qf_mvar': [s.imag for s in sf],
        'pt_mw': [s.real for s in st], 'qt_mvar': [s.imag for s in st],
        'thresholds': limits,
    }
    out['all_tested_constraints_pass'] = (
        max(maxp, maxq) <= limits['balance_mva']
        and out['max_generator_component_violation_mw_or_mvar'] <= limits['generator_mva']
        and out['max_voltage_violation_pu'] <= limits['voltage_pu']
        and out['max_branch_violation_mva'] <= limits['branch_mva']
        and out['max_angle_violation_deg'] <= limits['angle_deg'])
    out['coverage_note'] = 'Original box, balance, angle and positive RATE_A limits only; unlimited branches are not thermally certified.'
    return out


def aligned_angle_errors(pred, target, ref_index):
    if len(pred) != len(target):
        raise ValueError('angle vector mismatch')
    return [abs(wrap_degrees((p-pred[ref_index])-(t-target[ref_index])))
            for p, t in zip(pred, target)]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('case_json')
    parser.add_argument('prediction_json')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with open(args.case_json, encoding='utf-8-sig') as stream:
        case_data = json.load(stream)
    with open(args.prediction_json, encoding='utf-8-sig') as stream:
        pred_data = json.load(stream)
    result = evaluate(case_data, pred_data)
    with open(args.output, 'w', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
