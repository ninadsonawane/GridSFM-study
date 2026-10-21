"""Pinned MATPOWER case acquisition, structural audit, and neutral construction.

Standard-library only; this is NOT a PF/OPF solver or a general MATLAB parser.
Run from repository root. Numeric literal matrix parsing is deliberately narrow.
"""
import argparse
import collections
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "1a828c7af590714499284e36ee9c81273388c594"
SOURCE = ROOT / "data/source/matpower-8.1/case300.m"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def acquire(git_dir):
    """Use git-show bytes so Windows checkout newline conversion is irrelevant."""
    for name, source in [("case300.m", "data/case300.m"), ("LICENSE", "LICENSE")]:
        data = subprocess.check_output(["git", "-C", str(git_dir), "show", COMMIT + ":" + source])
        dest = SOURCE.parent / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() != data:
            raise ValueError("Refusing to overwrite different source: " + str(dest))
        dest.write_bytes(data)


def read_case(path=SOURCE):
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r"%[^\n]*", "", text)
    case = {"version": "2", "baseMVA": float(re.search(r"mpc.baseMVA\s*=\s*([\d.eE+-]+)\s*;", text).group(1))}
    for field in ("bus", "gen", "branch", "gencost"):
        match = re.search(r"mpc\." + field + r"\s*=\s*\[(.*?)\];", text, re.S)
        if match is None:
            raise ValueError("Missing literal matrix " + field)
        rows = [[float(x) for x in row.split()] for row in match.group(1).split(";") if row.strip()]
        if len(set(map(len, rows))) != 1:
            raise ValueError("Ragged " + field)
        case[field] = rows
    assignments = set(re.findall(r"mpc\.(\w+)\s*=", text))
    if assignments != {"version", "baseMVA", "bus", "gen", "branch", "gencost"}:
        raise ValueError("Case contains unsupported fields: " + str(assignments))
    return case


def components(case):
    adj = {int(b[0]): set() for b in case["bus"] if int(b[1]) != 4}
    for b in case["branch"]:
        if b[10] > 0 and int(b[0]) in adj and int(b[1]) in adj:
            adj[int(b[0])].add(int(b[1]))
            adj[int(b[1])].add(int(b[0]))
    unseen, groups = set(adj), []
    while unseen:
        stack, group = [min(unseen)], set()
        while stack:
            u = stack.pop()
            if u in group:
                continue
            group.add(u)
            stack.extend(adj[u] - group)
        unseen -= group
        groups.append(sorted(group))
    return groups


def validate(case):
    bus_ids = [int(b[0]) for b in case["bus"]]
    assert len(bus_ids) == len(set(bus_ids)), "Duplicate bus IDs"
    assert all(b[0] == int(b[0]) and b[0] > 0 for b in case["bus"]), "Noninteger bus IDs"
    assert all(int(g[0]) in bus_ids for g in case["gen"]), "Missing generator bus"
    assert all(int(b[0]) in bus_ids and int(b[1]) in bus_ids for b in case["branch"]), "Missing branch terminal"
    assert len(case["gencost"]) in (len(case["gen"]), 2 * len(case["gen"])), "Cost row mismatch"
    assert case["baseMVA"] > 0
    for island in components(case):
        refs = [int(b[0]) for b in case["bus"] if int(b[0]) in island and int(b[1]) == 3]
        assert len(refs) == 1, "Each connected island needs exactly one reference"
        assert any(int(g[0]) == refs[0] and g[7] > 0 for g in case["gen"]), "Reference lacks online generator"


