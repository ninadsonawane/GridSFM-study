import copy
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'python'))
from physics_metrics import branch_flows, evaluate, aligned_angle_errors, cost


def fixture():
    return {'baseMVA': 100.,
            'bus': [[91, 3, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, .9],
                    [901, 2, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, .9]],
            'gen': [[91, 0, 0, 500, -500, 1, 100, 1, 500, -500],
                    [901, 0, 0, 500, -500, 1, 100, 1, 500, -500]],
            'branch': [[91,901,0,.1,0,100,0,0,0,0,1,-360,360]],
            'gencost': [[2,0,0,3,.01,2,3], [2,0,0,3,.01,2,3]]}


class PhysicsTests(unittest.TestCase):
    def test_lossless_line_analytic(self):
        sf, st = branch_flows(fixture(), [1,1], [10,0])
        self.assertAlmostEqual(sf[0].real, 1000*math.sin(math.radians(10)))
        self.assertAlmostEqual(sf[0].imag, 1000*(1-math.cos(math.radians(10))))
        self.assertAlmostEqual(sf[0].real + st[0].real, 0)

    def test_parallel_outage_identity_and_unlimited(self):
        c=fixture(); c['branch'].append(copy.deepcopy(c['branch'][0]))
        sf,st=branch_flows(c,[1,1],[1,0]); self.assertEqual(sf[0],sf[1])
        c['branch'][1][10]=0; c['branch'][0][5]=0
        sf,st=branch_flows(c,[1,1],[1,0]); self.assertEqual(sf[1],0j)
        p={'vm':[1,1],'va_deg':[1,0], 'pg_mw':[sf[0].real,st[0].real], 'qg_mvar':[sf[0].imag,st[0].imag]}
        r=evaluate(c,p)
        self.assertTrue(r['all_tested_constraints_pass'])
        self.assertEqual(r['rated_active_branch_count'],0)
        self.assertIsNone(r['max_rated_branch_loading'])

    def test_shunt_sign_and_charging(self):
        c=fixture(); c['branch'][0][4]=.02; c['bus'][0][4:6]=[2,3]
        p={'vm':[1,1],'va_deg':[0,0],'pg_mw':[2,0],'qg_mvar':[-4,-1]}
        self.assertTrue(evaluate(c,p)['all_tested_constraints_pass'])

    def test_complex_tap_orientation(self):
        c=fixture(); c['branch'][0][8:10]=[1.1,20]
        sf,st=branch_flows(c,[1.1,1],[20,0])
        self.assertAlmostEqual(abs(sf[0]),0,places=10)
        self.assertAlmostEqual(abs(st[0]),0,places=10)

    def test_q_cost_rows_and_angle_gauge(self):
        c=fixture(); c['gencost'] += [[2,0,0,2,4,0],[2,0,0,2,5,0]]
        self.assertAlmostEqual(cost(c,[0,0],[2,3]),29)
        self.assertEqual(aligned_angle_errors([179,-179],[0,2],0),[0,0])

    def test_infeasible_not_cost_certified(self):
        p={'vm':[1,1],'va_deg':[0,0],'pg_mw':[10,0],'qg_mvar':[0,0]}
        self.assertFalse(evaluate(fixture(),p)['all_tested_constraints_pass'])

    def test_zero_impedance_rejected(self):
        c=fixture();c['branch'][0][3]=0
        with self.assertRaises(ValueError): branch_flows(c,[1,1],[0,0])

    def test_zero_angle_bound_is_active_with_nonzero_other_side(self):
        c=fixture();c['branch'][0][11:13]=[0,30]
        p={'vm':[1,1],'va_deg':[-1,0],'pg_mw':[0,0],'qg_mvar':[0,0]}
        self.assertEqual(evaluate(c,p)['max_angle_violation_deg'],1)

    def test_unsupported_dispatchable_load_and_bad_rating_rejected(self):
        p={'vm':[1,1],'va_deg':[0,0],'pg_mw':[0,0],'qg_mvar':[0,0]}
        c=fixture();c['gen'][0][8:10]=[0,-20]
        with self.assertRaises(ValueError):evaluate(c,p)
        c=fixture();c['branch'][0][5]=-1
        with self.assertRaises(ValueError):evaluate(c,p)


if __name__ == '__main__': unittest.main()
