"""Independent saved-array check of confirmation claims; no inference or solves."""
import json
from pathlib import Path
import numpy as np
from figures import OUT, RELEASES, load_cases, read, sha


def native(case, release):
    filename = {"AC-OPF": "ac", "DC-OPF": "dc"}.get(release, release)
    return read(case["directory"] / (filename + "-native.json"))


def capture(case, release, variable):
    return next(row for row in read(case["directory"] / (release + "-clamps.json"))["captures"] if row["variable"] == variable)


def equations(case, state):
    """Direct pi-branch equations, independently from the study scorer."""
    c = case["input"]
    b, e = np.asarray(c["bus"]), np.asarray(c["branch"])
    ids = {int(row[0]): i for i, row in enumerate(b)}
    f = np.array([ids[int(row[0])] for row in e])
    t = np.array([ids[int(row[1])] for row in e])
    v = np.asarray(state["vm"]) * np.exp(1j * np.deg2rad(state["va_deg"]))
    y = e[:, 10] / (e[:, 2] + 1j * e[:, 3])
    charging = 1j * e[:, 4] * e[:, 10] / 2
    tap = np.where(e[:, 8] == 0, 1, e[:, 8]) * np.exp(1j * np.deg2rad(e[:, 9]))
    i_f = (y + charging) / abs(tap)**2 * v[f] - y / np.conj(tap) * v[t]
    i_t = (y + charging) * v[t] - y / tap * v[f]
    sf = c["baseMVA"] * v[f] * np.conj(i_f)
    st = c["baseMVA"] * v[t] * np.conj(i_t)
    r = -(b[:, 2] + 1j * b[:, 3]) - (b[:, 4] - 1j * b[:, 5]) * abs(v)**2
    for j, g in enumerate(c["gen"]):
        if g[7] > 0:
            r[ids[int(g[0])]] += state["pg_mw"][j] + 1j * state["qg_mvar"][j]
    np.add.at(r, f, -sf)
    np.add.at(r, t, -st)
    return r, sf, st


def main():
    cases = {row["id"]: row for row in load_cases(set())}
    checks = read(OUT / "mechanisms/confirmation-checks.json")
    assert checks["status"] == "COMPLETE"
    residual_differences = []
    infeasible_count = 0
    for name, case in cases.items():
        for release in RELEASES:
            r, _, _ = equations(case, native(case, release))
            for component, values in (("P", abs(r.real)), ("Q", abs(r.imag))):
                for statistic, expected in (("mean", values.mean()), ("p95", np.percentile(values, 95)), ("max", values.max())):
                    residual_differences.append(abs(case["summary"][release][component][statistic] - expected))
            infeasible_count += bool(max(abs(r.real).max(), abs(r.imag).max()) > 1e-3)
    assert max(residual_differences) < 1e-6
    assert infeasible_count == len(cases) * 2 == 52

    baseline = cases["G300-0.93"]
    p_case, q_case = cases["CONF-P0935-Q093"], cases["CONF-P093-Q0935"]
    dc_equal = {key: native(baseline, "DC-OPF")[key] == native(q_case, "DC-OPF")[key]
                for key in ("pg_mw", "va_deg", "pf_mw", "pt_mw")}
    assert all(dc_equal.values())
    reactive = {}
    for release in RELEASES:
        before, after = native(baseline, release), native(q_case, release)
        qb, qa = np.asarray(before["qg_mvar"]), np.asarray(after["qg_mvar"])
        cb, ca = capture(baseline, release, "Qg"), capture(q_case, release, "Qg")
        clipped_b = np.asarray(cb["input"]) != np.asarray(cb["output"])
        clipped_a = np.asarray(ca["input"]) != np.asarray(ca["output"])
        assert np.array_equal(clipped_a, clipped_b)
        assert np.max(abs((qa - qb)[clipped_b]), initial=0) == 0
        native_change = float(qa.sum() - qb.sum())
        ac_change = sum(native(q_case, "AC-OPF")["qg_mvar"]) - sum(native(baseline, "AC-OPF")["qg_mvar"])
        assert native_change < 0 < ac_change
        reactive[release] = {"native_Qg_change_MVAr": native_change, "AC_Qg_change_MVAr": ac_change,
                             "same_clipped_rows": True, "clipped_count": int(sum(clipped_a)),
                             "clipped_rows_returned_Qg_change": 0}
    vm = {}
    for case in (baseline, p_case, q_case, cases["CONF-LOC-plus075"], cases["CONF-LOC-plus125"]):
        index = next(i for i, row in enumerate(case["input"]["bus"]) if row[0] == 235)
        cap = capture(case, "newer-base-v2", "V")
        vm[case["id"]] = {"preclip": cap["input"][index], "native": native(case, "newer-base-v2")["vm"][index]}
    assert vm[p_case["id"]]["native"] > .94 + 1e-4
    assert abs(vm[q_case["id"]]["native"] - .94) < 1e-7 and vm[q_case["id"]]["preclip"] < .94
    assert abs(vm["CONF-LOC-plus075"]["native"] - 1.06) < 1e-7
    assert abs(vm["CONF-LOC-plus125"]["native"] - .94) < 1e-7

    local = []
    loc_baseline = np.asarray(cases["LOC-plus050"]["input"]["bus"])
    for name in ("CONF-LOC-plus075", "CONF-LOC-plus125"):
        case = cases[name]
        buses = np.asarray(case["input"]["bus"])
        total_diff = abs(buses[:, 2:4].sum(axis=0) - loc_baseline[:, 2:4].sum(axis=0))
        assert max(total_diff) < 1e-8
        mask = np.isin(buses[:, 0], [235, 238])
        assert np.array_equal(buses[mask, 2:4], loc_baseline[mask, 2:4])
        local.append({"scenario": name, "max_PQ_total_difference": float(max(total_diff)), "bus235_238_PQ_unchanged": True})

    ties = {}
    for name in ("CONF-A600-plus040", "CONF-A600-minus040"):
        case = cases[name]
        e = np.asarray(case["input"]["branch"])
        rated = (e[:, 5] > 0) & (e[:, 10] > 0)
        assert np.array_equal(np.where(rated)[0] + 1, [823, 824])
        ties[name] = {}
        for release in (*RELEASES, "AC-OPF"):
            _, sf, st = equations(case, native(case, release))
            loading = np.maximum(abs(sf[rated]), abs(st[rated]))
            claimed = checks["existing600_tie_test"]["observations"][name]["methods"][release]
            assert abs(max(loading) - claimed["max_loading"]) < 1e-6
            ties[name][release] = {"max_loading_MVA": float(max(loading)), "violation_count": int(sum(loading - e[rated, 5] > 1e-3))}
    out = {"status": "PASS", "scope": "Independent saved-array sums, clipping, direct pi-branch equations; zero model or solver calls",
           "script_sha256": sha(__file__), "confirmation_checks_sha256": sha(OUT / "mechanisms/confirmation-checks.json"),
           "completed_inputs": len(cases), "native_states_recomputed": len(cases)*2,
           "native_states_with_balance_failure": infeasible_count,
           "max_difference_from_saved_PQ_summary": float(max(residual_differences)),
           "Q_only_DC_equal_arrays": dc_equal, "reactive_response": reactive, "v2_Vm235": vm,
           "fixed_total_location_inputs": local, "ties": ties}
    target = OUT / "mechanisms/confirmation-independent-review.json"
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: out[key] for key in ("status", "native_states_recomputed", "max_difference_from_saved_PQ_summary")}, indent=2))


if __name__ == "__main__":
    main()
