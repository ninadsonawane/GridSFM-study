"""Extract saved original-case300 evidence only. Never solve or run a model.

Run from any directory: python -B experiments/gsfm018/summarize_existing.py
Requires matplotlib only for the figure. Existing scientific artifacts are read-only.
Missing values remain blank/null; original summaries are retained in the JSON.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "results/diagnosis/GSFM-018/20261026-representation-gate"
DIRS = {
    "11C-1": "results/comparisons/GSFM-011C-1/20261022-loading-only",
    "15": "results/comparisons/GSFM-015/20261023-load-location-charging",
    "16": "results/comparisons/GSFM-016/20261024-electrical-mechanisms",
    "17": "results/comparisons/GSFM-017/20261026-increased-charging",
}
METHODS = ["AC-OPF", "DC-OPF", "microsoft-v1.1", "newer-base-v2"]
NAMES = {"Microsoft v1.1": "microsoft-v1.1", "Newer v2": "newer-base-v2"}
SOURCES = {}


def read(rel):
    path = ROOT / rel
    SOURCES[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(rel):
    path = ROOT / rel
    SOURCES[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def scalar(value):
    if value == "":
        return None
    if isinstance(value, str):
        try:
            return float(value) if "." in value or "e" in value.lower() else int(value)
        except ValueError:
            return value
    return value


def flatten(value, prefix=""):
    out = {}
    for key, val in value.items():
        name = f"{prefix}{key}"
        if isinstance(val, dict):
            out.update(flatten(val, name + "."))
        elif isinstance(val, list):
            out[name] = json.dumps(val, separators=(",", ":"))
        else:
            out[name] = val
    return out


def write_csv(path, rows):
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def extract():
    manifests = {}
    for experiment, filename in [("15", "all-scenarios.json"), ("16", "scenario-manifest.json"), ("17", "scenario-manifest.json")]:
        rel = f"{DIRS[experiment]}/{filename}"
        for entry in read(rel)["scenarios"]:
            manifests[(experiment, entry["id"])] = {**entry, "manifest_source": rel}
    records, inputs = [], []

    def add_input(experiment, scenario, meta, native_rows, source, reused_from=None):
        ac = next(x for x in native_rows if x["method"] == "AC-OPF")
        dc = next(x for x in native_rows if x["method"] == "DC-OPF")
        row = {
            "record_id": f"{experiment}:{scenario}", "experiment": experiment,
            "scenario": scenario, "input_sha256": meta["input_sha256"],
            "family": meta.get("family", "global"), "loading": meta.get("load_scale"),
            "positive_charging_factor": meta.get("positive_charging_factor"),
            "baseline": meta.get("baseline"), "changes": meta.get("changes"),
            "representation_control": scenario.startswith("REP-"),
            "reused_native_source": reused_from,
            "AC_reference_valid": ac["reference_valid"],
            "AC_status": "VERIFIED_LOCAL_REFERENCE" if ac["reference_valid"] else "UNKNOWN",
            "DC_own_constraints_pass": dc.get("native_DC_constraints_pass"),
            "Microsoft_joint_AC_feasible": next(x for x in native_rows if x["method"] == METHODS[2])["AC_joint_feasible"],
            "v2_joint_AC_feasible": next(x for x in native_rows if x["method"] == METHODS[3])["AC_joint_feasible"],
            "thermal_assessment": "N/A: original RATE_A all zero", "source": source,
            "manifest_source": meta.get("manifest_source"),
        }
        inputs.append(row)
        for native in native_rows:
            records.append({"input_record": row.copy(), "metrics": native})

    # Preserve the earlier seven loading records, including reused 100% baseline.
    directory = DIRS["11C-1"]
    protocol = read(f"{directory}/frozen-protocol.json")
    by_scale = {x["scale"]: x for x in protocol["inputs"]}
    by_scale[1.0] = manifests[("15", "G300-1.00")]
    approx = {(x["loading"], x["method"]): x for x in read(f"{directory}/approximation.json")}
    physical = read(f"{directory}/physical-validity.json")
    worst = read(f"{directory}/worst-locations.json")
    for scale in sorted(by_scale):
        group = []
        pgroup = [x for x in physical if x["loading"] == scale]
        reference_valid = next(x for x in pgroup if x["method"] == "AC-OPF")["AC_feasibility"]
        for p in pgroup:
            a = approx[(scale, p["method"])]
            amap = {"Pg_MW": "Pg_per_generator_MW", "Qg_MVAr": "Qg_per_generator_MVAr", "Vm_pu": "Vm_pu", "aligned_angle_deg": "aligned_angle_deg", "active_branch_flow_MW_both_ends": "branch_P_MW"}
            metrics = {
                "method": NAMES.get(p["method"], p["method"]), "reference_valid": reference_valid,
                "AC_joint_feasible": p["AC_feasibility"],
                "native_DC_constraints_pass": p.get("native_DC_constraints_pass"),
                "P": {"max": p["max_P_imbalance_MW"]},
                "Q": {"max": p["max_Q_imbalance_MVAr"]} if p["max_Q_imbalance_MVAr"] is not None else None,
                "Pg_max_excess": p.get("max_Pg_violation_MW"),
                "Qg_max_excess": p.get("max_Qg_violation_MVAr"),
                "Vm_max_excess": p.get("max_Vm_violation_pu"),
                "angle_max_excess_deg": p.get("max_angle_difference_violation_deg"),
                "objective_raw_original_units": p.get("dispatch_cost_per_hour"),
                "approximation": {dst: ({"mean": a[src]["MAE"], "max": a[src]["maximum"], "RMSE": a[src]["RMSE"]} if isinstance(a.get(src), dict) else None) for src, dst in amap.items()},
                "worst_locations": worst[str(scale)][p["method"]],
                "source_physical": p, "source_approximation": a,
                "unavailable_in_compact_11C": "P/Q mean/median/p95/counts and exact clipping records; not inferred",
            }
            group.append(metrics)
        meta = {**by_scale[scale], "load_scale": scale, "family": "global", "manifest_source": by_scale[scale].get("manifest_source", f"{directory}/frozen-protocol.json")}
        add_input("11C-1", f"load-{scale:.2f}", meta, group, f"{directory}/physical-validity.json", "GSFM-011B base" if scale == 1.0 else None)

    for experiment in ["15", "16", "17"]:
        directory = DIRS[experiment]
        source = f"{directory}/method-summary.json"
        summary = read(source)
        clips = read_csv(f"{directory}/clipping-summary.csv")
        grouped = defaultdict(list)
        for original in summary:
            x = dict(original)
            if experiment == "17":
                scenario = {"50%": "C300-L0.90-B0.50", "100%": "G300-0.90", "150%": "C300-L0.90-B1.50"}[x["charging"]]
            else:
                scenario = x["scenario"]
                # R300-base and RATE80-300 are complete published PGLib cases.
                if str(x.get("network")) != "300" or scenario in ["R300-base", "RATE80-300"]:
                    continue
            x["clipping"] = {}
            for c in clips:
                matches = c.get("charging") == x.get("charging") if experiment == "17" else c.get("scenario") == scenario
                if matches and c["method"] == x["method"]:
                    aliases = {
                        "strict_count": "strict_clipped_count",
                        "meaningful_count": "physically_meaningful_clipped_count",
                        "clipped_above_physical_tolerance_count": "physically_meaningful_clipped_count",
                        "lower_count": "lower_clipped_count", "upper_count": "upper_clipped_count",
                    }
                    variable = "Vm" if c["variable"] == "V" else c["variable"]
                    x["clipping"][variable] = {aliases.get(k, k): scalar(v) for k, v in c.items() if k not in ["charging", "scenario", "family", "network", "method", "variable"]}
                    x["clipping"][variable]["source"] = f"{directory}/clipping-summary.csv"
            grouped[scenario].append(x)
        for scenario, group in grouped.items():
            meta = manifests.get((experiment, scenario), manifests.get(("15", scenario)))
            if meta is None:
                raise ValueError(f"Missing manifest: {experiment} {scenario}")
            reused = meta.get("reused_from")
            if experiment == "16" and ("16", scenario) not in manifests:
                reused = f"15:{scenario}"
            if experiment == "17" and scenario != "C300-L0.90-B1.50":
                reused = f"15:{scenario}"
            add_input(experiment, scenario, meta, group, source, reused)

    first = {}
    for row in inputs:
        sha = row["input_sha256"]
        row["same_bytes_first_record"] = first.setdefault(sha, row["record_id"])
        row["duplicate_input_bytes"] = row["same_bytes_first_record"] != row["record_id"]
    by_id = {x["record_id"]: x for x in inputs}
    for rec in records:
        rec["input_record"] = by_id[rec["input_record"]["record_id"]]
    # 17 republishes 15's two unchanged native points but omits magnitudes
    # in its compact CSV. Recover only those saved matching-input metrics.
    richer = {(r["input_record"]["input_sha256"], r["metrics"]["method"]): r["metrics"].get("clipping", {}) for r in records if r["input_record"]["experiment"] == "15"}
    for rec in records:
        info, metrics = rec["input_record"], rec["metrics"]
        if info["experiment"] != "17":
            continue
        prior = richer.get((info["input_sha256"], metrics["method"]), {})
        for variable, clip in metrics.get("clipping", {}).items():
            saved = prior.get(variable)
            if saved:
                assert clip["strict_clipped_count"] == saved["strict_clipped_count"]
                assert clip["physically_meaningful_clipped_count"] == saved["physically_meaningful_clipped_count"]
                for field in ["max_abs_change", "sum_abs_change"]:
                    clip[field] = saved[field]
                clip["magnitude_source"] = saved["source"]
    # Include exact saved conventional null controls; do not infer identity
    # merely from matching scalar residuals or from the DC model definition.
    null_rel = f"{DIRS['16']}/DC-null-controls.json"
    nulls = {x["scenario"]: x for x in read(null_rel)}
    charge_rel = f"{DIRS['15']}/DC-charging-invariance.json"
    charge_nulls = {x["scenario"]: x for x in read(charge_rel)}
    verify17_rel = f"{DIRS['17']}/verification.json"
    verify17 = read(verify17_rel)
    for rec in records:
        info, metrics = rec["input_record"], rec["metrics"]
        if metrics["method"] != "DC-OPF":
            continue
        scenario = info["scenario"]
        if scenario in nulls:
            metrics["saved_state_invariance_control"] = {**nulls[scenario], "source": null_rel}
        elif scenario in charge_nulls:
            metrics["saved_state_invariance_control"] = {**charge_nulls[scenario], "source": charge_rel}
        elif scenario == "C300-L0.90-B1.50":
            metrics["saved_state_invariance_control"] = {"native_exactly_unchanged_vs_100pct_charging": verify17["DC_native_exactly_unchanged_vs100pct_charging"], "source": verify17_rel}
    return inputs, records


def artifact_availability():
    audits = []
    for experiment, directory in DIRS.items():
        rel = f"{directory}/{'artifact-sha256.json' if experiment == '17' else 'artifact-inventory.json'}"
        data = read(rel)
        if experiment == "11C-1":
            files = [{"path": f"{directory}/{k}", **v} for k, v in data.items()]
        else:
            files = data if isinstance(data, list) else data["files"]
        missing = [x for x in files if not (ROOT / x["path"]).is_file()]
        present = [x for x in files if (ROOT / x["path"]).is_file()]
        mismatch = [x["path"] for x in present if hashlib.sha256((ROOT/x["path"]).read_bytes()).hexdigest() != x["sha256"]]
        audits.append({"experiment": experiment, "inventory_source": rel, "scope": "whole historical run, including out-of-scope 600/PGLib files when present", "inventory_count": len(files), "present_count": len(present), "missing_count": len(missing), "missing_marked_local_only": sum(x.get("local_only", False) for x in missing), "present_hash_mismatches": mismatch, "missing_paths": [x["path"] for x in missing]})
    return audits


def mean(row, key):
    block = (row.get("approximation") or {}).get(key)
    return block.get("mean") if isinstance(block, dict) else None


def fmt(x):
    return "N/A" if x is None else (f"{x:.5f}" if abs(x) < 0.1 and x else f"{x:,.2f}")


def pair_text(records):
    index = {(r["input_record"]["experiment"], r["input_record"]["scenario"], r["metrics"]["method"]): r["metrics"] for r in records}
    pairs = [
        ("Global loading 100% to 106%", "16", "G300-1.00", "16", "G300-1.06", "Higher demand requires more generation; losses/reactive limits can alter dispatch.", "v2 maximum worsens while mean/median/p95 improve: localized tail change, not uniformly worse balance."),
        ("P-only +10%", "16", "G300-1.00", "16", "P10-300", "Higher active generation and cost expected; Q response depends on losses/voltage.", "v2 Pg improves and max P/Q worsen, but mean/p95 Q improve. One screened level."),
        ("Q-only +10%", "16", "G300-1.00", "16", "Q10-300", "More reactive demand can change AC voltage/dispatch; standard DC state is invariant.", "v2 Pg improves slightly while mean/p95/max Q worsen; the DC error change is a changed-reference effect."),
        ("Fixed-total transfer to low-admittance group", "16", "G300-1.00", "16", "L300-weak", "Totals fixed; location changes losses, voltage and dispatch. Admittance is only a proxy.", "Strongest saved multi-metric v2 deterioration, nearly unchanged Pg MAE; no causal weak-grid proof or nearby confirmation."),
        ("Opposite fixed-total transfer", "16", "G300-1.00", "16", "L300-strong", "Same transfer magnitude reversed; electrical response need not be symmetric.", "v2 mean Q improves slightly while maximum and p95 worsen; counterexample to a single severity ranking."),
        ("Charging 100% to 150%, load90%", "17", "G300-0.90", "17", "C300-L0.90-B1.50", "Positive charging supplies reactive power; Qg demand can fall and lower bounds may activate. DC ignores charging.", "Both Qg/Vm errors worsen; v2 max Q improves slightly but mean worsens. This is a synthetic parameter intervention."),
        ("Charging 100% to 50%, load90%", "17", "G300-0.90", "17", "C300-L0.90-B0.50", "Less reactive support can raise Qg and upper-bound activity; DC unchanged.", "Both Qg errors worsen, but v1.1 max/mean Q improve. Severity is not reference accuracy."),
        ("Charging 100% to 0%, load90%", "16", "G300-0.90", "16", "C300-L0.90-B0.00", "Removed positive charging may stress AC reactive support; solver failure is not infeasibility proof.", "AC UNKNOWN; all reference-dependent errors N/A. Native residual comparisons remain reference-free."),
        ("Charging 100% to 50%, load106%", "16", "G300-1.06", "16", "C300-L1.06-B0.50", "Less reactive support at higher demand may increase constraint activity.", "AC UNKNOWN; lower maximum residuals do not demonstrate better accuracy or a feasible native state."),
        ("Charging 100% to 0%, load106%", "16", "G300-1.06", "16", "C300-L1.06-B0.00", "Less reactive support at higher demand may increase constraint activity.", "AC UNKNOWN; same reference limitation, complete failure retained."),
    ]
    lines = ["# Saved original-case300 paired evidence", "", "No new solves/inference. Numeric arrows describe error (MAE), absolute balance severity, clipping counts, or the explicitly named physical quantity. References are previously validated feasible local optima, not global certificates. All native model points fail joint AC feasibility. Original-case thermal assessment is N/A. Representation controls remain a separate correctness limitation.", "", "| Intervention / baseline | Expected conventional response | Saved AC reference response | DC response | Microsoft v1.1 accuracy / balance / clipping | Base v2 accuracy / balance / clipping | Interpretation and confidence |", "|---|---|---|---|---|---|---|"]

    def arrow(a, b):
        return fmt(a) + " → " + fmt(b)

    def model(a, b):
        clips = []
        magnitudes = []
        for variable in ["Pg", "Qg", "Vm"]:
            ca, cb = a.get("clipping", {}).get(variable, {}), b.get("clipping", {}).get(variable, {})
            clips.append(f"{variable} {ca.get('strict_clipped_count', 'N/A')}→{cb.get('strict_clipped_count', 'N/A')} (material {ca.get('physically_meaningful_clipped_count', 'N/A')}→{cb.get('physically_meaningful_clipped_count', 'N/A')})")
            magnitudes.append(f"{variable} " + arrow(ca.get("max_abs_change"), cb.get("max_abs_change")))
        return "; ".join([
            "Pg MAE MW " + arrow(mean(a, "Pg_per_generator_MW"), mean(b, "Pg_per_generator_MW")),
            "Qg MAE MVAr " + arrow(mean(a, "Qg_per_generator_MVAr"), mean(b, "Qg_per_generator_MVAr")),
            "Vm MAE pu " + arrow(mean(a, "Vm_pu"), mean(b, "Vm_pu")),
            "max Q MVAr " + arrow(a["Q"]["max"], b["Q"]["max"]),
            "mean / p95 Q MVAr " + arrow(a["Q"]["mean"], b["Q"]["mean"]) + " / " + arrow(a["Q"]["p95"], b["Q"]["p95"]),
            "P/Q count " + f"{a['P_violating_buses']}/{a['Q_violating_buses']}→{b['P_violating_buses']}/{b['Q_violating_buses']}",
            "strict clips " + ", ".join(clips),
            "max clamp magnitude (MW/MVAr/pu) " + ", ".join(magnitudes),
        ])

    for label, e0, s0, e1, s1, expected, interpretation in pairs:
        rows = {m: (index[(e0, s0, m)], index[(e1, s1, m)]) for m in METHODS}
        a, b = rows["AC-OPF"]
        ac = ("PASS" if a["reference_valid"] else "UNKNOWN") + "→" + ("PASS" if b["reference_valid"] else "UNKNOWN")
        if b["reference_valid"]:
            ac += "; active Q bounds " + arrow(a.get("Qg_at_bound_count"), b.get("Qg_at_bound_count"))
        else:
            ac += "; failed-iterate bound counts omitted from physical response; full diagnostic retained in CSV"
        if "total_Qg_MVAr" in a:
            ac += "; total Qg MVAr " + arrow(a["total_Qg_MVAr"], b["total_Qg_MVAr"])
            ac += "; Q lower/upper " + f"{a['Qg_at_lower_count']}/{a['Qg_at_upper_count']}→{b['Qg_at_lower_count']}/{b['Qg_at_upper_count']}"
        elif a.get("objective_raw_original_units") is not None and b.get("objective_raw_original_units") is not None and b["reference_valid"]:
            ac += "; objective " + arrow(a["objective_raw_original_units"], b["objective_raw_original_units"])
        a, b = rows["DC-OPF"]
        dc = "Own-law PASS→PASS; Pg MAE MW " + arrow(mean(a, "Pg_per_generator_MW"), mean(b, "Pg_per_generator_MW"))
        dc += "; flow MAE MW " + arrow(mean(a, "branch_P_MW"), mean(b, "branch_P_MW"))
        if b.get("saved_state_invariance_control"):
            dc += "; native DC state/flows exactly unchanged (saved control)"
            if a["reference_valid"] and b["reference_valid"]:
                dc += "; changed errors come from changed AC reference"
            else:
                dc += "; target reference errors N/A because AC outcome UNKNOWN"
        lines.append("| " + " | ".join([label + f" ({s0}→{s1})", expected, ac, dc, model(*rows[METHODS[2]]), model(*rows[METHODS[3]]), interpretation + " Confidence: descriptive saved-state association only."]) + " |")
    lines += ["", "Exact source rows and all saved metrics are retained in existing-evidence.json and existing-methods.csv. Clipping magnitudes are included where published by 15/16; the two unchanged points reused in 17 inherit their saved 15 magnitudes with source paths and matching-count checks. The new 150% point has published counts only, so its magnitude remains N/A. Strict events can include numerical-scale changes; material means change above 1e-3 MW/MVAr or 1e-4 pu. Lower/upper activity is available in 17; earlier compact summaries only give total activity. Missing metrics are not reconstructed from unavailable native states.", "", "The redistribution moves 63.82 MW and 16.02 MVAr between source-selected PQ, positive-load, 115 kV five-bus groups. Low |Ybus_ii| group: 609, 531, 154, 173, 179; high group: 2, 1, 77, 118, 37. Neither group label establishes voltage stability or causal network strength."]
    return "\n".join(lines) + "\n"


def plot(records, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    colors = {METHODS[0]: "#6d7176", METHODS[1]: "#408345", METHODS[2]: "#2477b5", METHODS[3]: "#cf5927"}
    labels = {METHODS[0]: "AC reference", METHODS[1]: "DC-OPF", METHODS[2]: "Microsoft v1.1", METHODS[3]: "Base v2"}
    fig, ax = plt.subplots(2, 3, figsize=(14, 8.1))
    for m in METHODS:
        rows = [r for r in records if r["input_record"]["experiment"] == "11C-1" and r["metrics"]["method"] == m]
        xs = [100*r["input_record"]["loading"] for r in rows]
        ys = [mean(r["metrics"], "Pg_per_generator_MW") for r in rows]
        ax[0, 0].plot(xs, [float("nan") if x is None else x for x in ys], "o-", color=colors[m], label=labels[m], ms=4)
        if m in METHODS[2:]:
            ax[0, 1].plot(xs, [r["metrics"]["Q"]["max"] for r in rows], "o-", color=colors[m], label=labels[m], ms=4)
            rich = sorted([r for r in records if r["input_record"]["experiment"] == "16" and r["input_record"]["family"] == "global" and r["metrics"]["method"] == m], key=lambda r: r["input_record"]["loading"])
            xx = [100*r["input_record"]["loading"] for r in rich]
            for stat, style in [("mean", "o-"), ("p95", "s--")]:
                ax[0, 2].plot(xx, [r["metrics"]["Q"][stat] for r in rich], style, color=colors[m], label=f"{labels[m]} {stat}", ms=4)
            charge = sorted([r for r in records if r["input_record"]["experiment"] == "17" and r["metrics"]["method"] == m], key=lambda r: r["input_record"]["positive_charging_factor"] or 1)
            xx = [100*(r["input_record"]["positive_charging_factor"] or 1) for r in charge]
            ax[1, 0].plot(xx, [mean(r["metrics"], "Qg_per_generator_MVAr") for r in charge], "o-", color=colors[m], label=labels[m])
            for col, stat in [(1, "max"), (2, "mean")]:
                ax[1, col].plot(xx, [r["metrics"]["Q"][stat] for r in charge], "o-", color=colors[m], label=labels[m])
    titles = [["Generation approximation", "Worst-bus Q imbalance", "Distribution: mean and 95th percentile"], ["Reactive-generation approximation", "Worst-bus Q imbalance", "Mean Q imbalance"]]
    ylabs = [["Pg MAE (MW)", "Max |Q residual| (MVAr)", "|Q residual| (MVAr)"], ["Qg MAE (MVAr)", "Max |Q residual| (MVAr)", "Mean |Q residual| (MVAr)"]]
    for r in range(2):
        for c in range(3):
            ax[r,c].set_title(titles[r][c], fontsize=11, loc="left")
            ax[r,c].set_ylabel(ylabs[r][c], fontsize=9)
            ax[r,c].set_xlabel("P and Q loading (% original)" if r == 0 else "Positive charging (% original), load90%", fontsize=9)
            ax[r,c].grid(alpha=.23)
            ax[r,c].tick_params(labelsize=9)
    for c in [0,1]:
        ax[0,c].axvspan(108.8, 111, color="#9a9a9a", alpha=.12)
        ax[0,c].text(.98, .98, "110% AC UNKNOWN", transform=ax[0,c].transAxes, ha="right", va="top", fontsize=8)
    ax[0,0].legend(fontsize=8, loc="center left")
    ax[0,2].legend(fontsize=7.7, loc="center right", bbox_to_anchor=(1, .72))
    ax[1,0].legend(fontsize=8)
    fig.suptitle("Original MATPOWER case300: accuracy and imbalance move differently", fontsize=15, x=.05, ha="left")
    fig.text(.05,.925,"Saved evidence from 11C-1 and 15–17; no rerun. Lines connect inspected points, not a fitted response law.",fontsize=10)
    fig.text(.05,.025,"All native model points fail joint AC feasibility; counts are near saturation. Thermal assessment N/A.\nDistribution data for loading are published at 90/100/106% only; 110% reference errors are unavailable. Row-order sensitivity limits causal claims.",fontsize=9)
    fig.subplots_adjust(top=.86,bottom=.14,left=.065,right=.98,hspace=.4,wspace=.3)
    fig.savefig(out/"loading-charging.png", dpi=180)
    fig.savefig(out/"loading-charging.svg")
    svg = out/"loading-charging.svg"
    svg.write_bytes(("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n").encode("utf-8"))
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    inputs, records = extract()
    availability = artifact_availability()
    assert len(inputs) == 44, len(inputs)
    assert len(records) == 176, len(records)
    assert len({x["input_sha256"] for x in inputs}) == 30
    assert all(not r["metrics"]["AC_joint_feasible"] for r in records if r["metrics"]["method"] in METHODS[2:])
    assert all(r["metrics"].get("native_DC_constraints_pass") for r in records if r["metrics"]["method"] == "DC-OPF")
    assert all(not r["metrics"].get("reference_valid") or mean(r["metrics"], "Pg_per_generator_MW") is not None for r in records)
    for record in records:
        if record["input_record"]["experiment"] != "11C-1" and record["metrics"]["method"] in METHODS[2:]:
            for variable in ["Pg", "Qg", "Vm"]:
                block = record["metrics"]["clipping"][variable]
                assert isinstance(block["strict_clipped_count"], int)
                assert isinstance(block["physically_meaningful_clipped_count"], int)
    distinct = {x["input_sha256"]: x for x in inputs}
    unknown = [x["scenario"] for x in distinct.values() if not x["AC_reference_valid"]]
    metadata = {
        "scope": "original MATPOWER case300 and declared interventions only; all600, R300-base and RATE80-300 PGLib rows excluded",
        "execution": "read-only extraction of compact historical evidence; no inference, OPF/PF or physics recomputation",
        "input_records": len(inputs), "method_records": len(records), "distinct_input_byte_hashes": len(distinct),
        "representation_control_byte_hashes": sum(x["representation_control"] for x in distinct.values()),
        "distinct_AC_references_accepted": sum(x["AC_reference_valid"] for x in distinct.values()),
        "distinct_AC_UNKNOWN": unknown,
        "distinct_DC_own_constraint_passes": sum(x["DC_own_constraints_pass"] for x in distinct.values()),
        "distinct_native_joint_AC_passes": 0, "distinct_native_points": 2*len(distinct),
        "duplicate_policy": "Keep every experiment/scenario record; group identical input bytes by saved SHA256. Physically equivalent renumber/reorder controls have different byte hashes and are labelled, not independent grids.",
        "unavailable_policy": "Null/blank means unavailable or not applicable, never zero. 11C compact data lack distribution/count/clipping fields.17 compact data lack material clipping magnitudes. Raw signed per-bus/per-branch details largely absent.",
        "units": {"P": "MW", "Q": "MVAr", "Pg": "MW", "Qg": "MVAr", "Vm": "pu", "angle": "degrees"},
        "fixed_tolerances": {"balance_MW_MVAr": .001, "generator_MW_MVAr": .001, "Vm_pu": .0001, "angle_deg": .001},
        "artifact_availability": availability, "source_sha256": SOURCES,
    }
    write_csv(out/"existing-inputs.csv", inputs)
    write_csv(out/"existing-methods.csv", [{**r["input_record"], **flatten(r["metrics"])} for r in records])
    (out/"existing-pairs.md").write_text(pair_text(records), encoding="utf-8")
    (out/"existing-evidence.json").write_text(json.dumps({"metadata": metadata, "inputs": inputs, "method_records": records}, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    plot(records, out)
    print(json.dumps({k:v for k,v in metadata.items() if k in ["input_records","method_records","distinct_input_byte_hashes","distinct_AC_references_accepted","distinct_AC_UNKNOWN","distinct_DC_own_constraint_passes","distinct_native_joint_AC_passes","distinct_native_points"]}, indent=2))
    print("Historical inventory present-file hash mismatches:", sum(len(a["present_hash_mismatches"]) for a in availability))


if __name__ == "__main__":
    main()
