import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'/'python'))
from make_scenarios import make_manifest, pilot, validate, load_multipliers

class ProtocolTests(unittest.TestCase):
    def test_manifest_reproducible_and_grouped(self):
        m=make_manifest(); validate(m); self.assertEqual(m,make_manifest())
        self.assertEqual(len(pilot()),24)
        nominal={r['family_id']:r for r in m['rows'] if r['split']=='test_id'}
        for r in m['rows']:
            if r['split']=='test_outage':
                b=nominal[r['family_id']]
                self.assertEqual((r['lambda'],r['delta'],r['load_seed']), (b['lambda'],b['delta'],b['load_seed']))
    def test_load_seed(self):
        self.assertEqual(load_multipliers(42),load_multipliers(42))
        self.assertNotEqual(load_multipliers(42)[0],load_multipliers(42)[1])

if __name__=='__main__':unittest.main()
