"""Final read-only audit of saved GSFM-020 experiments, never a runner.

Run only after the parent declares FINAL_READY. The sole write is a new audit
report. No model, PF or OPF execution is imported or invoked.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import torch

from audit_ac_references import ROOT, OUT, audit_case, physical_check, read, sha

sys.path.insert(0, str(ROOT / "scripts/python"))
from gridsfm_convert import convert

RELEASES = {
    "microsoft-v1.1": ("microsoft", "1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6",
                       "f8a4396122e603e8303afdebe3b093819c0f64dac0878394aed0bd63205fd831"),
    "newer-base-v2": ("newer", "517a07531ea55a11bd81a89a6c6879695a2ba4b4",
                      "9e5333ce0573a3322432cb96c1f62031abc457299a81f66871b10232ba8ea9c7"),
}
TOL = dict(balance_MW_MVAr=1e-3, generator_MW_MVAr=1e-3,
           voltage_pu=1e-4, angle_deg=1e-3, thermal_MVA=1e-3)


def utc(value):
    return dt.datetime.fromisoformat(value).astimezone(dt.timezone.utc)


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and a.shape == b.shape and torch.equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return isinstance(b, (tuple, list)) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def serial(value):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    return value


def close(a, b, tolerance=1e-6):
    assert np.all(np.isfinite(np.asarray(a))), "Non-finite comparison"
    assert np.max(np.abs(np.asarray(a) - np.asarray(b)), initial=0) <= tolerance, (a, b, tolerance)


def check_sources():
    result = {}
    for release, (directory, commit, checkpoint_hash) in RELEASES.items():
        source = ROOT.parent / "runtime/sources" / directory
        files = {p.relative_to(source).as_posix(): sha(p)
                 for p in (source / "model/gridsfm").rglob("*.py")}
        assert subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip() == commit
        assert not subprocess.check_output(["git", "-C", str(source), "diff", "--name-only", commit, "--", "model/gridsfm"], text=True).strip()
        ckpt = ROOT.parent / "runtime/checkpoints" / ("gridsfm_open_v1.1.pt" if release == "microsoft-v1.1" else "gridsfm_open_v2.pt")
        assert sha(ckpt) == checkpoint_hash
        result[release] = dict(source_commit=commit, source_hashes=files,
                               checkpoint_sha256=checkpoint_hash)
    return result


def check_input(d, spec):
    c = read(d / "input.json")
    base = read(OUT / "bases" / str(spec["network"]) / "input.json")
    assert sha(d / "input.json") == spec["input_sha256"]
    assert c["gen"] == base["gen"] and c["gencost"] == base["gencost"]
    assert c["baseMVA"] == base["baseMVA"] == 100
    for key in set(c) - {"bus", "gen", "branch", "gencost"}:
        assert c[key] == base[key]
    differences = [dict(matrix=k, row_1based=i+1, column_1based=j+1, before=x, after=y)
                   for k in ["bus", "gen", "branch", "gencost"]
                   for i, (a, b) in enumerate(zip(base[k], c[k]))
                   for j, (x, y) in enumerate(zip(a, b)) if x != y]
    assert read(d / "field-differences.json") == differences
    for key in ["bus", "gen", "branch", "gencost"]:
        assert len(c[key]) == len(base[key])
        assert all(len(a) == len(b) for a, b in zip(c[key], base[key]))
    for a, b in zip(c["bus"], base["bus"]):
        assert all(x == y for j, (x, y) in enumerate(zip(a, b)) if j not in [2, 3])
    for a, b in zip(c["branch"], base["branch"]):
        assert all(x == y for j, (x, y) in enumerate(zip(a, b)) if j != 4)
        close(a[4], b[4] * spec.get("charging_scale", 1.) if b[4] > 0 else b[4], 1e-12)
    demand = np.array([[b[2], b[3]] for b in base["bus"]], dtype=float)
    for i in range(len(demand)):
        area = (1 if i < 300 else -1) if spec["network"] == 600 else 0
        demand[i, 0] *= spec.get("load_scale", 1.) * spec.get("p_scale", 1.) * (1 + area * spec.get("area_delta", 0.))
        demand[i, 1] *= spec.get("load_scale", 1.) * spec.get("q_scale", 1.) * (1 + area * spec.get("area_delta", 0.))
    if "redistribution" in spec:
        assert spec["network"] == 300
        selection = read(ROOT / "results/comparisons/GSFM-015/20261023-load-location-charging/local-selection.json")
        before = demand.sum(axis=0)
        for group, sign in [("weak_bus_ids", 1), ("strong_bus_ids", -1)]:
            ix = [i for i, b in enumerate(c["bus"]) if b[0] in selection[group]]
            for j, key in enumerate(["transfer_MW", "transfer_MVAr"]):
                old = demand[ix, j].copy()
                demand[ix, j] += sign * spec["redistribution"] * selection[key] * old / old.sum()
        close(demand.sum(axis=0), before, 1e-8)
    close(np.array(c["bus"])[:, 2:4], demand, 1e-10)
    inherited = 411 if spec["network"] == 300 else 822
    assert all(b[5] == 0 for b in c["branch"][:inherited])
    if spec["network"] == 600:
        assert len(c["bus"]) == 600 and len(c["gen"]) == 138 and len(c["branch"]) == 824
        assert all(b[5] == 600 for b in c["branch"][822:])
    else:
        assert len(c["bus"]) == 300 and len(c["gen"]) == 69 and len(c["branch"]) == 411
    signature = hashlib.sha256(json.dumps([c[k] for k in ["bus", "gen", "branch", "gencost"]], separators=(",", ":")).encode()).hexdigest()
    return c, dict(input_sha256=sha(d / "input.json"), field_difference_count=len(differences),
                  fixed_original_order=True, unchanged_except_preregistered_fields=True,
                  electrical_signature=signature)


def residual_details(c, s, sf, st):
    buses = np.array(c["bus"], float); ids = {int(b[0]): i for i, b in enumerate(buses)}
    residual = -buses[:, 2].astype(complex) - 1j * buses[:, 3]
    residual -= (buses[:, 4] - 1j * buses[:, 5]) * np.asarray(s["vm"])**2
    for i, g in enumerate(c["gen"]):
        if g[7] > 0:
            residual[ids[int(g[0])]] += complex(s["pg_mw"][i], s["qg_mvar"][i])
    for i, b in enumerate(c["branch"]):
        residual[ids[int(b[0])]] -= sf[i]
        residual[ids[int(b[1])]] -= st[i]
    result = {}
    for label, arr in [("P", residual.real), ("Q", residual.imag)]:
        a = abs(arr)
        result[label] = dict(mean=float(a.mean()), median=float(np.median(a)),
                             p95=float(np.percentile(a, 95)), max=float(a.max()),
                             violations=int((a > 1e-3).sum()))
    return result


def check_model(d, c, release, sources, summary, code_record, frozen_time, ledger_rec):
    prefix = d / release
    raw = read(str(prefix) + "-returned.json")
    tensors = torch.load(str(prefix) + "-returned.pt", map_location="cpu", weights_only=True)
    assert serial(tensors) == raw
    tensor_metadata = {k: dict(shape=list(v.shape), dtype=str(v.dtype))
                       for k, v in tensors.items() if isinstance(v, torch.Tensor)}
    md = read(str(prefix) + "-metadata.json")
    attempt = read(str(prefix) + "-attempt.json")
    assert md["status"] == attempt["status"] == "PASS"
    assert md["release"] == release and md["order"] == "original" and md["intervention"] == "none"
    assert md["model_input_has_solution"] is False and md["label_poison_control"] is False
    assert md["native_saved_before_evaluation"] is True and md["additional_PF_or_OPF"] is False
    assert md["clip_mode"] == "clamp" and md["leaky_alpha"] == 0
    assert md["versions"]["seed"] == 0 and md["versions"]["torch_threads"] == 4
    assert md["input_sha256"] == attempt["input_sha256"] == sha(d / "input.json")
    assert md["source_commit"] == sources[release]["source_commit"]
    assert md["source_hashes"] == sources[release]["source_hashes"]
    assert md["checkpoint_sha256"] == sources[release]["checkpoint_sha256"]
    assert md["worker_sha256"] == code_record["files"]["experiments/gsfm020/model_worker.py"]
    started = dt.datetime.fromtimestamp(attempt["started_unix"], dt.timezone.utc)
    assert frozen_time <= utc(ledger_rec["attempted_UTC"]) <= started <= utc(ledger_rec["completed_UTC"])
    obj = convert(c)
    if release == "newer-base-v2":
        for rows in obj["grid"]["nodes"].values():
            for row in rows:
                row.append(1.)
        for family in ["ac_line", "transformer"]:
            for row in obj["grid"]["edges"][family]["features"]:
                row.append(1.)
    actual_obj = read(str(prefix) + "-input.pyg.json")
    assert actual_obj == obj and "solution" not in actual_obj
    mp = md["mapping"]
    assert mp == obj["metadata"]
    assert mp["bus_source_rows"] == list(range(len(c["bus"])))
    active = [i for i, g in enumerate(c["gen"]) if g[7] > 0]
    assert mp["gen_source_rows"] == active
    assert sorted(mp["ac_line_source_rows"] + mp["transformer_source_rows"]) == [i for i, b in enumerate(c["branch"]) if b[10] > 0]
    assert len(raw["Pg"]) == len(raw["Qg"]) == len(active)
    assert len(raw["V"]) == len(raw["theta"]) == len(c["bus"])
    expected = dict(vm=raw["V"], va_deg=[math.degrees(v) for v in raw["theta"]],
                    pg_mw=[0.] * len(c["gen"]), qg_mvar=[0.] * len(c["gen"]))
    for source, target in [("Pg", "pg_mw"), ("Qg", "qg_mvar")]:
        for i, v in zip(active, raw[source]):
            expected[target][i] = v * c["baseMVA"]
    native = read(str(prefix) + "-native.json")
    assert native == expected
    prepared_default = torch.load(str(prefix) + "-prepared-default.pt", map_location="cpu", weights_only=True)
    prepared_used = torch.load(str(prefix) + "-prepared-used.pt", map_location="cpu", weights_only=True)
    assert same(prepared_default, prepared_used), "Electrical case used altered prepared features"
    assert sha(str(prefix) + "-prepared-default.pt") == md["prepared_default_sha256"]
    assert sha(str(prefix) + "-prepared-used.pt") == md["prepared_used_sha256"]
    saved_clips = {x["variable"]: x for x in read(d / "clipping-summary.json") if x["method"] == release}
    captures = read(str(prefix) + "-clamps.json")["captures"]
    assert [x["variable"] for x in captures] == ["Pg", "Qg", "V"]
    for cap in captures:
        v = cap["variable"]; a, z, lo, hi = (np.asarray(cap[k]) for k in ["input", "output", "lo", "hi"])
        assert all(np.isfinite(x).all() for x in [a, z, lo, hi])
        assert np.array_equal(np.clip(a, lo, hi), z) and cap["output"] == raw[v]
        if v == "V":
            bounds = np.asarray([[b[12], b[11]] for b in c["bus"]], np.float32)
            scale, tolerance = 1., 1e-4
            locations = [int(b[0]) for b in c["bus"]]
        else:
            lower, upper = (9, 8) if v == "Pg" else (4, 3)
            bounds = np.asarray([[c["gen"][i][lower]/c["baseMVA"], c["gen"][i][upper]/c["baseMVA"]] for i in active], np.float32)
            scale, tolerance = c["baseMVA"], 1e-3
            locations = [i+1 for i in active]
        assert np.array_equal(lo, bounds[:, 0]) and np.array_equal(hi, bounds[:, 1])
        saved = saved_clips[v]
        assert saved["strict_count"] == int((a != z).sum())
        assert saved["material_count"] == int((abs(a-z)*scale > tolerance).sum())
        assert saved["strict_locations"] == [locations[i] for i in range(len(a)) if a[i] != z[i]]
        assert saved["material_locations"] == [locations[i] for i in range(len(a)) if abs(a[i]-z[i])*scale > tolerance]
        assert saved["lower_count"] == int((a < lo).sum()) and saved["upper_count"] == int((a > hi).sum())
        close(saved["max_change"], float(max(abs(a-z)*scale)), 1e-9)
    metrics, sf, st = physical_check(c, native)
    details = residual_details(c, native, sf, st)
    assert summary["AC_joint_feasible"] == metrics["joint_pass"]
    for label in ["P", "Q"]:
        for stat in ["mean", "median", "p95", "max"]:
            close(summary[label][stat], details[label][stat], 1e-6)
        assert summary[label+"_violating_buses"] == details[label]["violations"]
    for saved, actual in [("Pg_max_excess", "Pg_excess_MW"), ("Qg_max_excess", "Qg_excess_MVAr"),
                           ("Vm_max_excess", "Vm_excess_pu"), ("angle_max_excess_deg", "angle_excess_deg")]:
        close(summary[saved], metrics[actual], 1e-9)
    assert summary["rated_online_branch_count"] == metrics["rated_branches"]
    if metrics["thermal_excess_MVA"] is None:
        assert summary["thermal_max_excess_MVA_or_DC_MW"] is None
    else:
        close(summary["thermal_max_excess_MVA_or_DC_MW"], metrics["thermal_excess_MVA"], 1e-6)
    return dict(status="PASS", raw_tensors_equal_json=True, native_mapping_exact=True,
                shipped_features_unaltered=True, observed_clamps_exact=True,
                started_UTC=started.isoformat(), raw_return_sha256=sha(str(prefix)+"-returned.pt"),
                raw_tensor_metadata=tensor_metadata, physics=metrics)


def check_dc(d, c, summary):
    if not (d / "dc-native.json").exists():
        failure = read(d / "dc-failure.json")
        assert failure["status"] == "FAILED_UNKNOWN"
        assert summary["status"] == "FAILED_UNKNOWN" and summary["approximation"] is None
        return dict(status="PASS", outcome="UNKNOWN_NO_RETURNED_DC_POINT",
                    failure_preserved=True, own_equations_pass=None,
                    Qg_Vm_joint_AC_NA=True)
    native = read(d / "dc-native.json"); raw = read(d / "dc-raw.json"); status = read(d / "dc-status.json")
    adapter = read(d / "dc-input-adapter-audit.json")
    assert adapter["status"] == "PASS" and adapter["original_all_fields_and_branch_angles_preserved"] is True
    assert native["qg_mvar"] is None and native["vm"] is None
    assert summary["Q"] is None and summary["AC_joint_feasible"] is None
    for key, expected in dict(OPF_ALG_DC=200, PDIPM_MAX_IT=150, PDIPM_FEASTOL=1e-10,
                              PDIPM_GRADTOL=1e-9, PDIPM_COMPTOL=1e-9, COST_MULT=1.).items():
        assert status["options"][key] == expected
    buses = np.asarray(c["bus"], float); gen = np.asarray(c["gen"], float); branches = np.asarray(c["branch"], float)
    rb, rg, re = (np.asarray(raw[k], float) for k in ["bus", "gen", "branch"])
    assert np.array_equal(rb[:, 0], buses[:, 0]) and np.array_equal(rg[:, 0], gen[:, 0])
    assert np.array_equal(re[:, :13], branches) and raw["gencost"] == c["gencost"]
    assert np.array_equal(rg[:, 1], native["pg_mw"]) and np.array_equal(rb[:, 8], native["va_deg"])
    for col in [1, 2, 3, 4, 5, 6, 9, 10, 11, 12]:
        assert np.array_equal(rb[:, col], buses[:, col])
    for col in [3, 4, 5, 6, 7, 8, 9]:
        assert np.array_equal(rg[:, col], gen[:, col])
    ids = {int(b[0]): i for i, b in enumerate(buses)}
    angles = np.asarray(native["va_deg"]); pg = np.asarray(native["pg_mw"])
    residual = -buses[:, 2] - buses[:, 4]
    for i, g in enumerate(gen):
        if g[7] > 0:
            residual[ids[int(g[0])]] += pg[i]
    flows, angle_excess, thermal_excess = [], [], []
    for b in branches:
        i, j = ids[int(b[0])], ids[int(b[1])]
        flow = c["baseMVA"] * b[10] / (b[3] * (b[8] or 1.)) * math.radians(angles[i]-angles[j]-b[9])
        flows.append(flow); residual[i] -= flow; residual[j] += flow
        if b[10] > 0:
            if b[5] > 0:
                thermal_excess.append(abs(flow)-b[5])
            if b[11] > -360:
                angle_excess.append(b[11]-(angles[i]-angles[j]))
            if b[12] < 360:
                angle_excess.append(angles[i]-angles[j]-b[12])
    close(flows, native["pf_mw"]); close(-np.asarray(flows), native["pt_mw"])
    close(flows, re[:, 13]); close(-np.asarray(flows), re[:, 15])
    active = gen[:, 7] > 0
    pgex = max(0., np.max(gen[active, 9]-pg[active]), np.max(pg[active]-gen[active, 8]))
    own_pass = bool(max(abs(residual)) <= 1e-3 and pgex <= 1e-3 and max([0.]+angle_excess) <= 1e-3 and max([0.]+thermal_excess) <= 1e-3)
    assert status["independent_DC_constraints_pass"] == summary["native_DC_constraints_pass"] == own_pass
    assert bool(raw["success"]) == status["solver_success"]
    assert status["status"] == ("CONVERGED" if raw["success"] else "FAILED_UNKNOWN")
    if raw["success"]:
        assert own_pass
    close(summary["P"]["max"], max(abs(residual)))
    assert summary["P_violating_buses"] == int((abs(residual)>1e-3).sum())
    objective = sum(float(np.polyval(row[4:4+int(row[3])], val)) for row, val in zip(c["gencost"], pg))
    close(objective, status["objective"], 1e-4); close(objective, raw["f"], 1e-4)
    return dict(status="PASS", own_equations_pass=own_pass,
                solver_success=bool(raw["success"]), maximum_P_residual_MW=float(max(abs(residual))),
                Pg_excess_MW=float(pgex), thermal_excess_DC_MW=float(max([0.]+thermal_excess)) if thermal_excess else None,
                Qg_Vm_joint_AC_NA=True, input_fields_preserved=True)


def main():
    p = argparse.ArgumentParser(); p.add_argument("--out", type=Path, default=OUT / "final-verification.json")
    p.add_argument("--expected-discovery", type=int, default=20); p.add_argument("--expected-confirmation", type=int, default=6)
    args = p.parse_args(); assert not args.out.exists(), "Preserve prior verification; choose a new output"
    started = dt.datetime.now(dt.timezone.utc)
    ledger = read(OUT / "ledger.json"); records = ledger["attempted"]
    start, deadline, compute_stop = (utc(ledger[k]) for k in ["start_UTC", "deadline_UTC", "compute_stop_UTC"])
    assert deadline-start == dt.timedelta(hours=5) and start < compute_stop < deadline
    assert started < deadline
    assert ledger["discovery_limit"] == 24 and ledger["confirmation_limit"] == 6
    assert len(records) == len({x["id"] for x in records})
    counts = {kind: sum(x["kind"] == kind for x in records) for kind in ["discovery", "confirmation"]}
    assert counts == dict(discovery=args.expected_discovery, confirmation=args.expected_confirmation)
    assert counts["discovery"] <= 24 and counts["confirmation"] <= 6
    for rec in records:
        assert rec["status"] == "COMPLETE"
        assert start <= utc(rec["attempted_UTC"]) < compute_stop
        assert utc(rec["attempted_UTC"]) <= utc(rec["completed_UTC"]) <= deadline
    plans, specifications = {}, {}
    last_discovery = max(utc(x["completed_UTC"]) for x in records if x["kind"] == "discovery")
    confirmation_checks = []
    for path in sorted((OUT / "batches").glob("*/plan.json")):
        plan = read(path); verify = read(path.parent / "verification.json")
        assert verify["status"] == "COMPLETE" and verify["plan_sha256"] == sha(path)
        assert 4 <= len(plan["scenarios"]) <= 6
        assert verify["scenarios"] == len(plan["scenarios"])
        assert all(plan.get(k) for k in ["hypothesis", "motivation", "paired_baseline", "expected_AC", "expected_DC"])
        plans[plan["batch"]] = plan
        freeze = utc(plan["frozen_UTC"])
        group = [x for x in records if x["batch"] == plan["batch"]]
        assert {x["id"] for x in group} == {x["id"] for x in plan["scenarios"]}
        assert all(x["kind"] == plan["kind"] and freeze <= utc(x["attempted_UTC"]) for x in group)
        if plan["kind"] == "confirmation":
            assert last_discovery < freeze
            confirmation_checks.append(dict(batch=plan["batch"], frozen_UTC=plan["frozen_UTC"],
                latest_discovery_completion_UTC=last_discovery.isoformat(),
                first_confirmation_attempt_UTC=min(x["attempted_UTC"] for x in group), plan_sha256=sha(path)))
        for spec in plan["scenarios"]:
            assert spec["id"] not in specifications
            specifications[spec["id"]] = spec
    assert set(specifications) == {x["id"] for x in records}
    assert {d.name for d in (OUT / "cases").iterdir() if (d / "input.json").exists()} == set(specifications)
    prior = read(OUT / "prior-tracked-sha256.json"); assert len(prior) == 929
    assert all((ROOT / name).is_file() and sha(ROOT / name) == expected for name, expected in prior.items())
    sources = check_sources()
    diagnostic = read(OUT / "diagnostic-gate.json")
    assert diagnostic["status"] == "PASS"
    diagnostic_actual = sum(x["actual_neural_forwards"] for x in ledger["diagnostic_forwards"])
    diagnostic_invocations = sum(x["invocations_including_preprocessing_failure"] for x in ledger["diagnostic_forwards"])
    diagnostic_failed = sum(x["failed_preprocessing_attempts"] for x in ledger["diagnostic_forwards"])
    assert diagnostic["executed_neural_forwards"] == diagnostic_actual
    assert diagnostic_actual <= ledger["diagnostic_forward_limit"] == 20
    assert diagnostic_invocations == diagnostic_actual + diagnostic_failed
    result_cases, signatures = [], set()
    for rec in records:
        d = OUT / "cases" / rec["id"]
        case, input_audit = check_input(d, specifications[rec["id"]])
        assert input_audit["electrical_signature"] not in signatures
        signatures.add(input_audit["electrical_signature"])
        status = read(d / "run-status.json"); code = read(d / "code-at-execution.json")
        code["files"] = {name.replace("\\", "/"): value for name, value in code["files"].items()}
        assert status["scenario"] == rec["id"] and set(status["models"]) == set(RELEASES)
        assert status["DC"]["returncode"] == 0 and len(status["AC"]) in [1, 2]
        assert all(x["returncode"] == 0 for x in status["models"].values())
        assert utc(rec["attempted_UTC"]) <= utc(code["clock_UTC"]) <= utc(rec["completed_UTC"])
        assert code["files"]["experiments/gsfm020/solver_server.jl"] == "b50e340f06a0c3cd0562fa64d053b762940ff05725caa513b6ec546dd06adf4e"
        rows = {x["method"]: x for x in read(d / "summary.json")}
        assert set(rows) == {"AC-OPF", "DC-OPF", *RELEASES}
        ac = audit_case(d)
        assert rec["reference_valid"] == ac["reference_accepted"]
        assert (d / "ac-native.json").exists() == ac["reference_accepted"]
        assert all(x["reference_valid"] == ac["reference_accepted"] for x in rows.values())
        if not ac["reference_accepted"]:
            assert all(x["approximation"] is None for x in rows.values())
            assert read(d / "ac-status.json")["feasibility"] == "UNKNOWN"
        for key in ["Qg_per_generator_MVAr", "Qg_bus_aggregate_MVAr", "Vm_pu", "branch_Q_MVAr"]:
            if rows["DC-OPF"]["approximation"] is not None:
                assert rows["DC-OPF"]["approximation"][key] is None
        freeze = utc(plans[rec["batch"]]["frozen_UTC"])
        models = {release: check_model(d, case, release, sources, rows[release], code, freeze, rec) for release in RELEASES}
        dc = check_dc(d, case, rows["DC-OPF"])
        result_cases.append(dict(scenario=rec["id"], kind=rec["kind"], status="PASS", input=input_audit,
                                 all_four_methods_attempted=True, AC=ac, DC=dc, models=models))
        print("AUDITED", rec["id"], flush=True)
    completed = dt.datetime.now(dt.timezone.utc)
    assert completed <= deadline
    result = dict(status="PASS", started_UTC=started.isoformat(), completed_UTC=completed.isoformat(),
        scope="Read-only saved-artifact verification; zero model forwards, PF calls or OPF solves",
        counts=counts, input_limit=30, wall_clock_limit_hours=5, deadline_UTC=ledger["deadline_UTC"],
        fixed_tolerances=TOL, prior_tracked_files_preserved=len(prior), unique_electrical_inputs=len(signatures),
        confirmation_preregistration_checks=confirmation_checks,
        preregistration_evidence="Saved plan hashes, frozen timestamps, ledger attempts and model attempt timestamps agree; no external timestamp notarization is claimed.",
        diagnostic_actual_neural_forwards=diagnostic_actual,
        diagnostic_worker_invocations=diagnostic_invocations, diagnostic_pre_forward_failures=diagnostic_failed,
        diagnostic_limit_note="The 20-forward gate counts actual neural forwards. Pre-forward preprocessing failures are reported separately and preserved; total worker invocations are not relabelled as forwards.",
        release_identity=sources, cases=result_cases)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", cases=len(result_cases), counts=counts, prior_files=len(prior), output=str(args.out))))


if __name__ == "__main__":
    main()
