"""Dependency-free conversion checks; optional actual upstream cycle/ML checks.

python scripts/python/gridsfm_selfcheck.py
python scripts/python/gridsfm_selfcheck.py --upstream /path/to/GridSFM
python scripts/python/gridsfm_selfcheck.py --model
The last requires the separate GridSFM environment; it is NOT an accuracy test.
"""
from __future__ import annotations
import argparse
import ast
import copy
import json
import math
from pathlib import Path
import unittest
from gridsfm_convert import convert
from gridsfm_adapter import validate_object


def toy():
    return {"baseMVA": 100.,
            "bus": [[101, 3, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, .9],
                    [9001, 1, 20, 5, 2, 3, 1, 1, 0, 230, 1, 1.1, .9]],
            "gen": [[101, 0, 0, 100, -100, 1, 100, 1, 200, 0]],
            "branch": [[101, 9001, .01, .1, .02, 100, 0, 0, 0, 0, 1, -360, 360],
                       [101, 9001, .01, .1, .02, 100, 0, 0, 0, 0, 1, -360, 360]],
            "gencost": [[2, 0, 0, 3, .02, 3, 5]], "branch_ids": ["tie:1", "tie:2"]}


def labels():
    # Structural fixture ONLY, not a solved AC-OPF operating point.
    return {"vm": [1, 1], "va_deg": [0, -1], "pg_mw": [20], "qg_mvar": [5],
            "pf_mw": [10, 10], "qf_mvar": [2.5, 2.5], "pt_mw": [-9.9, -9.9],
            "qt_mvar": [-2.3, -2.3], "objective": 73., "accepted_feasible": True}


class ConversionChecks(unittest.TestCase):
    def test_parallel_identity(self):
        out = convert(toy()); validate_object(out)
        self.assertEqual(out["metadata"]["ac_line_branch_ids"], ["tie:1", "tie:2"])
        self.assertEqual(out["grid"]["edges"]["ac_line"]["senders"], [0, 0])
        self.assertEqual(out["metadata"]["bus_external_ids"], [101, 9001])

    def test_single_tie_outage(self):
        m = toy(); m["branch"][0][10] = 0
        out = convert(m, labels()); validate_object(out, True)
        self.assertEqual(out["metadata"]["ac_line_branch_ids"], ["tie:2"])
        self.assertEqual(out["metadata"]["dropped_branch_ids"], ["tie:1"])
        self.assertEqual(out["solution"]["edges"]["ac_line"]["features"][0], [-.099, -.023, .1, .025])

    def test_units_cost_direction(self):
        out = convert(toy(), labels()); validate_object(out, True)
        x = out["grid"]["nodes"]
        self.assertEqual(x["generator"][0][8:], [200., 300., 5.])
        self.assertEqual(x["shunt"], [[.03, .02]])  # Bs first, positive injection
        self.assertEqual(x["load"], [[.2, .05]])
        self.assertAlmostEqual(out["solution"]["nodes"]["bus"][1][0], -math.pi/180)

    def test_no_label_feature_leakage(self):
        a = labels(); b = labels(); b["vm"] = [.95, 1.02]; b["pg_mw"] = [30]
        b["objective"] = .02*30**2+3*30+5
        self.assertEqual(convert(toy(), a)["grid"], convert(toy(), b)["grid"])
        self.assertEqual(convert(toy())["grid"], convert(toy(), a)["grid"])

    def test_transformer_and_zero_rating(self):
        m = toy(); m["branch"][0][8:10] = [1.05, 10]; m["branch"][0][5] = 0
        out = convert(m); e = out["grid"]["edges"]["transformer"]
        self.assertEqual(e["senders"], [0]); self.assertEqual(e["receivers"], [1])
        self.assertEqual(e["features"][0][4], 0)
        self.assertEqual(e["features"][0][7], 1.05)
        self.assertAlmostEqual(e["features"][0][8], math.pi/18)
        self.assertEqual(e["features"][0][-2:], [.01, .01])

    def test_fail_closed(self):
        m = toy(); m["branch"][0][10] = m["branch"][1][10] = 0
        with self.assertRaises(ValueError): convert(m)
        m = toy(); m["gencost"].append([2, 0, 0, 2, 1, 0])
        with self.assertRaises(ValueError): convert(m)
        s = labels(); s["accepted_feasible"] = False
        with self.assertRaises(ValueError): convert(toy(), s)
        s = labels(); s["objective"] += 1
        with self.assertRaises(ValueError): convert(toy(), s)
        m = toy(); m["gen"][0][8:10] = [0, -20]
        with self.assertRaises(ValueError): convert(m)
        m = toy(); m["gencost"][0][3] = 2.5
        with self.assertRaises(ValueError): convert(m)


