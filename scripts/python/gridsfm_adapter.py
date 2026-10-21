"""Minimal custom-data adapter for the pinned Microsoft v1.1 tensor contract.

Experimental: dependency-free converter tested; PyTorch integration not yet run.
No OPFDataset download, fake case-name change, synthetic infeasibility or trainer.
Use torch.utils.data.DataLoader(..., collate_fn=gridsfm.data.batch_data_list).
"""
from __future__ import annotations
import json
import math
from pathlib import Path


def validate_object(obj, require_labels=False):
    nodes, edges = obj["grid"]["nodes"], obj["grid"]["edges"]
    widths = {"bus": 4, "generator": 11, "load": 2, "shunt": 2}
    for kind, width in widths.items():
        rows = nodes[kind]
        if any(len(row) != width or not all(math.isfinite(v) for v in row) for row in rows):
            raise ValueError(f"{kind}: invalid shape or nonfinite value")
    nb = len(nodes["bus"])
    if nb == 0:
        raise ValueError("No buses")
    for kind in ("ac_line", "transformer", "generator_link", "load_link", "shunt_link"):
        e = edges[kind]
        if len(e["senders"]) != len(e["receivers"]):
            raise ValueError("Edge endpoint lengths differ")
        ns = nb if kind in ("ac_line", "transformer") else len(nodes[kind.split("_")[0]])
        if any(not isinstance(i, int) or i < 0 or i >= ns for i in e["senders"]):
            raise ValueError("Invalid sender index")
        if any(not isinstance(i, int) or i < 0 or i >= nb for i in e["receivers"]):
            raise ValueError("Invalid receiver index")
        if kind.endswith("_link") and e["senders"] != list(range(ns)):
            raise ValueError("Each generator/load/shunt must have exactly one ordered bus link")
        if kind in ("ac_line", "transformer"):
            width = 9 if kind == "ac_line" else 11
            if len(e["features"]) != len(e["senders"]) or any(
                len(r) != width or not all(math.isfinite(v) for v in r) for r in e["features"]
            ):
                raise ValueError(f"{kind}: invalid branch features")
            ids = obj["metadata"][kind+"_branch_ids"]
            if len(ids) != len(e["senders"]) or len(set(ids)) != len(ids):
                raise ValueError("Physical edge IDs must be one-to-one")
    physical_ids = (obj["metadata"]["ac_line_branch_ids"] +
                    obj["metadata"]["transformer_branch_ids"])
    if len(set(physical_ids)) != len(physical_ids):
        raise ValueError("Physical edge IDs must also be unique across families")
    if require_labels:
        if obj["metadata"].get("accepted_feasible") is not True:
            raise ValueError("Unknown/failed solves must not become regression or negative labels")
        sol = obj["solution"]
        for kind in ("bus", "generator"):
            if len(sol["nodes"][kind]) != len(nodes[kind]) or any(
                len(r) != 2 or not all(math.isfinite(v) for v in r) for r in sol["nodes"][kind]
            ):
                raise ValueError("Invalid node target shape/value")
        for kind in ("ac_line", "transformer"):
            se, ie = sol["edges"][kind], edges[kind]
            if se["senders"] != ie["senders"] or se["receivers"] != ie["receivers"]:
                raise ValueError("Target edge direction/order differs from features")
            if len(se["features"]) != len(ie["senders"]) or any(
                len(r) != 4 or not all(math.isfinite(v) for v in r) for r in se["features"]
            ):
                raise ValueError("Invalid flow target shape/value")


def to_data(obj, training=False):
    """Rebuild clean features first, transform, then attach labels if requested."""
    validate_object(obj, require_labels=training)
    import torch
    from torch_geometric.data import HeteroData
    from gridsfm import prepare_for_inference
    d = HeteroData()
    d.x = torch.tensor(obj["grid"]["context"], dtype=torch.float32).reshape(-1)
    nodes, edges = obj["grid"]["nodes"], obj["grid"]["edges"]
    for name, width in (("bus", 4), ("generator", 11), ("load", 2), ("shunt", 2)):
        d[name].x = torch.tensor(nodes[name], dtype=torch.float32).reshape(-1, width)
    for kind in ("ac_line", "transformer"):
        e = edges[kind]; width = 9 if kind == "ac_line" else 11
        d["bus", kind, "bus"].edge_index = torch.tensor(
            [e["senders"], e["receivers"]], dtype=torch.long).reshape(2, -1)
        d["bus", kind, "bus"].edge_attr = torch.tensor(
            e["features"], dtype=torch.float32).reshape(-1, width)
    for name in ("generator", "load", "shunt"):
        kind = name+"_link"; e = edges[kind]
        index = torch.tensor([e["senders"], e["receivers"]], dtype=torch.long).reshape(2, -1)
        d[name, kind, "bus"].edge_index = index
        d["bus", kind, name].edge_index = index.flip(0)
    prepare_for_inference(d)
    if training:
        d.feasible = torch.tensor(1, dtype=torch.long)
        d.objective = torch.tensor(obj["metadata"]["objective"], dtype=torch.float32)
        for name in ("bus", "generator"):
            d[name].y = torch.tensor(obj["solution"]["nodes"][name], dtype=torch.float32).reshape(-1, 2)
        for kind in ("ac_line", "transformer"):
            d["bus", kind, "bus"].edge_label = torch.tensor(
                obj["solution"]["edges"][kind]["features"], dtype=torch.float32).reshape(-1, 4)
    return d


class CustomCaseDataset:
    """Explicit manifest-selected paths, one clean graph per access; no implicit split."""
    def __init__(self, paths, training=True):
        self.paths = tuple(Path(p) for p in paths)
        if len(set(self.paths)) != len(self.paths):
            raise ValueError("Duplicate scenario paths")
        self.training = training

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, index):
        obj = json.loads(self.paths[index].read_text(encoding="utf-8-sig"))
        return to_data(obj, training=self.training)
