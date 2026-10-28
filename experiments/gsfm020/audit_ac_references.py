"""Read-only independent AC reference audit; never imports an OPF or model runner.

Rebuilds branch stamps directly, cross-checks PYPOWER Ybus, validates all parsed
original limits/loads/shunts, and checks every prior tracked-file SHA-256.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pypower.makeYbus import makeYbus

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/comparisons/GSFM-020/20261026-local-operating-conditions"
OPTIONS = dict(tol=1e-9, bound_relax_factor=0.0, max_cpu_time=120.0,
               acceptable_tol=1e-9, max_iter=3000, constr_viol_tol=1e-10,
               print_level=0)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def near(value, expected, tol=1e-9):
    assert abs(value - expected) <= tol, (value, expected, tol)


def parsed_check(case, raw):
    d = raw["parsed_network"]
    base = case["baseMVA"]
    near(d["baseMVA"], base)
    assert d["per_unit"] is True
    assert len(d["bus"]) == len(case["bus"])
    assert len(d["gen"]) == len(case["gen"])
    assert len(d["branch"]) == len(case["branch"])
    loads, shunts = {}, {}
    for x in d.get("load", {}).values():
        assert x["status"] == 1
        i = int(x["load_bus"])
        loads[i] = loads.get(i, 0j) + complex(x["pd"], x["qd"]) * base
    for x in d.get("shunt", {}).values():
        assert x["status"] == 1
        i = int(x["shunt_bus"])
        shunts[i] = shunts.get(i, 0j) + complex(x["gs"], x["bs"]) * base
    for b in case["bus"]:
        i = int(b[0]); x = d["bus"][str(i)]
        assert x["source_id"] == ["bus", i]
        for key, value in [("bus_i", b[0]), ("bus_type", b[1]),
                           ("area", b[6]), ("vm", b[7]),
                           ("va", math.radians(b[8])), ("base_kv", b[9]),
                           ("zone", b[10]), ("vmax", b[11]), ("vmin", b[12])]:
            near(x[key], value)
        near(loads.get(i, 0j), complex(b[2], b[3]), 1e-8)
        near(shunts.get(i, 0j), complex(b[4], b[5]), 1e-8)
    for j, b in enumerate(case["branch"], 1):
        x = d["branch"][str(j)]
        assert x["source_id"] == ["branch", j]
        for key, value in [("f_bus", b[0]), ("t_bus", b[1]), ("br_r", b[2]),
                           ("br_x", b[3]), ("tap", b[8] or 1),
                           ("shift", math.radians(b[9])), ("br_status", b[10]),
                           ("angmin", math.radians(b[11])),
                           ("angmax", math.radians(b[12]))]:
            near(x[key], value)
        near(x["b_fr"], b[4] / 2)
        near(x["b_to"], b[4] / 2)
        near(x.get("g_fr", 0), 0)
        near(x.get("g_to", 0), 0)
        for key, col in [("rate_a", 5), ("rate_b", 6), ("rate_c", 7)]:
            near(x.get(key, 0), b[col] / base)
    for j, g in enumerate(case["gen"], 1):
        x = d["gen"][str(j)]
        assert x["source_id"] == ["gen", j]
        for key, value in [("gen_bus", g[0]), ("pg", g[1] / base),
                           ("qg", g[2] / base), ("qmax", g[3] / base),
                           ("qmin", g[4] / base), ("vg", g[5]),
                           ("mbase", g[6]), ("gen_status", g[7]),
                           ("pmax", g[8] / base), ("pmin", g[9] / base)]:
            near(x[key], value)
        co = case["gencost"][j - 1]; n = int(co[3])
        assert x["model"] == int(co[0]) == 2 and x["ncost"] == n
        near(x["startup"], co[1]); near(x["shutdown"], co[2])
        assert np.allclose(x["cost"], [v * base ** (n - 1 - k)
                           for k, v in enumerate(co[4:4+n])], rtol=0, atol=1e-7)
    assert raw["options"] == OPTIONS
    assert raw["method"] in ["default", "flat"]


def physical_check(c, s):
    buses = np.asarray(c["bus"], dtype=float)
    gens = np.asarray(c["gen"], dtype=float)
    branches = np.asarray(c["branch"], dtype=float)
    ids = {int(b[0]): i for i, b in enumerate(buses)}
    base = c["baseMVA"]
    vm = np.asarray(s["vm"], dtype=float)
    theta = np.asarray(s["va_deg"], dtype=float)
    pg = np.asarray(s["pg_mw"], dtype=float)
    qg = np.asarray(s["qg_mvar"], dtype=float)
    for values in [vm, theta, pg, qg]:
        assert np.isfinite(values).all()
    assert len(vm) == len(theta) == len(buses)
    assert len(pg) == len(qg) == len(gens)
    volt = vm * np.exp(1j * np.deg2rad(theta))
    out = np.zeros(len(buses), dtype=complex)
    sf, st, angle_excess, thermal_excess = [], [], [], []
    for b in branches:
        i, j = ids[int(b[0])], ids[int(b[1])]
        if b[10] <= 0:
            sf.append(0j); st.append(0j); continue
        y = 1 / complex(b[2], b[3])
        tap = (b[8] or 1) * np.exp(1j * math.radians(b[9]))
        end = y + 1j * b[4] / 2
        f = base * volt[i] * np.conj(end / abs(tap)**2 * volt[i] - y / np.conj(tap) * volt[j])
        t = base * volt[j] * np.conj(-y / tap * volt[i] + end * volt[j])
        sf.append(f); st.append(t); out[i] += f; out[j] += t
        if b[5] > 0:
            thermal_excess.append(max(abs(f), abs(t)) - b[5])
        da = theta[i] - theta[j]
        if b[11] > -360:
            angle_excess.append(b[11] - da)
        if b[12] < 360:
            angle_excess.append(da - b[12])
    generated = np.zeros(len(buses), dtype=complex)
    for j, g in enumerate(gens):
        if g[7] > 0:
            generated[ids[int(g[0])]] += complex(pg[j], qg[j])
        else:
            near(pg[j], 0); near(qg[j], 0)
    shunts = (buses[:, 4] - 1j * buses[:, 5]) * vm**2
    residual = generated - buses[:, 2] - 1j * buses[:, 3] - out - shunts
    bint, eint = buses.copy(), branches.copy()
    bint[:, 0] = np.arange(len(buses))
    eint[:, 0] = [ids[int(b[0])] for b in branches]
    eint[:, 1] = [ids[int(b[1])] for b in branches]
    ybus, yf, yt = makeYbus(base, bint, eint)
    yr = generated - buses[:, 2] - 1j * buses[:, 3] - base * volt * np.conj(ybus @ volt)
    cross = float(np.max(np.abs(residual - yr)))
    assert cross < 1e-6
    active = gens[:, 7] > 0
    pgex = max(0., np.max(gens[active, 9] - pg[active]), np.max(pg[active] - gens[active, 8]))
    qgex = max(0., np.max(gens[active, 4] - qg[active]), np.max(qg[active] - gens[active, 3]))
    vex = max(0., np.max(buses[:, 12] - vm), np.max(vm - buses[:, 11]))
    pmax = float(np.max(np.abs(residual.real)))
    qmax = float(np.max(np.abs(residual.imag)))
    amax = max([0.] + angle_excess)
    tmax = max([0.] + thermal_excess)
    passed = pmax <= 1e-3 and qmax <= 1e-3 and pgex <= 1e-3 and qgex <= 1e-3 and vex <= 1e-4 and amax <= 1e-3 and tmax <= 1e-3
    result = dict(max_P_MW=pmax, max_Q_MVAr=qmax,
                  Pg_excess_MW=float(pgex), Qg_excess_MVAr=float(qgex),
                  Vm_excess_pu=float(vex), angle_excess_deg=float(amax),
                  rated_branches=len(thermal_excess),
                  thermal_excess_MVA=float(tmax) if thermal_excess else None,
                  direct_stamp_vs_PYPOWER_Ybus_MVA=cross, joint_pass=bool(passed))
    return result, np.asarray(sf), np.asarray(st)


def audit_case(d):
    c = read(d / "input.json"); status = read(d / "ac-status.json")
    accepted = status["verified_reference"]
    audits = []
    for i, attempt in enumerate(status["attempts"]):
        path = d / f"ac-attempt{i}.json"
        if not path.exists():
            audits.append(dict(attempt=i, status="NO_RETURNED_SOLVER_POINT_UNKNOWN")); continue
        raw = read(path); parsed_check(c, raw)
        assert attempt["request"]["remaining_seconds"] == 120
        assert attempt["request"]["capture_internal_iterate"] is False
        assert attempt["method"] == ["default", "flat"][i]
        native_path = d / f"ac-attempt{i}-native.json"
        if not native_path.exists():
            assert not accepted
            audits.append(dict(attempt=i, status="NO_COMPLETE_NATIVE_STATE_UNKNOWN",
                               termination=raw["termination_status"],
                               parsed_fields_preserved=True))
            continue
        s = read(native_path)
        metrics, sf, st = physical_check(c, s)
        expected_accept = raw["termination_status"] in ["LOCALLY_SOLVED", "OPTIMAL", "ALMOST_LOCALLY_SOLVED"] and metrics["joint_pass"]
        sol = raw["solution"]; base = c["baseMVA"]
        for j, b in enumerate(c["bus"]):
            point = sol["bus"][str(int(b[0]))]
            near(s["vm"][j], point["vm"], 1e-12)
            near(s["va_deg"][j], math.degrees(point["va"]), 1e-10)
        for j, g in enumerate(c["gen"]):
            if g[7] <= 0:
                near(s["pg_mw"][j], 0); near(s["qg_mvar"][j], 0)
                continue
            point = sol["gen"][str(j+1)]
            near(s["pg_mw"][j], point["pg"] * base, 1e-9)
            near(s["qg_mvar"][j], point["qg"] * base, 1e-9)
        branch_error = 0.
        for j, b in enumerate(c["branch"]):
            if b[10] <= 0:
                continue
            point = sol["branch"][str(j+1)]
            for key, val in [("pf", sf[j].real), ("qf", sf[j].imag),
                             ("pt", st[j].real), ("qt", st[j].imag)]:
                branch_error = max(branch_error, abs(point[key] * base - val))
        if expected_accept:
            assert branch_error < 1e-5
        objective = sum(float(np.polyval(row[4:4+int(row[3])], pg))
                        for row, pg in zip(c["gencost"], s["pg_mw"]))
        near(objective, raw["objective"], 1e-4)
        if expected_accept:
            assert accepted and read(d / "ac-native.json") == s
        audits.append(dict(attempt=i, termination=raw["termination_status"],
                           objective=objective, expected_accept=expected_accept,
                           parsed_fields_preserved=True, metrics=metrics,
                           reconstructed_vs_solver_branch_max_MVA=branch_error))
    assert accepted == any(x.get("expected_accept", False) for x in audits)
    return dict(scenario=d.name, status="PASS", reference_accepted=accepted,
                input_sha256=sha(d / "input.json"), attempts=audits)


def main():
    p = argparse.ArgumentParser(); p.add_argument("--case", action="append")
    p.add_argument("--out", type=Path, required=True); args = p.parse_args()
    assert not args.out.exists(), "Use a new audit output; preserve earlier audits"
    prior = read(OUT / "prior-tracked-sha256.json")
    changed = [name for name, expected in prior.items()
               if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
    assert not changed, ("Previous tracked files changed", changed)
    cases = ([OUT / "cases" / name for name in args.case] if args.case else
             sorted(d for d in (OUT / "cases").iterdir() if (d / "run-status.json").exists()))
    report = dict(status="PASS", no_new_solves_or_forwards=True,
                  preserved_prior_tracked_files=len(prior),
                  audited_cases=[audit_case(d) for d in cases])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", cases=len(cases), prior_files=len(prior), output=str(args.out))))


if __name__ == "__main__":
    main()
