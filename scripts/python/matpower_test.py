"""Structural regression tests, never a substitute for MATLAB solver validation."""
import copy
import json
import unittest
from matpower_case import ROOT, SOURCE, read_case, sha256, construct, components, audit


class MatpowerStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = read_case()
        cls.cfg = json.loads((ROOT / "configs/network-case300x2.json").read_text())

    def test_exact_source(self):
        self.assertEqual(sha256(SOURCE), "69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5")

    def test_source_audit(self):
        a = audit(self.base)
        self.assertEqual(a["counts"], {"bus": 300, "gen": 69, "branch": 411, "gencost": 69})
        self.assertEqual(a["rateA_zero_count"], 411)
        self.assertEqual(a["reference_bus_ids"], [7049])
        self.assertEqual(a["off_nominal_tap_count"], 62)

    def test_counts_and_terminal_map(self):
        c, m = construct(self.base, self.cfg)
        self.assertEqual([len(c[k]) for k in ("bus", "gen", "branch", "gencost")], [600, 138, 824, 138])
        self.assertEqual(c["branch"][-1][:2], [210, 510])
        self.assertEqual([m["branch_map"][i]["id"] for i in (-2,-1)], ["tie:1", "tie:2"])
        self.assertEqual(len(set(x["id"] for x in m["branch_map"])), 824)

    def test_no_input_mutation(self):
        original = copy.deepcopy(self.base)
        construct(self.base, self.cfg)
        self.assertEqual(original, self.base)

    def test_reference_and_pv_role(self):
        c, _ = construct(self.base, self.cfg)
        old_ref = next(i for i,b in enumerate(self.base["bus"]) if b[1] == 3)
        self.assertEqual(c["bus"][old_ref][1], 3)
        self.assertEqual(c["bus"][old_ref+300][1], 2)
        self.assertEqual(sum(b[1] == 3 for b in c["bus"]), 1)

    def test_qcost_order(self):
        base = copy.deepcopy(self.base)
        qcost = [[2,0,0,3,0.123,float(i),9] for i in range(69)]
        base["gencost"] += qcost
        c, m = construct(base, self.cfg)
        self.assertEqual(c["gencost"][:69], self.base["gencost"])
        self.assertEqual(c["gencost"][69:138], self.base["gencost"])
        self.assertEqual(c["gencost"][138:207], qcost)
        self.assertEqual(c["gencost"][207:], qcost)
        self.assertEqual(m["gen_map"][-1]["q_cost_row_1based"], 276)

    def test_original_impedances_shunts_and_costs_preserved(self):
        c, _ = construct(self.base, self.cfg)
        for area in range(2):
            for j,b in enumerate(self.base["branch"]):
                self.assertEqual(c["branch"][area*411+j][2:], b[2:])
            for j,b in enumerate(self.base["bus"]):
                self.assertEqual(c["bus"][area*300+j][4:6], b[4:6])
        self.assertEqual(c["gencost"], self.base["gencost"]*2)

    def test_asymmetry_conservation(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["load_lambda"], cfg["load_delta"] = 1.1, .1
        c, _ = construct(self.base, cfg)
        for k in (2,3):
            self.assertAlmostEqual(sum(b[k] for b in c["bus"]), 2*1.1*sum(b[k] for b in self.base["bus"]), places=6)
        self.assertLess(c["bus"][next(i for i,b in enumerate(self.base["bus"]) if b[2]<0)][2], 0)

    def test_single_outage_stays_connected_preserves_id(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["tie_status"] = [1,0]
        c,m = construct(self.base, cfg)
        self.assertEqual(len(components(c)), 1)
        self.assertEqual(len(c["branch"]), 824)
        self.assertEqual(sum(b[10] > 0 for b in c["branch"]), 823)
        self.assertEqual(m["branch_map"][-1]["id"], "tie:2")

    def test_double_outage_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["tie_status"] = [0,0]
        with self.assertRaises(ValueError): construct(self.base, cfg)

    def test_different_voltage_terminals_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["terminal_external_ids"] = [231,1]
        with self.assertRaises(ValueError): construct(self.base, cfg)

    def test_missing_external_id_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["terminal_external_ids"] = [300,300]
        with self.assertRaises(ValueError): construct(self.base, cfg)

    def test_source_is_already_multigraph(self):
        self.assertEqual(len(audit(self.base)["parallel_unordered_pairs"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
