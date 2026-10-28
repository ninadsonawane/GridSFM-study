"""Publication-style figures from completed saved Experiment20 outputs only.

No inference, solver, data construction, repairs or scientific interpolation.
Usage: python -B experiments/gsfm020/figures.py [--batches 01-load-transition]
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/comparisons/GSFM-020/20261026-local-operating-conditions"
RELEASES = ("microsoft-v1.1", "newer-base-v2")
COLORS = {"microsoft-v1.1": "#C76522", "newer-base-v2": "#136D9C", "AC-OPF": "#273746", "DC-OPF": "#6D747A"}
MARKERS = {"discovery": "o", "confirmation": "D"}
LABELS = {"microsoft-v1.1": "v1.1", "newer-base-v2": "v2", "AC-OPF": "Verified AC", "DC-OPF": "DC"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_cases(only_batches):
    ledger = read(OUT / "ledger.json")
    complete = {row["id"]: row for row in ledger["attempted"] if row["status"] == "COMPLETE"}
    cases = []
    for plan_path in sorted((OUT / "batches").glob("*/plan.json")):
        plan = read(plan_path)
        if only_batches and plan["batch"] not in only_batches:
            continue
        for specification in plan["scenarios"]:
            name = specification["id"]
            directory = OUT / "cases" / name
            if name not in complete or not (directory / "summary.json").exists():
                continue
            assert complete[name]["kind"] == plan["kind"]
            assert sha(directory / "input.json") == specification["input_sha256"]
            case = {"id": name, "spec": specification, "kind": complete[name]["kind"],
                    "batch": plan["batch"], "directory": directory,
                    "summary": {row["method"]: row for row in read(directory / "summary.json")},
                    "input": read(directory / "input.json"),
                    "input_sha256": specification["input_sha256"],
                    "summary_sha256": sha(directory / "summary.json")}
            cases.append(case)
    return cases


def configure():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.titlesize": 12, "axes.labelsize": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#AFB6BB", "axes.linewidth": .7,
                         "axes.titleweight": "bold", "axes.titlepad": 10,
                         "grid.color": "#DDE2E5", "grid.linewidth": .6,
                         "legend.frameon": False, "legend.fontsize": 8.5,
                         "pdf.fonttype": 42, "ps.fonttype": 42,
                         "savefig.facecolor": "white", "figure.facecolor": "white"})


def decorate(ax, xlabel):
    ax.grid(axis="y", alpha=.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5, min_n_ticks=3, steps=[1, 2, 5, 10]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
    ax.tick_params(color="#AFB6BB", labelcolor="#333F47")


def series(ax, cases, x, values, color, label, linestyle="-", width=1.7):
    values = np.asarray([np.nan if v is None else v for v in values], dtype=float)
    ax.plot(x, values, color=color, lw=width, ls=linestyle, label=label, zorder=2)
    for kind, marker in MARKERS.items():
        mask = np.asarray([case["kind"] == kind for case in cases]) & np.isfinite(values)
        if mask.any():
            ax.scatter(np.asarray(x)[mask], values[mask], s=27 if kind == "discovery" else 46,
                       marker=marker, color=color, edgecolor="white", linewidth=.6, zorder=4)


def valid_error(case, method, key):
    summary = case["summary"].get(method, {})
    approximation = summary.get("approximation")
    return approximation[key]["mean"] if summary.get("reference_valid") and approximation and approximation.get(key) else None


def kind_legend(fig, cases, y):
    present = {case["kind"] for case in cases}
    handles = [Line2D([], [], color="#56616A", linestyle="none", marker=marker,
                      markersize=6, label=kind.capitalize() + " input")
               for kind, marker in MARKERS.items() if kind in present]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(.975, y), ncol=len(handles),
               handletextpad=.5, columnspacing=1.4)


def state_counts(cases):
    accepted = sum(bool(case["summary"].get("AC-OPF", {}).get("reference_valid")) for case in cases)
    states = [case["summary"].get(release, {}) for case in cases for release in RELEASES]
    passed = sum(s.get("AC_joint_feasible") is True for s in states)
    known = sum(s.get("AC_joint_feasible") in (True, False) for s in states)
    return accepted, passed, known


def export(fig, stem, cases, figures):
    path = figures / stem
    fig.savefig(path.with_suffix(".png"), dpi=210)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)
    return {"stem": stem, "case_ids": [case["id"] for case in cases],
            "png_sha256": sha(path.with_suffix(".png")), "pdf_sha256": sha(path.with_suffix(".pdf"))}


def loading_figure(cases, figures):
    cases = sorted(cases, key=lambda case: case["spec"].get("load_scale", 1.0))
    x = [100 * case["spec"].get("load_scale", 1.0) for case in cases]
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 8.7))
    fig.subplots_adjust(left=.080, right=.975, bottom=.135, top=.820, hspace=.52, wspace=.26)
    fig.suptitle("Frozen GridSFM: loading, voltage and native balance", x=.08, y=.97, ha="left", fontsize=19, fontweight="bold", color="#233540")
    accepted, passed, known = state_counts(cases)
    fig.text(.08, .926, f"Original case300  |  {len(cases)} completed electrical inputs  |  verified AC references {accepted}/{len(cases)}", color="#53636D", fontsize=10.5)
    fig.text(.08, .897, f"Native joint AC feasibility: {passed}/{known} model states pass  |  fixed original ordering  |  thermal assessment N/A", color="#53636D", fontsize=10.5)
    kind_legend(fig, cases, .862)

    ax = axes[0, 0]
    vm, preclip, ref, lower = [], [], [], []
    for case in cases:
        bus = next(i for i, row in enumerate(case["input"]["bus"]) if int(row[0]) == 235)
        native = read(case["directory"] / "newer-base-v2-native.json")
        captures = read(case["directory"] / "newer-base-v2-clamps.json")["captures"]
        voltage = next(item for item in captures if item["variable"] == "V")
        vm.append(native["vm"][bus]); preclip.append(voltage["input"][bus])
        lower.append(case["input"]["bus"][bus][12])
        reference = case["directory"] / "ac-native.json"
        ref.append(read(reference)["vm"][bus] if reference.exists() and case["summary"]["AC-OPF"]["reference_valid"] else None)
    assert len(set(lower)) == 1, "Global loading plot assumes unchanged voltage bounds"
    series(ax, cases, x, preclip, "#9A5295", "v2 before clamp", "--", 1.4)
    series(ax, cases, x, vm, COLORS["newer-base-v2"], "v2 native")
    series(ax, cases, x, ref, COLORS["AC-OPF"], "Verified AC", "-.", 1.5)
    ax.axhline(lower[0], color="#A1A7AA", lw=1.0, ls=":", label=f"Lower bound ({lower[0]:g} pu)")
    ax.set_title("A  Bus 235 voltage", loc="left")
    ax.set_ylabel("Voltage magnitude (pu)")
    ax.legend(loc="best", ncol=2, columnspacing=.8, handlelength=2.2)

    for ax, release, panel in ((axes[0, 1], "newer-base-v2", "B"), (axes[1, 0], "microsoft-v1.1", "C")):
        for statistic, color, linestyle in (("max", COLORS[release], "-"), ("p95", "#6E5D9A", "--"), ("mean", "#3B8B72", ":")):
            values = [case["summary"][release]["Q"][statistic] for case in cases]
            series(ax, cases, x, values, color, {"max": "Maximum", "p95": "95th percentile", "mean": "Mean"}[statistic], linestyle)
        ax.set_yscale("log")
        ax.set_title(f"{panel}  {LABELS[release]} reactive imbalance", loc="left")
        ax.set_ylabel("Absolute bus Q residual (MVAr, log scale)")
        ax.legend(loc="best", ncol=1)
    severity_values = [case["summary"][release]["Q"][statistic] for case in cases for release in RELEASES for statistic in ("mean", "p95", "max")]
    for ax in (axes[0, 1], axes[1, 0]):
        ax.set_ylim(min(severity_values) / 1.35, max(severity_values) * 1.35)

    ax = axes[1, 1]
    for release in RELEASES:
        for key, label, linestyle in (("Pg_per_generator_MW", "Pg", "-"), ("Qg_per_generator_MVAr", "Qg", "--")):
            series(ax, cases, x, [valid_error(case, release, key) for case in cases], COLORS[release], f"{LABELS[release]} {label}", linestyle)
    series(ax, cases, x, [valid_error(case, "DC-OPF", "Pg_per_generator_MW") for case in cases], COLORS["DC-OPF"], "DC Pg", ":")
    ax.set_title("D  Dispatch accuracy against verified AC", loc="left")
    ax.set_ylabel("MAE: Pg in MW; Qg in MVAr")
    ax.legend(loc="best", ncol=3, columnspacing=.9, handlelength=2.1)
    for ax in axes.flat:
        decorate(ax, "Global Pd and Qd (% of original)")
    fig.text(.08, .065, "Lines connect saved samples only. Markers distinguish discovery and confirmation; no historical points are included.", fontsize=9, color="#596872")
    fig.text(.08, .040, "Balance acceptance stays fixed at 0.001 MW/MVAr. Lower residuals or lower approximation error do not establish native feasibility.", fontsize=9, color="#596872")
    return export(fig, "01-loading-native-response", cases, figures)


def condition_figure(groups, figures):
    fig, axes = plt.subplots(len(groups), 2, figsize=(12.8, 3.55 * len(groups) + 1.65), squeeze=False)
    fig.subplots_adjust(left=.08, right=.975, bottom=.15, top=.79 if len(groups) == 1 else .825, hspace=.55, wspace=.26)
    fig.suptitle("Frozen GridSFM: demand location and physical validity", x=.08, y=.965, ha="left", fontsize=18, fontweight="bold", color="#233540")
    all_cases = [case for _, _, rows in groups for case in rows]
    accepted, passed, known = state_counts(all_cases)
    fig.text(.08, .92, f"{len(all_cases)} completed electrical inputs  |  verified AC references {accepted}/{len(all_cases)}  |  native joint passes {passed}/{known}", color="#53636D", fontsize=10.5)
    kind_legend(fig, all_cases, .885)
    for index, (field, title, cases) in enumerate(groups):
        cases = sorted(cases, key=lambda case: case["spec"][field])
        factor = 100 if field == "area_delta" else 1
        x = [factor * case["spec"][field] for case in cases]
        ax = axes[index, 0]
        for release in RELEASES:
            for statistic, linestyle in (("max", "-"), ("mean", "--")):
                series(ax, cases, x, [case["summary"][release]["Q"][statistic] for case in cases], COLORS[release], f"{LABELS[release]} Q {statistic}", linestyle)
        ax.set_yscale("log")
        ax.set_ylabel("Absolute bus Q residual (MVAr, log scale)")
        short = "Fixed-total case300" if field == "redistribution" else "Two-copy area shift"
        ax.set_title(f"{'AC'[index]}  {short}: Q imbalance", loc="left")
        ax.legend(loc="best", ncol=2)
        ax = axes[index, 1]
        for release in RELEASES:
            for key, label, linestyle in (("Pg_per_generator_MW", "Pg", "-"), ("Qg_per_generator_MVAr", "Qg", "--")):
                series(ax, cases, x, [valid_error(case, release, key) for case in cases], COLORS[release], f"{LABELS[release]} {label}", linestyle)
        ax.set_title(f"{'BD'[index]}  {short}: dispatch error", loc="left")
        ax.set_ylabel("MAE: Pg in MW; Qg in MVAr")
        ax.legend(loc="center right", bbox_to_anchor=(.99, .65), ncol=2)
        xlabel = "Area demand offset δ (%) — A: 1+δ; B: 1−δ" if field == "area_delta" else "Redistribution strength (× saved fixed-total transfer)"
        pad = max((max(x) - min(x)) * .05, .05)
        for ax in axes[index]:
            decorate(ax, xlabel)
            ax.set_xlim(min(x) - pad, max(x) + pad)
    fig.text(.08, .065, "Only completed saved inputs. Accuracy is N/A when the AC reference is UNKNOWN; lines connect sampled settings only.", fontsize=9, color="#596872")
    fig.text(.08, .035, "Original case300 thermal assessment is N/A; connected-system thermal coverage is limited to the existing finite-rated ties.", fontsize=9, color="#596872")
    return export(fig, "02-demand-location-response", all_cases, figures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", nargs="*", default=[])
    args = parser.parse_args()
    configure()
    cases = load_cases(set(args.batches))
    figures = OUT / "figures"
    figures.mkdir(exist_ok=True)
    outputs = []
    controls = ("p_scale", "q_scale", "area_delta", "charging_scale", "redistribution")
    loading = [case for case in cases if case["spec"]["network"] == 300 and not any(key in case["spec"] for key in controls)]
    if loading:
        outputs.append(loading_figure(loading, figures))
    groups = []
    for field, network, title in (("redistribution", 300, "case300 fixed-total redistribution"), ("area_delta", 600, "Two-copy system area demand shift")):
        selected = [case for case in cases if case["spec"]["network"] == network and field in case["spec"]]
        if selected:
            # Separate mechanisms must not be silently pooled across other settings.
            fixed = [{key: value for key, value in case["spec"].items() if key not in (field, "id", "input_sha256")} for case in selected]
            assert all(setting == fixed[0] for setting in fixed), "Separate nonmatched secondary conditions before plotting"
            groups.append((field, title, selected))
    if groups:
        outputs.append(condition_figure(groups, figures))
    manifest = {"generated_UTC": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(__file__),
                "source": "Saved completed inputs only; zero forwards and zero solves", "batch_filter": args.batches,
                "case_sources": [{key: case[key] for key in ("id", "kind", "batch", "input_sha256", "summary_sha256")} for case in cases],
                "figures": outputs}
    with (figures / "manifest.json").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"figures": [output["stem"] for output in outputs], "completed_inputs": len(cases)}, indent=2))


if __name__ == "__main__":
    main()