def audit(case):
    validate(case)
    bus, gen, branch, cost = (case[k] for k in ("bus", "gen", "branch", "gencost"))
    ids = [int(b[0]) for b in bus]
    kv = {int(b[0]): b[9] for b in bus}
    degree = collections.Counter(int(i) for b in branch if b[10] > 0 for i in b[:2])
    pairs = collections.Counter(tuple(sorted(map(int, b[:2]))) for b in branch)
    candidates = sorted([(degree[i], i, kv[i]) for i in ids if kv[i] == 345], reverse=True)
    return {
        "baseMVA": case["baseMVA"], "counts": {k: len(case[k]) for k in ("bus", "gen", "branch", "gencost")},
        "matrix_widths": {k: len(case[k][0]) for k in ("bus", "gen", "branch", "gencost")},
        "external_id_min_max": [min(ids), max(ids)], "ids_equal_1_to_n": ids == list(range(1, len(ids)+1)),
        "ids_outside_1_to_n": [i for i in ids if i > len(ids)],
        "bus_types": dict(collections.Counter(str(int(b[1])) for b in bus)),
        "reference_bus_ids": [int(b[0]) for b in bus if b[1] == 3],
        "nominal_kv_counts": dict(collections.Counter(str(b[9]) for b in bus)),
        "online_generators": sum(g[7] > 0 for g in gen), "online_branches": sum(b[10] > 0 for b in branch),
        "connected_components": len(components(case)), "rateA_zero_count": sum(b[5] == 0 for b in branch),
        "rateA_positive_count": sum(b[5] > 0 for b in branch), "nonzero_gs_count": sum(b[4] != 0 for b in bus),
        "nonzero_bs_count": sum(b[5] != 0 for b in bus),
        "gs_sum_MW_at_unit_V": sum(b[4] for b in bus), "bs_sum_MVAr_at_unit_V": sum(b[5] for b in bus),
        "explicit_tap_count": sum(b[8] != 0 for b in branch),
        "off_nominal_tap_count": sum(b[8] not in (0, 1) for b in branch),
        "nonzero_shift_count": sum(b[9] != 0 for b in branch),
        "angle_bounds_counts_deg": dict(collections.Counter(str(b[11:13]) for b in branch)),
        "different_kv_branch_count": sum(kv[int(b[0])] != kv[int(b[1])] for b in branch),
        "cost_model_counts": dict(collections.Counter(str(int(c[0])) for c in cost)),
        "cost_ncost_counts": dict(collections.Counter(str(int(c[3])) for c in cost)),
        "separate_reactive_cost_rows": len(cost) == 2 * len(gen),
        "negative_pd_count": sum(b[2] < 0 for b in bus), "negative_qd_count": sum(b[3] < 0 for b in bus),
        "negative_reactance_branch_rows_1based": [i+1 for i,b in enumerate(branch) if b[3] < 0],
        "nonzero_generator_capability_rows_1based": [i+1 for i,g in enumerate(gen) if any(g[10:16])],
        "initial_vm_outside_bounds_count": sum(b[7] < b[12] or b[7] > b[11] for b in bus),
        "initial_vm_min_max": [min(b[7] for b in bus),max(b[7] for b in bus)],
        "total_pd_MW": sum(b[2] for b in bus), "total_qd_MVAr": sum(b[3] for b in bus),
        "total_pmax_MW": sum(g[8] for g in gen if g[7] > 0),
        "parallel_unordered_pairs": [{"buses": list(k), "circuits": v} for k, v in pairs.items() if v > 1],
        "candidate_345kV_terminals_degree_id_kv": candidates[:10],
    }


