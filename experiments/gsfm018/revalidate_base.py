"""Revalidate DERIVED base states from tracked 11D CSVs; no model or solver.

The raw predict() dictionaries remain unavailable. This reconstructs only the
four native AC-state arrays, records whether their serialization matches the
historical native JSON hash, and saves explicitly labelled derivative artifacts.
"""
import argparse
import csv
import datetime
import hashlib
import json
import pathlib
import platform
import subprocess
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/python"))
from matpower_case import read_case, validate
from physics_metrics import aligned_angle_errors, branch_flows, evaluate

SOURCE_SHA = "69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5"
BALANCE_TOL = 1e-3
CROSSCHECK_TOL = 1e-7
RELEASES = ["microsoft-v1.1", "newer-base-v2"]
METHODS = {"AC-reference": "AC-OPF", "microsoft-v1.1": "Microsoft v1.1", "newer-base-v2": "Newer v2"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return digest(pathlib.Path(path).read_bytes())


def encoded(obj):
    return (json.dumps(obj, indent=2, allow_nan=False) + "\n").encode("utf-8")


def save_new_or_identical(path, obj):
    data = encoded(obj)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("Refusing to overwrite different derivative: " + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest(data), "bytes": len(data)}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def record_input(path):
    record = {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}
    try:
        rel = path.relative_to(ROOT).as_posix()
        blob = subprocess.check_output(["git", "show", "HEAD:" + rel], cwd=ROOT)
        record.update(repo_relative_path=rel, git_HEAD_blob_sha256=digest(blob))
        record["working_text_matches_HEAD_after_newline_normalization"] = path.read_bytes().replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n")
        assert record["working_text_matches_HEAD_after_newline_normalization"]
    except ValueError:
        record["repo_relative_path"] = None
    return record


def extract_state(bus_rows, gen_rows, release, reference=False):
    buses = {int(row["bus_id"]): row for row in bus_rows if row["release"] == release}
    gens = {int(row["gen_row_1based"]): row for row in gen_rows if row["release"] == release}
    assert len(buses) == 300 and len(gens) == 69
    assert sum(row["release"] == release for row in bus_rows) == 300
    assert sum(row["release"] == release for row in gen_rows) == 69
    suffix = "ref" if reference else "pred"
    state = {"vm": [], "va_deg": [], "pg_mw": [], "qg_mvar": []}
    for bus in CASE["bus"]:
        row = buses[int(bus[0])]
        assert float(row["loading"]) == 1 and row["reference_available"] == "True"
        assert float(row["demand_P_pred"]) == bus[2] and float(row["demand_Q_pred"]) == bus[3]
        assert float(row["demand_P_ref"]) == bus[2] and float(row["demand_Q_ref"]) == bus[3]
        state["vm"].append(float(row["Vm_" + suffix + "_pu"]))
        state["va_deg"].append(float(row["angle_" + suffix + "_deg"]))
    for i, gen in enumerate(CASE["gen"], 1):
        row = gens[i]
        assert int(row["bus_id"]) == int(gen[0])
        state["pg_mw"].append(float(row["Pg_" + suffix + "_MW"]))
        state["qg_mvar"].append(float(row["Qg_" + suffix + "_MVAr"]))
    assert all(np.isfinite(v).all() for v in state.values())
    return state


def stamp_matrices(case):
    """Independent complex128 MATPOWER pi stamp; does not call branch_flows."""
    buses = np.asarray(case["bus"], dtype=np.float64)
    lines = np.asarray(case["branch"], dtype=np.float64)
    lookup = {int(row[0]): i for i, row in enumerate(buses)}
    f = np.array([lookup[int(row[0])] for row in lines])
    t = np.array([lookup[int(row[1])] for row in lines])
    status = lines[:, 10]
    ys = status / (lines[:, 2] + 1j * lines[:, 3])
    charging = status * lines[:, 4]
    tapmag = np.where(lines[:, 8] == 0, 1.0, lines[:, 8])
    tap = tapmag * np.exp(1j * np.deg2rad(lines[:, 9]))
    ytt = ys + 0.5j * charging
    yff = ytt / (tap * np.conjugate(tap))
    yft, ytf = -ys / np.conjugate(tap), -ys / tap
    yf = np.zeros((len(lines), len(buses)), dtype=np.complex128)
    yt = np.zeros_like(yf)
    row = np.arange(len(lines))
    yf[row, f], yf[row, t] = yff, yft
    yt[row, f], yt[row, t] = ytf, ytt
    ybus = np.zeros((len(buses), len(buses)), dtype=np.complex128)
    np.add.at(ybus, (f, f), yff)
    np.add.at(ybus, (f, t), yft)
    np.add.at(ybus, (t, f), ytf)
    np.add.at(ybus, (t, t), ytt)
    ybus[np.arange(len(buses)), np.arange(len(buses))] += (buses[:, 4] + 1j * buses[:, 5]) / case["baseMVA"]
    return ybus, yf, yt, f, t, lookup


def residual_summary(values, ids):
    a = np.abs(values)
    return {"mean_abs": float(a.mean()), "median_abs": float(np.median(a)),
            "p95_abs_linear_interpolation": float(np.percentile(a, 95)), "max_abs": float(a.max()),
            "max_abs_bus_id": int(ids[int(a.argmax())]),
            "violating_bus_count_at_0.001": int((a > BALANCE_TOL).sum()),
            "top5_absolute": [{"bus_id": int(ids[i]), "signed_residual": float(values[i])}
                              for i in sorted(range(len(a)), key=lambda i: (-a[i], ids[i]))[:5]]}


def bound_summary(values, lo, hi, ids, tolerance):
    values, lo, hi = (np.asarray(x) for x in (values, lo, hi))
    lower = np.maximum(lo - values, 0)
    upper = np.maximum(values - hi, 0)
    return {"tolerance": tolerance, "lower_violation_count": int((lower > tolerance).sum()),
            "upper_violation_count": int((upper > tolerance).sum()),
            "max_lower_excess": float(lower.max()), "max_upper_excess": float(upper.max()),
            "lower_active_count": int((np.abs(values - lo) <= tolerance).sum()),
            "upper_active_count": int((np.abs(values - hi) <= tolerance).sum()),
            "violations": [{"id": ids[i], "lower_excess": float(lower[i]), "upper_excess": float(upper[i])}
                           for i in range(len(values)) if max(lower[i], upper[i]) > tolerance]}


def main(args):
    global CASE
    assert sha(args.case) == SOURCE_SHA, "Original case bytes do not match pin"
    CASE = read_case(args.case)
    validate(CASE)
    assert [len(CASE[k]) for k in ("bus", "gen", "branch")] == [300, 69, 411]
    assert CASE["baseMVA"] == 100 and all(row[5] == 0 for row in CASE["branch"])
    assert all(row[11] == -360 and row[12] == 360 for row in CASE["branch"])
    evidence = ROOT / "results/diagnosis/GSFM-011D/20261022-saved-states"
    baseline = ROOT / "results/comparisons/GSFM-011B/20261022-original-case300"
    bus_path, gen_path = evidence / "base-bus-terms.csv", evidence / "base-generators.csv"
    rows, gen_rows = read_csv(bus_path), read_csv(gen_path)
    assert len(rows) == 600 and len(gen_rows) == 138
    states = {release: extract_state(rows, gen_rows, release) for release in RELEASES}
    states["AC-reference"] = extract_state(rows, gen_rows, RELEASES[0], reference=True)
    assert states["AC-reference"] == extract_state(rows, gen_rows, RELEASES[1], reference=True)
    inventory = json.loads((baseline / "artifact-inventory.json").read_text())
    prior_bus = {(r["method"], int(r["original_bus_id"])): r for r in read_csv(baseline / "bus-diagnostics.csv")}
    source_records = [record_input(p) for p in [args.case, bus_path, gen_path, baseline / "artifact-inventory.json", baseline / "bus-diagnostics.csv"]]
    derived_files, native_hash_check = {}, {}
    for label, state in states.items():
        prior_name = ("ac" if label == "AC-reference" else label) + "-native.json"
        native_hash_check[label] = {"historical_native_filename": prior_name,
                                   "historical_native_sha256": inventory[prior_name]["sha256"],
                                   "reconstructed_native_serialization_sha256": digest(encoded(state)),
                                   "exact_historical_native_serialization_hash_match": digest(encoded(state)) == inventory[prior_name]["sha256"]}
        derived_files[label] = save_new_or_identical(args.scratch / (label + "-DERIVED-state.json"),
            {"artifact_kind": "DERIVED_FROM_TRACKED_11D_CSV_NOT_A_NEW_NATIVE_RETURN", "state_label": label,
             "source_csv_sha256": {"base-bus-terms.csv": sha(bus_path), "base-generators.csv": sha(gen_path)},
             "original_bus_ids": [int(row[0]) for row in CASE["bus"]],
             "original_generator_rows_1based": list(range(1, 70)), "state": state})
    assert all(v["exact_historical_native_serialization_hash_match"] for v in native_hash_check.values()), "Derived arrays differ from historically hashed native state"
    ybus, yf, yt, f, t, lookup = stamp_matrices(CASE)
    ids = [int(row[0]) for row in CASE["bus"]]
    gbus = np.array([lookup[int(row[0])] for row in CASE["gen"]])
    online = np.array([row[7] > 0 for row in CASE["gen"]])
    bus = np.asarray(CASE["bus"])
    gen = np.asarray(CASE["gen"])
    all_metrics, flow_cache = {}, {}
    for label, state in states.items():
        evaluated = evaluate(CASE, state)
        sf, st = [np.asarray(x) for x in branch_flows(CASE, state["vm"], state["va_deg"])]
        volt = np.asarray(state["vm"]) * np.exp(1j * np.deg2rad(state["va_deg"]))
        generation = np.zeros(300, dtype=np.complex128)
        np.add.at(generation, gbus[online], (np.asarray(state["pg_mw"]) + 1j * np.asarray(state["qg_mvar"]))[online])
        demand = bus[:, 2] + 1j * bus[:, 3]
        outgoing = (bus[:, 4] - 1j * bus[:, 5]) * np.asarray(state["vm"]) ** 2
        np.add.at(outgoing, f, sf)
        np.add.at(outgoing, t, st)
        residual = generation - demand - outgoing
        matrix_residual = generation - demand - CASE["baseMVA"] * volt * np.conjugate(ybus @ volt)
        differences = {"branch_sum_vs_Ybus_max_complex_MVA": float(np.abs(residual - matrix_residual).max()),
                       "from_flows_vs_Yf_max_complex_MVA": float(np.abs(sf - CASE["baseMVA"] * volt[f] * np.conjugate(yf @ volt)).max()),
                       "to_flows_vs_Yt_max_complex_MVA": float(np.abs(st - CASE["baseMVA"] * volt[t] * np.conjugate(yt @ volt)).max())}
        old = np.array([complex(float(prior_bus[(METHODS[label], bid)]["P_imbalance_MW"]), float(prior_bus[(METHODS[label], bid)]["Q_imbalance_MVAr"])) for bid in ids])
        differences["recomputed_vs_tracked_11B_max_complex_residual_MVA"] = float(np.abs(residual - old).max())
        suffix = "ref" if label == "AC-reference" else "pred"
        selected_release = RELEASES[0] if label == "AC-reference" else label
        selected = {int(row["bus_id"]): row for row in rows if row["release"] == selected_release}
        old11d = np.array([complex(float(selected[bid]["residual_P_" + suffix]), float(selected[bid]["residual_Q_" + suffix])) for bid in ids])
        differences["recomputed_vs_tracked_11D_max_complex_residual_MVA"] = float(np.abs(residual - old11d).max())
        assert max(differences.values()) < CROSSCHECK_TOL, (label, differences)
        assert abs(evaluated["max_p_residual_mw"] - np.abs(residual.real).max()) < CROSSCHECK_TOL
        assert abs(evaluated["max_q_residual_mvar"] - np.abs(residual.imag).max()) < CROSSCHECK_TOL
        flow_cache[label] = np.r_[sf.real, st.real]
        summary = {"joint_AC_constraints_pass": evaluated["all_tested_constraints_pass"],
                   "P_residual_MW": residual_summary(residual.real, ids),
                   "Q_residual_MVAr": residual_summary(residual.imag, ids), "crosschecks": differences,
                   "Pg_MW": bound_summary(state["pg_mw"], gen[:, 9], gen[:, 8], list(range(1, 70)), 1e-3),
                   "Qg_MVAr": bound_summary(state["qg_mvar"], gen[:, 4], gen[:, 3], list(range(1, 70)), 1e-3),
                   "Vm_pu": bound_summary(state["vm"], bus[:, 12], bus[:, 11], ids, 1e-4),
                   "active_angle_limit_count": 0, "thermal_assessment": "N/A: all original RATE_A are zero",
                   "actual_clipping_counts_and_magnitudes": None,
                   "clipping_note": "Cannot infer actual clipping from state bound activity; pre-clipping activations unavailable."}
        detail = {"artifact_kind": "DERIVED_STATE_POSTPROCESSING", "state_label": label,
                  "original_bus_ids": ids, "signed_P_residual_MW": residual.real.tolist(),
                  "signed_Q_residual_MVAr": residual.imag.tolist(), "independent_evaluator": evaluated,
                  "matrix_crosschecks": differences}
        summary["detail_artifact"] = save_new_or_identical(args.scratch / (label + "-DERIVED-diagnostics.json"), detail)
        if label != "AC-reference":
            summary["FP32_lattice_max_difference"] = {
                key: float(np.abs(np.asarray(state[key]) / scale - (np.asarray(state[key]) / scale).astype(np.float32).astype(np.float64)).max())
                for key, scale in [("vm", 1), ("pg_mw", 100), ("qg_mvar", 100)]}
        all_metrics[label] = summary
    assert all_metrics["AC-reference"]["joint_AC_constraints_pass"]
    assert not any(all_metrics[r]["joint_AC_constraints_pass"] for r in RELEASES)
    slack = next(i for i, row in enumerate(CASE["bus"]) if row[1] == 3)
    reference = states["AC-reference"]
    for label in RELEASES:
        state = states[label]
        all_metrics[label]["approximation_MAE_against_DERIVED_verified_AC_reference"] = {
            **{key: float(np.abs(np.asarray(state[key]) - reference[key]).mean()) for key in ("pg_mw", "qg_mvar", "vm")},
            "reference_aligned_angle_deg": float(np.mean(aligned_angle_errors(state["va_deg"], reference["va_deg"], slack))),
            "both_end_original_AC_Pflow_MW": float(np.abs(flow_cache[label] - flow_cache["AC-reference"]).mean())}
    report = {"status": "PASS", "date_UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "scope": "Original base input only; reconstructed tracked CSV states; no inference, solve, repair or new electrical input.",
              "study_HEAD": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(), "numpy": np.__version__,
              "command": [sys.executable, "-B", "experiments/gsfm018/revalidate_base.py", "--case", str(args.case)],
              "code_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [pathlib.Path(__file__), ROOT / "scripts/python/matpower_case.py", ROOT / "scripts/python/physics_metrics.py"]},
              "input_artifacts": source_records, "derived_state_artifacts": derived_files,
              "raw_artifact_presence_in_current_checkout": {name: (baseline / name).exists() for name in
                  ["input.json", "ac-native.json", "ac-result.json", "microsoft-v1.1-native.json", "newer-base-v2-native.json",
                   "microsoft-v1.1-returned.json", "newer-base-v2-returned.json", "microsoft-v1.1-input.pyg.json", "newer-base-v2-input.pyg.json"]},
              "historical_native_serialization_checks": native_hash_check,
              "duplicate_reference_arrays_exactly_equal_across_two_release_CSV_blocks": True,
              "rounding_assessment": "CSV numeric strings parsed directly to binary64 without intentional rounding; historical native serialization hashes are tested separately. Raw predict dictionaries remain absent.",
              "independent_matrix_method": "Standalone dense complex128 MATPOWER pi stamp, separate from existing stdlib branch checker; no PYPOWER import or solve.",
              "crosscheck_acceptance_MW_MVAr": CROSSCHECK_TOL,
              "fixed_feasibility_tolerances": {"P_Q_balance_MW_MVAr": 1e-3, "Pg_Qg_bounds_MW_MVAr": 1e-3, "Vm_bounds_pu": 1e-4, "active_angle_bounds_deg": 1e-3},
              "metrics": all_metrics,
              "limitations": ["Derivative state recovery is not a new inference or solver run.",
                  "No checkpoint bytes, raw predict dictionaries, original feature tensors, or pre-clipping activations are recovered.",
                  "AC local-optimum status is inherited from historical solver records; this run independently checks physical feasibility only.",
                  "This validates base-state physics, not representation invariance or electrical sensitivity.",
                  "Original angle limits are disabled and thermal assessment is N/A."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(encoded(report))
    print(json.dumps({"status": report["status"], "native_hash_matches": {k: v["exact_historical_native_serialization_hash_match"] for k, v in native_hash_check.items()},
                      "max_crosscheck_MVA": max(max(v["crosschecks"].values()) for v in all_metrics.values()),
                      "joint_AC_feasible": {k: v["joint_AC_constraints_pass"] for k, v in all_metrics.items()}, "report": str(args.output)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=pathlib.Path, required=True, help="Unchanged MATPOWER 8.1 case300.m with pinned SHA")
    parser.add_argument("--scratch", type=pathlib.Path, default=ROOT / "work/base_revalidation")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "results/diagnosis/GSFM-018/20261026-representation-gate/base-revalidation.json")
    main(parser.parse_args())
