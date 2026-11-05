"""Physikalische Referenzfälle und numerische Grenzfälle, ohne FEMM."""
from dataclasses import replace
from pathlib import Path
import csv
import uuid
import unittest
import numpy as np
import thermal


class ThermalTests(unittest.TestCase):
    def setUp(self):
        self.coil = thermal.Coil(40,80,42,79.4,60,10,918,1,2.81)
        self.settings = thermal.Settings()

    def test_zero_current_has_no_heat_or_resistance_change(self):
        s = replace(self.settings, ambient_c=35)
        r = thermal.calculate(replace(self.coil,current=0),s)
        np.testing.assert_array_equal(r.copper_c,np.full_like(r.copper_c,35))
        np.testing.assert_array_equal(r.core_c,np.full_like(r.core_c,35))
        np.testing.assert_array_equal(r.power_w,np.zeros_like(r.power_w))
        self.assertEqual(r.steady_c,(35,35))
        self.assertEqual(r.limit_times_s,(None,None))

    def test_warm_zero_current_cools_both_nodes(self):
        s = replace(self.settings,initial_c=80,duration_min=300)
        r = thermal.calculate(replace(self.coil,current=0),s)
        self.assertLess(r.copper_c[-1],80)
        self.assertLess(r.core_c[-1],80)
        self.assertGreaterEqual(r.copper_c.min(),s.ambient_c-1e-9)
        self.assertGreaterEqual(r.core_c.min(),s.ambient_c-1e-9)
        self.assertTrue(np.all(np.diff(r.copper_c)<=1e-9))
        self.assertTrue(np.all(np.diff(r.core_c)<=1e-9))

    def test_negative_current_gives_identical_heating(self):
        a = thermal.calculate(self.coil)
        b = thermal.calculate(replace(self.coil,current=-self.coil.current))
        np.testing.assert_array_equal(a.copper_c,b.copper_c)
        np.testing.assert_array_equal(a.core_c,b.core_c)
        np.testing.assert_array_equal(a.power_w,b.power_w)

    def test_uncoupled_node_matches_known_first_order_solution(self):
        s = replace(self.settings,coupling_w_k=0,copper_alpha=0)
        r = thermal.calculate(self.coil,s)
        p = self.coil.current**2*r.data['resistance20_ohm']
        g = r.data['g_copper_w_k']
        capacity = r.data['copper_capacity_j_k']
        reference = s.ambient_c+p/g*(1-np.exp(-g*r.times_s/capacity))
        np.testing.assert_allclose(r.copper_c,reference,rtol=1e-12,atol=1e-11)
        np.testing.assert_array_equal(r.core_c,np.full_like(r.core_c,s.ambient_c))

    def test_adiabatic_energy_is_conserved_between_nodes(self):
        s = replace(self.settings,h_copper=0,h_core=0,copper_alpha=0,duration_min=10)
        r = thermal.calculate(self.coil,s)
        energy = (r.data['copper_capacity_j_k']*(r.copper_c-s.ambient_c)
                  +r.data['core_capacity_j_k']*(r.core_c-s.ambient_c))
        expected = self.coil.current**2*r.data['resistance20_ohm']*r.times_s
        np.testing.assert_allclose(energy,expected,rtol=1e-11,atol=1e-8)
        self.assertFalse(r.stable)
        self.assertIsNone(r.steady_c)

    def test_equilibrium_balances_generated_and_rejected_heat(self):
        s = replace(self.settings,h_copper=30,h_core=30,duration_min=1000)
        r = thermal.calculate(self.coil,s)
        self.assertTrue(r.stable)
        cu,fe = r.steady_c
        p = self.coil.current**2*r.data['resistance20_ohm']*(1+s.copper_alpha*(cu-20))
        qcu = r.data['g_copper_w_k']*(cu-s.ambient_c)
        qfe = r.data['g_core_w_k']*(fe-s.ambient_c)
        self.assertAlmostEqual(p,qcu+qfe,places=10)
        self.assertAlmostEqual(s.coupling_w_k*(cu-fe),qfe,places=10)
        np.testing.assert_allclose((r.copper_c[-1],r.core_c[-1]),r.steady_c,atol=1e-4)

    def test_higher_current_heats_more_and_cooling_heats_less(self):
        low = thermal.calculate(replace(self.coil,current=1))
        high = thermal.calculate(replace(self.coil,current=2))
        cooled = thermal.calculate(replace(self.coil,current=2),replace(self.settings,h_copper=40,h_core=40))
        self.assertGreater(high.copper_c[-1],low.copper_c[-1])
        self.assertGreater(high.core_c[-1],low.core_c[-1])
        self.assertLess(cooled.copper_c[-1],high.copper_c[-1])
        self.assertLess(cooled.core_c[-1],high.core_c[-1])

    def test_threshold_time_is_independent_of_plot_resolution(self):
        sparse = thermal.calculate(self.coil,samples=2)
        dense = thermal.calculate(self.coil,samples=1001)
        self.assertEqual(sparse.limit_times_s,dense.limit_times_s)
        self.assertTrue(all(hit is not None for hit in sparse.limit_times_s))
        for index,hit in enumerate(sparse.limit_times_s):
            values = sparse.copper_c if index==0 else sparse.core_c
            sample = np.flatnonzero(sparse.times_s==hit)[0]
            self.assertAlmostEqual(values[sample],self.settings.limit_c,places=8)

    def test_already_hot_and_unreached_limits(self):
        r = thermal.calculate(self.coil,replace(self.settings,initial_c=110))
        self.assertEqual(r.limit_times_s,(0,0))
        r = thermal.calculate(replace(self.coil,current=.1))
        self.assertEqual(r.limit_times_s,(None,None))

    def test_unstable_case_stops_at_model_boundary(self):
        r = thermal.calculate(replace(self.coil,current=10))
        self.assertFalse(r.stable)
        self.assertIsNone(r.steady_c)
        self.assertTrue(r.model_truncated)
        self.assertLess(r.times_s[-1],self.settings.duration_min*60)
        self.assertAlmostEqual(max(r.copper_c.max(),r.core_c.max()),thermal.MODEL_MAX_C,places=8)
        self.assertIsNotNone(r.limit_times_s[0])
        self.assertTrue(np.isfinite(r.power_w).all())

    def test_exact_critical_case_has_linear_growth_without_false_equilibrium(self):
        s = replace(self.settings,coupling_w_k=0)
        d = thermal.coil_data(self.coil,s)
        critical_h = self.coil.current**2*d['resistance20_ohm']*s.copper_alpha/d['copper_area_m2']
        s = replace(s,h_copper=critical_h,duration_min=1)
        r = thermal.calculate(self.coil,s)
        expected = s.ambient_c+self.coil.current**2*d['resistance20_ohm']/d['copper_capacity_j_k']*r.times_s
        np.testing.assert_allclose(r.copper_c,expected,atol=1e-10)
        self.assertFalse(r.stable)

    def test_stiff_coupling_still_respects_total_energy(self):
        s = replace(self.settings,coupling_w_k=10000,h_copper=0,h_core=0,copper_alpha=0,duration_min=1)
        r = thermal.calculate(self.coil,s)
        energy = (r.data['copper_capacity_j_k']*(r.copper_c-s.ambient_c)
                  +r.data['core_capacity_j_k']*(r.core_c-s.ambient_c))
        np.testing.assert_allclose(energy,r.power_w*r.times_s,atol=1e-6,rtol=1e-9)

    def test_geometry_mass_and_overhang_surface(self):
        d = thermal.coil_data(self.coil,self.settings)
        expected_mass = np.pi*(.04/2)**2*.08*self.settings.core_density
        self.assertAlmostEqual(d['core_mass_kg'],expected_mass)
        self.assertEqual(d['core_overlap_mm'],60)
        shifted = thermal.coil_data(replace(self.coil,coil_offset=-20),self.settings)
        self.assertEqual(shifted['core_overlap_mm'],40)
        self.assertGreater(shifted['core_area_m2'],d['core_area_m2'])
        covered = thermal.coil_data(self.coil,replace(self.settings,copper_exposed_percent=0,core_exposed_percent=50))
        self.assertEqual(covered['g_copper_w_k'],0)
        self.assertAlmostEqual(covered['core_area_m2'],d['core_area_m2']/2)

    def test_bad_settings_are_rejected(self):
        cases = [('duration_min',0),('duration_min',-1),('ambient_c',float('nan')),
                 ('h_core',-1),('h_copper',float('inf')),('coupling_w_k',-1),
                 ('core_cp',0),('copper_density',0),('core_exposed_percent',101),
                 ('copper_alpha',-.1),('initial_c',301),('limit_c',201),('duration_min',True)]
        for key,value in cases:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                thermal.calculate(self.coil,replace(self.settings,**{key:value}))

    def test_missing_or_impossible_coil_data_are_rejected(self):
        cases = [('wire_d_mm',None),('wire_d_mm',0),('turns',1.5),('turns',10000000),
                 ('core_d',90),('coil_od',20),('current',float('inf')),('wire_od_mm',.8)]
        for key,value in cases:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                thermal.calculate(replace(self.coil,**{key:value}))

    def test_csv_contains_both_nodes_and_saved_assumptions(self):
        r = thermal.calculate(self.coil,samples=12)
        folder = Path(__file__).resolve().parent/'test_output'
        folder.mkdir(exist_ok=True)
        path = folder/('thermal_'+uuid.uuid4().hex+'.csv')
        try:
            thermal.export_csv(r,path,'upper')
            with path.open(encoding='utf-8-sig',newline='') as file:
                rows = list(csv.reader(file,delimiter=';'))
            self.assertIn(['# Spule','upper'],rows)
            self.assertIn(['# Annahme_coupling_w_k','0.3'],rows)
            index = next(i for i,row in enumerate(rows) if row[0]=='Zeit_s')
            self.assertEqual(rows[index][1:3],['Wicklung_Mittel_C','Kern_Mittel_C'])
            self.assertEqual(len(rows)-index-1,len(r.times_s))
        finally:
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
