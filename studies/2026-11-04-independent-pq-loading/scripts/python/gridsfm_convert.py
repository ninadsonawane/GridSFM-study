"""Strict MATPOWER-matrix JSON -> Microsoft GridSFM v1.1 JSON.

No solver or ML dependencies. Keep UNSOLVED inputs separate from accepted labels.
This adapter is research code: toy checks pass, solver/model round-trip is pending.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path


def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def _matrix(mpc, name, width):
    rows = mpc[name]
    if not isinstance(rows, list) or any(len(r) < width for r in rows):
        raise ValueError(f"{name} must be rows with at least {width} columns")
    if any(not math.isfinite(float(v)) for r in rows for v in r):
        raise ValueError(f"{name} has nonfinite data")
    return rows


def _ids(mpc, name, count, defaults):
    ids = mpc.get(name, defaults)
    if len(ids) != count or len(set(ids)) != count:
        raise ValueError(f"{name}: expected {count} unique persistent IDs")
    return ids


def _quadratic(row):
    if row[0] != 2 or row[3] != int(row[3]) or int(row[3]) not in (1, 2, 3):
        raise ValueError("Only exact constant/linear/quadratic polynomial costs supported")
    n = int(row[3])
    if len(row) < 4 + n:
        raise ValueError("Truncated gencost row")
    return [0.0] * (3 - n) + [float(v) for v in row[4:4+n]]


def convert(mpc, solution=None):
    """Return native object. Input branch order and persistent IDs are preserved.

    MATPOWER bus/gen/branch arrays use native units, VA/SHIFT/ANG in degrees.
    solution arrays, when supplied, align with ALL original input matrix rows.
    accepted_feasible=True means an external residual/limit gate has passed.
    """
    for key in ("A", "N", "H", "Cw", "userfcn", "dcline", "storage"):
        if key in mpc and mpc[key]:
            raise ValueError(f"Unsupported problem extension {key}; cannot silently drop it")
    base = float(mpc["baseMVA"])
    if not math.isfinite(base) or base <= 0:
        raise ValueError("baseMVA must be finite and positive")
    buses, gens, branches = (_matrix(mpc, "bus", 13), _matrix(mpc, "gen", 10),
                             _matrix(mpc, "branch", 13))
    costs = _matrix(mpc, "gencost", 5)
    if len(costs) not in (len(gens), 2 * len(gens)):
        raise ValueError("gencost must have ng or 2*ng rows")
    qcost = len(costs) == 2 * len(gens)
    if qcost and any(any(c != 0 for c in _quadratic(r)) for r in costs[len(gens):]):
        raise ValueError("Nonzero reactive generation costs unsupported by GridSFM schema")
    bids = _ids(mpc, "bus_ids", len(buses), [int(b[0]) for b in buses])
    gids = _ids(mpc, "gen_ids", len(gens), [f"gen:{i+1}" for i in range(len(gens))])
    eids = _ids(mpc, "branch_ids", len(branches), [f"branch:{i+1}" for i in range(len(branches))])
    ext_ids = [int(b[0]) for b in buses]
    if len(set(ext_ids)) != len(ext_ids) or any(b[0] != int(b[0]) for b in buses):
        raise ValueError("MATPOWER BUS_I must be unique integers")
    for g in gens:
        if g[0] != int(g[0]) or int(g[0]) not in ext_ids:
            raise ValueError("Generator references an unknown/noninteger external bus ID")
        if g[9] > g[8] or g[4] > g[3]:
            raise ValueError("Generator bound order invalid; no automatic correction")
        if g[9] < 0 and g[8] == 0:
            raise ValueError("MATPOWER dispatchable-load power-factor constraints unsupported")
    for e in branches:
        if any(e[k] != int(e[k]) or int(e[k]) not in ext_ids for k in (0, 1)):
            raise ValueError("Branch references an unknown/noninteger external bus ID")
    if any(b[12] > b[11] or b[12] <= 0 for b in buses):
        raise ValueError("Invalid voltage limits; no automatic correction")
    active_bus = [i for i, b in enumerate(buses) if int(b[1]) != 4]
    bmap = {int(buses[i][0]): j for j, i in enumerate(active_bus)}
    if not active_bus or sum(int(buses[i][1]) == 3 for i in active_bus) != 1:
        raise ValueError("Minimum study requires one REF bus in one connected island")
    active_gen = [i for i, g in enumerate(gens) if g[7] > 0 and int(g[0]) in bmap]
    active_branch = [i for i, e in enumerate(branches)
                     if e[10] > 0 and int(e[0]) in bmap and int(e[1]) in bmap]
    nodes = {"bus": [[buses[i][9], buses[i][1], buses[i][12], buses[i][11]]
                     for i in active_bus], "generator": [], "load": [], "shunt": []}
    edges = {k: {"senders": [], "receivers": [], "features": []}
             for k in ("ac_line", "transformer")}
    for k in ("generator_link", "load_link", "shunt_link"):
        edges[k] = {"senders": [], "receivers": []}
    for i in active_gen:
        g = gens[i]
        if len(g) >= 16 and any(float(v) != 0 for v in g[10:16]):
            raise ValueError("Nonrectangular generator PQ capability curves unsupported")
        c2, c1, c0 = _quadratic(costs[i])
        nodes["generator"].append([g[6], g[1]/base, g[9]/base, g[8]/base,
                                    g[2]/base, g[4]/base, g[3]/base, g[5],
                                    c2*base*base, c1*base, c0])
        edges["generator_link"]["senders"].append(len(nodes["generator"])-1)
        edges["generator_link"]["receivers"].append(bmap[int(g[0])])
    if not active_gen:
        raise ValueError("At least one active generator required")
    for i in active_bus:
        b = buses[i]
        for name, vals in (("load", [b[2]/base, b[3]/base]),
                           ("shunt", [b[5]/base, b[4]/base])):
            if any(v != 0 for v in vals):
                nodes[name].append(vals)
                edges[name+"_link"]["senders"].append(len(nodes[name])-1)
                edges[name+"_link"]["receivers"].append(bmap[int(b[0])])
    family_rows = {"ac_line": [], "transformer": []}
    adjacency = [set() for _ in active_bus]
    for i in active_branch:
        e = branches[i]
        u, v = bmap[int(e[0])], bmap[int(e[1])]
        if u == v or (e[2] == 0 and e[3] == 0):
            raise ValueError("Self-loop/zero-impedance branch unsupported; no automatic repair")
        if any(e[k] < 0 for k in (5, 6, 7)) or e[8] < 0:
            raise ValueError("Negative rating/tap unsupported")
        adjacency[u].add(v); adjacency[v].add(u)
        tap = 1.0 if e[8] == 0 else e[8]
        amin, amax = math.radians(e[11]), math.radians(e[12])
        rates = [e[k]/base for k in (5, 6, 7)]  # retain zero=unlimited; no inference
        # An explicit unity MATPOWER tap still identifies a transformer.
        family = "transformer" if e[8] != 0 or e[9] != 0 else "ac_line"
        features = ([amin, amax, e[2], e[3], *rates, tap, math.radians(e[9]), e[4]/2, e[4]/2]
                    if family == "transformer" else
                    [amin, amax, e[4]/2, e[4]/2, e[2], e[3], *rates])
        edges[family]["senders"].append(u); edges[family]["receivers"].append(v)
        edges[family]["features"].append(features); family_rows[family].append(i)
    seen, todo = {0}, [0]
    while todo:
        for j in adjacency[todo.pop()]:
            if j not in seen:
                seen.add(j); todo.append(j)
    if len(seen) != len(active_bus):
        raise ValueError("Disconnected topology; minimum study excludes multiple islands")
    meta = {"adapter": "gridsfm-study-neutral-v1", "source_input_sha256": canonical_hash(mpc),
            "bus_external_ids": [ext_ids[i] for i in active_bus],
            "bus_ids": [bids[i] for i in active_bus], "gen_ids": [gids[i] for i in active_gen],
            "bus_source_rows": active_bus, "gen_source_rows": active_gen,
            "dropped_bus_rows": [i for i in range(len(buses)) if i not in active_bus],
            "dropped_gen_rows": [i for i in range(len(gens)) if i not in active_gen],
            "dropped_branch_ids": [eids[i] for i in range(len(branches)) if i not in active_branch],
            "zero_reactive_cost_block_omitted": qcost,
            "units": {"power": "pu", "angle": "rad", "base_kV": "kV", "mbase": "MVA"},
            "feature_policy": "original unsolved PG/QG/VG only; labels separate",
            "feature_provenance_check": "caller must supply original unsolved input; cannot infer from matrices"}
    for family, rows in family_rows.items():
        meta[family+"_source_rows"] = rows
        meta[family+"_branch_ids"] = [eids[i] for i in rows]
    out = {"grid": {"nodes": nodes, "edges": edges, "context": [[[base]]]}, "metadata": meta}
    if solution is not None:
        if solution.get("accepted_feasible") is not True:
            raise ValueError("Labels require an independent accepted_feasible gate, not solver success alone")
        groups = ((["vm", "va_deg"], len(buses)), (["pg_mw", "qg_mvar"], len(gens)),
                  (["pf_mw", "qf_mvar", "pt_mw", "qt_mvar"], len(branches)))
        for keys, n in groups:
            for key in keys:
                if len(solution[key]) != n or any(not math.isfinite(v) for v in solution[key]):
                    raise ValueError(f"Invalid label {key}")
        sb = [[math.radians(solution["va_deg"][i]), solution["vm"][i]] for i in active_bus]
        sg = [[solution["pg_mw"][i]/base, solution["qg_mvar"][i]/base] for i in active_gen]
        sol_edges = {}
        for family, rows in family_rows.items():
            sol_edges[family] = {"senders": edges[family]["senders"][:],
                                 "receivers": edges[family]["receivers"][:],
                                 "features": [[solution[k][i]/base for k in
                                               ("pt_mw", "qt_mvar", "pf_mw", "qf_mvar")]
                                              for i in rows]}
        objective = float(solution["objective"])
        recomputed = sum(x[8]*y[0]**2+x[9]*y[0]+x[10]
                         for x, y in zip(nodes["generator"], sg))
        if not math.isfinite(objective) or abs(objective-recomputed) > 1e-6*max(1, abs(objective)):
            raise ValueError("Label objective differs from converted generation costs")
        out["solution"] = {"nodes": {"bus": sb, "generator": sg}, "edges": sol_edges}
        meta.update(objective=objective, accepted_feasible=True,
                    solution_sha256=canonical_hash(solution))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path); p.add_argument("output", type=Path)
    p.add_argument("--labels", type=Path)
    args = p.parse_args()
    raw = json.loads(args.input.read_text(encoding="utf-8-sig"))
    labels = json.loads(args.labels.read_text(encoding="utf-8-sig")) if args.labels else None
    out = convert(raw, labels)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as f:
        json.dump(out, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"output": str(args.output), "input_sha256": out["metadata"]["source_input_sha256"],
                      "bus_count": len(out["grid"]["nodes"]["bus"])}))


if __name__ == "__main__":
    main()