def construct(base, cfg):
    """Copy exact matrices; renumber via external-ID -> new-ID maps; never solve."""
    validate(base)
    if len(components(base)) != 1 or any(b[1] == 4 for b in base["bus"]):
        raise ValueError("Minimum construction requires one connected source with no isolated buses")
    n, ng, nl = (len(base[k]) for k in ("bus", "gen", "branch"))
    if len(base["bus"][0]) != 13 or len(base["branch"][0]) != 13:
        raise ValueError("Pass unsolved input matrices; result columns are not accepted")
    terms = cfg["terminal_external_ids"]
    old = [int(b[0]) for b in base["bus"]]
    row = {i: k for k, i in enumerate(old)}
    if any(t not in row for t in terms):
        raise ValueError("Terminal is an external bus ID, not a row position")
    if base["bus"][row[terms[0]]][9] != base["bus"][row[terms[1]]][9]:
        raise ValueError("Direct tie requires equal nominal kV")
    if len(cfg["tie_status"]) != 2 or cfg["tie_status"] not in ([1, 1], [1, 0], [0, 1]):
        raise ValueError("Require two ties or a single outage; double outage excluded")
    tie = cfg["tie"]
    if not (tie["r_pu"] >= 0 and tie["x_pu"] > 0 and tie["rateA_MVA"] > 0):
        raise ValueError("Invalid tie impedance/rating")
    if tie["tap"] not in (0, 1) or tie["shift_deg"] != 0:
        raise ValueError("Study tie is a unity-ratio unshifted line")
    if not (0 < cfg["load_lambda"] and abs(cfg["load_delta"]) < 1):
        raise ValueError("Invalid load scaling")
    maps = [{i: k + 1 + area*n for k, i in enumerate(old)} for area in range(2)]
    case = {"version": "2", "baseMVA": base["baseMVA"], "bus": [], "gen": [], "branch": []}
    manifest = {"bus_map": [], "gen_map": [], "branch_map": [], "construction_config": copy.deepcopy(cfg)}
    area_offset = int(max(b[6] for b in base["bus"]))
    zone_offset = int(max(b[10] for b in base["bus"]))
    for area in range(2):
        tag = "AB"[area]
        load_scale = cfg["load_lambda"] * (1 + (1 if area == 0 else -1)*cfg["load_delta"])
        for j, original in enumerate(base["bus"]):
            b = original[:]
            b[0] = maps[area][int(original[0])]
            b[2], b[3] = original[2]*load_scale, original[3]*load_scale
            b[6], b[10] = original[6] + area*area_offset, original[10] + area*zone_offset
            if area == 1 and b[1] == 3:
                b[1] = 2  # retains voltage-control role; removes second phase reference
            case["bus"].append(b)
            manifest["bus_map"].append({"id": tag+":bus:"+str(int(original[0])), "area": tag, "source_row_1based": j+1, "source_external_id": int(original[0]), "new_external_id": b[0]})
        for j, original in enumerate(base["gen"]):
            g = original[:]
            g[0] = maps[area][int(g[0])]
            case["gen"].append(g)
            manifest["gen_map"].append({"id": tag+":gen:"+str(j+1), "source_row_1based": j+1, "new_row_1based": area*ng+j+1, "p_cost_row_1based": area*ng+j+1})
        for j, original in enumerate(base["branch"]):
            b = original[:]
            b[0], b[1] = maps[area][int(b[0])], maps[area][int(b[1])]
            case["branch"].append(b)
            manifest["branch_map"].append({"id": tag+":branch:"+str(j+1), "source_row_1based": j+1, "new_row_1based": area*nl+j+1})
    # MATPOWER order must be ALL P costs, then ALL Q costs, if supplied.
    p = copy.deepcopy(base["gencost"][:ng])
    case["gencost"] = copy.deepcopy(p) + copy.deepcopy(p)
    if len(base["gencost"]) == 2*ng:
        q = copy.deepcopy(base["gencost"][ng:])
        case["gencost"] += copy.deepcopy(q) + copy.deepcopy(q)
        for j, entry in enumerate(manifest["gen_map"]):
            entry["q_cost_row_1based"] = 2*ng+j+1
    for circuit in range(2):
        case["branch"].append([maps[0][terms[0]], maps[1][terms[1]], tie["r_pu"], tie["x_pu"], tie["b_pu"], tie["rateA_MVA"], tie["rateB_MVA"], tie["rateC_MVA"], tie["tap"], tie["shift_deg"], cfg["tie_status"][circuit], tie["angmin_deg"], tie["angmax_deg"]])
        manifest["branch_map"].append({"id": "tie:"+str(circuit+1), "source_row_1based": None, "new_row_1based": 2*nl+circuit+1})
    validate(case)
    assert len(components(case)) == 1
    assert len(case["bus"]) == 2*n and len(case["gen"]) == 2*ng and len(case["branch"]) == 2*nl+2
    case["bus_ids"] = [x["id"] for x in manifest["bus_map"]]
    case["gen_ids"] = [x["id"] for x in manifest["gen_map"]]
    case["branch_ids"] = [x["id"] for x in manifest["branch_map"]]
    return case, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--git-dir", help="Acquire pinned raw blobs from existing MATPOWER Git checkout")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--audit-out", type=Path, default=ROOT / "manifests/matpower-case300-audit.json")
    parser.add_argument("--construct", type=Path, help="Network config JSON; output neutral JSON to --out-dir")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/generated")
    args = parser.parse_args()
    if args.git_dir:
        acquire(args.git_dir)
    case = read_case(args.source)
    result = audit(case)
    result["source_sha256"] = sha256(args.source)
    result["source_commit"] = COMMIT
    result["execution_scope"] = "Literal matrix parsing and structural audit only; no PF or OPF run"
    args.audit_out.parent.mkdir(parents=True, exist_ok=True)
    args.audit_out.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if args.construct:
        cfg = json.loads(args.construct.read_text(encoding="utf-8"))
        built, mapping = construct(case, cfg)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "case300x2-neutral.json").write_text(json.dumps(built)+"\n", encoding="utf-8")
        (args.out_dir / "case300x2-mapping.json").write_text(json.dumps(mapping, indent=2)+"\n", encoding="utf-8")
        print("Constructed unsolved neutral matrices. No GridSFM conversion or solver validation claimed.")


if __name__ == "__main__":
    main()