def upstream_cycle_check(root):
    """Execute the actual function body without importing unavailable PyG.

    This tests cycle construction, not promotion/batching or model support.
    """
    import numpy as np
    import torch
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import minimum_spanning_tree
    from typing import Dict, List, Tuple
    source = Path(root)/"model/gridsfm/cycle_basis.py"
    parsed = ast.parse(source.read_text(encoding="utf-8"))
    function = next(n for n in parsed.body if isinstance(n, ast.FunctionDef)
                    and n.name == "_fundamental_cycles_fast")
    function.args.args[0].annotation = None
    namespace = {"np": np, "Dict": Dict, "List": List, "Tuple": Tuple,
                 "_csr_matrix": csr_matrix, "_scipy_mst": minimum_spanning_tree,
                 "_AC_LINE_KEY": ("bus", "ac_line", "bus"),
                 "_TRANSFORMER_KEY": ("bus", "transformer", "bus")}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
    class Store: pass
    class Graph(dict): pass
    d = Graph(); d["bus"] = Store(); d["bus"].x = torch.zeros(2, 4)
    key = ("bus", "ac_line", "bus"); d[key] = Store()
    d[key].edge_index = torch.tensor([[0, 0], [1, 1]]); d.edge_types = [key]
    cycles = namespace["_fundamental_cycles_fast"](d)
    assert len(cycles) == 1 and {e[2] for e in cycles[0]} == {("ac_line", 0), ("ac_line", 1)}
    # Reverse orientation of second physical edge: it must remain distinct.
    d[key].edge_index = torch.tensor([[0, 1], [1, 0]])
    cycles_rev = namespace["_fundamental_cycles_fast"](d)
    assert len(cycles_rev) == 1 and len(cycles_rev[0]) == 2
    d[key].edge_index = torch.tensor([[0], [1]])
    assert namespace["_fundamental_cycles_fast"](d) == []
    print(json.dumps({"actual_upstream_cycle_function": "PASS", "parallel_edges": 2,
                      "cycles": 1, "after_single_outage_cycles": 0,
                      "full_pyg_model_check": "NOT RUN"}))


def model_check():
    import torch
    from gridsfm_adapter import to_data
    from gridsfm import batch_data_list
    from gridsfm.model import GridTransformerBackbone
    from gridsfm.loss import compute_loss
    m = toy(); obj = convert(m, labels()); d = to_data(obj, training=True)
    assert d["branch_ac"].x.shape[0] == 2 and d["cycle"].x.shape[0] == 1
    m["branch"][1][10] = 0
    one = to_data(convert(m, labels()), training=True)
    assert one["branch_ac"].x.shape[0] == 1
    batch = batch_data_list([d, one])
    assert batch["bus", "ac_line", "bus"].edge_index.shape[1] == 3
    torch.manual_seed(17)
    model = GridTransformerBackbone(hidden_dim=16, num_blocks=1)
    model(batch); loss, _ = compute_loss(batch)
    assert torch.isfinite(loss); loss.backward()
    a = batch_data_list([to_data(obj)]); bobj = copy.deepcopy(obj)
    bobj["solution"]["nodes"]["bus"][0][1] = 55
    b = batch_data_list([to_data(bobj)])
    model.eval()
    with torch.no_grad():
        ap = model(a)["bus"].pred; bp = model(b)["bus"].pred
    torch.testing.assert_close(ap, bp, rtol=0, atol=0)
    print("PASS: random-model structural forward/backward, outage batching, solution-label invariance")


def lora_check():
    """Tiny NN wrapper contract test; not GridSFM adaptation or an OPF result."""
    import torch
    from torch import nn
    from gridsfm_lora import GridSFMLoRAModel, LoRAConfig
    class Block(nn.Module):
        def __init__(self):
            super().__init__()
            self.ffn = nn.ModuleDict({"bus": nn.Sequential(nn.Linear(4, 8), nn.GELU(), nn.Linear(8, 4))})
    class Backbone(nn.Module):
        def __init__(self):
            super().__init__(); self.blocks = nn.ModuleList([Block()])
        def forward(self, x):
            return self.blocks[0].ffn["bus"](x)
    torch.manual_seed(17); base = Backbone(); x = torch.randn(3, 4)
    baseline = base(x).detach().clone(); wrapped = GridSFMLoRAModel(base)
    name = wrapped.add_adapter(LoRAConfig(rank=2, alpha=2))
    torch.testing.assert_close(wrapped(x), baseline, atol=0, rtol=0)
    assert wrapped.target_modules == ("blocks.0.ffn.bus.0", "blocks.0.ffn.bus.2")
    assert all("adapters" in n for n,p in wrapped.named_parameters() if p.requires_grad)
    wrapped(x).square().mean().backward()
    assert all(p.grad is None for n,p in wrapped.named_parameters() if "adapters" not in n)
    assert any(p.grad is not None and torch.count_nonzero(p.grad) for p in wrapped.adapter_parameters(name))
    wrapped.disable_adapter(); torch.testing.assert_close(wrapped(x), baseline, atol=0, rtol=0)
    print("PASS: imported FFN LoRA target names, zero-output initialization, backbone freeze, adapter gradients")


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--upstream", type=Path); p.add_argument("--model", action="store_true")
    p.add_argument("--lora", action="store_true")
    args = p.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConversionChecks))
    if not result.wasSuccessful(): raise SystemExit(1)
    if args.upstream: upstream_cycle_check(args.upstream)
    if args.model: model_check()
    if args.lora: lora_check()
