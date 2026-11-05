"""Aktivierung, Topfkerne und thermische Schnittstelle; ohne echten FEMM-Start."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import itertools
import math
import threading
import unittest
from unittest.mock import patch

import model
import thermal
from core_types import core_volume_mm3, pot_exterior_area_mm2


class RecordingFemm:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def record(*args):
            self.calls.append((name, args))
            if name == "mo_blockintegral":
                raise AssertionError("Bei deaktiviertem Objekt darf kein Objektintegral laufen.")
        return record


class CoreSwitchTests(unittest.TestCase):
    def setUp(self):
        self.materials = patch.object(model, "material_names", return_value={})
        self.materials.start()
        self.addCleanup(self.materials.stop)

    def test_all_activation_combinations(self):
        for up, low, obj in itertools.product([False, True], repeat=3):
            with self.subTest(upper=up, lower=low, object=obj):
                c = model.Config()
                c.upper.enabled, c.lower.enabled, c.object.enabled = up, low, obj
                g = model.Geometry(c)
                self.assertEqual(model.validate(c)[0], [])
                self.assertEqual(g.label_checks(), [])
                groups = {p.group for p in g.rectangles} | {p.group for p in g.circles}
                self.assertEqual(model.UPPER_CORE in groups, up)
                self.assertEqual(model.UPPER_COIL in groups, up)
                self.assertEqual(model.LOWER_CORE in groups, low)
                self.assertEqual(model.LOWER_COIL in groups, low)
                self.assertEqual(model.OBJECT in groups, obj)
                self.assertEqual(g.group_at(1, g.p["center"]), model.OBJECT if obj else model.AIR)
                self.assertEqual(model.mass(c) > 0, obj)
                self.assertEqual(model.Solver.magnetic_volume(c) > 0, obj)
                self.assertGreater(g.domain_r, 0)
                self.assertGreater(g.domain_z1, g.domain_z0)

    def test_inactive_components_keep_values_but_do_not_validate_physics(self):
        c = model.Config()
        c.upper.enabled = False
        c.upper.core_d = -20
        c.upper.material = "NICHT LADEN"
        c.upper.current = 42
        c.object.enabled = False
        c.object.kind = "pm"
        c.object.measured_mass_g = None
        before = c.to_dict()
        self.assertEqual(model.validate(c)[0], [])
        self.assertIsNone(model.wire_data(c.upper))
        self.assertIn("Deaktiviert", model.wire_summary(c.upper))
        self.assertEqual(c.to_dict(), before)

    def test_object_deactivation_keeps_nominal_positions(self):
        c = model.Config(upper_gap=12, lower_gap=23)
        before = model.coordinates(c)
        c.object.enabled = False
        self.assertEqual(model.coordinates(c), before)
        g = model.Geometry(c)
        self.assertEqual(g.circles, [])
        self.assertFalse(any(p.group == model.OBJECT for p in g.rectangles))

    def test_pm_deactivation_removes_internal_magnet(self):
        c = model.Config()
        c.object.kind = "pm"
        c.object.enabled = False
        self.assertFalse(any(p.name == "Innenmagnet" for p in model.Geometry(c).rectangles))
        self.assertEqual(model.mass(c), 0)

    def test_pot_geometry_volume_orientation_and_labels(self):
        c = model.Config()
        c.upper.core_kind = c.lower.core_kind = "pot"
        self.assertEqual(model.validate(c)[0], [])
        g = model.Geometry(c)
        self.assertEqual(g.label_checks(), [])
        upper = [p for p in g.rectangles if p.group == model.UPPER_CORE]
        lower = [p for p in g.rectangles if p.group == model.LOWER_CORE]
        self.assertEqual(len(upper), 3)
        self.assertEqual(len(lower), 3)
        reference = math.pi * (20**2*80 + (48**2-20**2)*10 + (48**2-43**2)*70)
        self.assertAlmostEqual(core_volume_mm3(c.upper), reference)
        self.assertAlmostEqual(sum(math.pi*(p.r1**2-p.r0**2)*(p.z1-p.z0) for p in upper), reference)
        for a, b in zip(upper, lower):
            self.assertEqual((a.r0, a.r1), (b.r0, b.r1))
            self.assertEqual((a.z0, a.z1), (-b.z1, -b.z0))
        # Der offene Wickelraum liegt objektseitig, die Rückwand weiter entfernt.
        self.assertEqual(g.group_at(45, 25), model.UPPER_CORE)
        self.assertEqual(g.group_at(41, 25), model.AIR)
        self.assertEqual(g.group_at(41, 95), model.UPPER_CORE)

    def test_pot_input_constraints(self):
        for key, value in [("pot_inner_d", 39), ("pot_inner_d", 75),
                           ("pot_outer_d", 86), ("pot_back_h", 0),
                           ("pot_back_h", 80), ("coil_offset", -1),
                           ("coil_h", 61)]:
            c = model.Config()
            c.upper.core_kind = "pot"
            setattr(c.upper, key, value)
            with self.subTest(key=key, value=value):
                self.assertTrue(model.validate(c)[0])
                with self.assertRaises(ValueError):
                    thermal.coil_data(thermal.Coil.from_magnet(c.upper), thermal.Settings())

    def test_closed_air_pocket_has_own_label(self):
        c = model.Config()
        c.lower.enabled = False
        c.upper.core_kind = "pot"
        c.upper.coil_id = c.upper.core_d
        c.upper.coil_od = c.upper.pot_inner_d
        c.upper.coil_offset = 0
        c.upper.coil_h = 50
        self.assertEqual(model.validate(c)[0], [])
        g = model.Geometry(c)
        pocket = [(r, z) for r, z, mat, *_ in g.labels
                  if mat == "air" and z > g.p["top"]]
        self.assertEqual(pocket, [(31.5, 80)])
        self.assertEqual(g.label_checks(), [])
        # Radialer Freiraum verbindet den Raum wieder mit der Aussenluft.
        c.upper.coil_id += 2
        g = model.Geometry(c)
        self.assertFalse(any(mat == "air" and z > g.p["top"]
                             for r, z, mat, *_ in g.labels))

    def test_pot_dimensions_follow_selected_shape(self):
        c = model.Config()
        c.upper.core_kind = "pot"
        self.assertIn("Topf", model.geometry_info(c, "upper"))
        self.assertIn("Rückwand", model.geometry_info(c, "upper"))
        for key, title in [("core_d", "Mittelpol"), ("pot_inner_d", "Topf Ø innen"),
                           ("pot_outer_d", "Topf Ø aussen"), ("pot_back_h", "Rückwand")]:
            fig = model.geometry_figure(c, section="upper", parameter="upper."+key)
            self.assertTrue(any(t.get_text().startswith(title) for t in fig.axes[0].texts))
        c.upper.core_kind = "rod"
        self.assertNotIn("Topf", model.geometry_info(c, "upper"))
        c.upper.enabled = False
        self.assertIn("deaktiviert", model.geometry_info(c, "upper"))

    def test_femm_omits_disabled_materials_circuits_and_labels(self):
        c = model.Config()
        c.lower.enabled = False
        c.lower.material = "INAKTIVER KERN"
        c.object.enabled = False
        c.object.material = "INAKTIVES OBJEKT"
        f = RecordingFemm()
        with TemporaryDirectory() as folder:
            solver = model.Solver(SimpleNamespace(femm=f, signature="TEST"), folder)
            solver.build(c, model.Geometry(c), Path(folder))
        materials = [args[0] for name, args in f.calls if name == "mi_getmaterial"]
        circuits = [args[0] for name, args in f.calls if name == "mi_addcircprop"]
        blocks = [args[5] for name, args in f.calls if name == "mi_setblockprop"]
        self.assertEqual(materials, [c.upper.material])
        self.assertEqual(circuits, ["Oben"])
        self.assertFalse(set(blocks) & {model.LOWER_CORE, model.LOWER_COIL, model.OBJECT})

    def test_pot_shared_edges_are_split_without_overlaps(self):
        c = model.Config()
        c.upper.core_kind = c.lower.core_kind = "pot"
        f = RecordingFemm()
        with TemporaryDirectory() as folder:
            model.Solver(SimpleNamespace(femm=f), folder).build(c, model.Geometry(c), Path(folder))
        segments = [args for name, args in f.calls if name == "mi_addsegment"]
        keys = [tuple(sorted(((r0, z0), (r1, z1)))) for r0, z0, r1, z1 in segments]
        self.assertEqual(len(set(keys)), len(keys))
        for i, (ar0, az0, ar1, az1) in enumerate(segments):
            for br0, bz0, br1, bz1 in segments[i+1:]:
                if ar0 == ar1 == br0 == br1:
                    self.assertLessEqual(min(max(az0, az1), max(bz0, bz1)) -
                                         max(min(az0, az1), min(bz0, bz1)), 1e-9)
                if az0 == az1 == bz0 == bz1:
                    self.assertLessEqual(min(max(ar0, ar1), max(br0, br1)) -
                                         max(min(ar0, ar1), min(br0, br1)), 1e-9)

    def test_no_object_solver_does_not_integrate_object(self):
        c = model.Config()
        c.upper.enabled = c.lower.enabled = c.object.enabled = False
        f = RecordingFemm()
        with TemporaryDirectory() as folder:
            result = model.Solver(SimpleNamespace(femm=f, signature="TEST"), folder).solve(c)
        self.assertEqual(result["upper_current_a"], 0)
        self.assertEqual(result["lower_current_a"], 0)
        for key in ["mass_kg", "weight_n", "magnetic_force_z_n", "net_force_n",
                    "magnetic_volume_m3", "volume_relative_error"]:
            self.assertEqual(result[key], 0, key)
        self.assertEqual(result["electrical"], {"upper": None, "lower": None})
        self.assertFalse(any(name == "mo_blockintegral" for name, _ in f.calls))

    def test_force_sweeps_need_active_upper_coil_and_object(self):
        for side in ["upper", "object"]:
            c = model.Config()
            getattr(c, side).enabled = False
            with self.assertRaises(ValueError):
                model.validate_options("current", c, dict(start=0, end=1, step=.5, fixed_lower=.393))
            with self.assertRaises(ValueError):
                model.find_roots(c, {}, lambda *args: None, threading.Event())
            # Ein solcher Aufbau bleibt speicherbar und für Einzelfelder gültig.
            model.settings_payload(c, model.DEFAULT_SWEEPS)

    def test_new_settings_and_legacy_versions(self):
        c = model.Config()
        c.upper.core_kind = "pot"
        c.lower.enabled = c.object.enabled = False
        payload = model.settings_payload(c, model.DEFAULT_SWEEPS)
        loaded, _ = model.parse_settings(payload)
        self.assertEqual(loaded, c)
        self.assertEqual(payload["version"], 6)
        for version in [1, 3]:
            old = model.settings_payload(model.Config(), model.DEFAULT_SWEEPS)
            old["version"] = version
            for side in ["upper", "lower"]:
                for key in model.electrical.MAGNET_FIELDS:del old["config"][side][key]
            for key in model.electrical.NUMERIC_FIELDS:del old["config"]["numerics"][key]
            del old["config"]["object"]["enabled"]
            for side in ["upper", "lower"]:
                for key in ["enabled", "core_kind", *model.POT_KEYS]:
                    del old["config"][side][key]
                if version == 1:
                    del old["config"][side]["wire_d_mm"]
                    del old["config"][side]["wire_od_mm"]
            loaded, _ = model.parse_settings(old)
            self.assertTrue(loaded.upper.enabled and loaded.lower.enabled and loaded.object.enabled)
            self.assertEqual(loaded.upper.core_kind, "rod")
            self.assertEqual(loaded.upper.wire_d_mm, None if version == 1 else 1)

    def test_settings_require_true_booleans_and_known_shapes(self):
        good = model.settings_payload(model.Config(), model.DEFAULT_SWEEPS)
        for section in ["upper", "lower", "object"]:
            for bad in ["false", 0, 1, None]:
                value = deepcopy(good)
                value["config"][section]["enabled"] = bad
                with self.assertRaises(ValueError):
                    model.parse_settings(value)
        bad = deepcopy(good)
        bad["config"]["upper"]["core_kind"] = "unknown"
        with self.assertRaises(ValueError):
            model.parse_settings(bad)

    def test_thermal_pot_mass_and_exposed_areas(self):
        c = model.Config()
        c.upper.core_kind = "pot"
        coil = thermal.Coil.from_magnet(c.upper)
        s = thermal.Settings()
        data = thermal.coil_data(coil, s)
        self.assertAlmostEqual(data["core_mass_kg"], core_volume_mm3(c.upper)*1e-9*s.core_density)
        self.assertAlmostEqual(data["core_area_m2"], pot_exterior_area_mm2(c.upper)*1e-6)
        self.assertAlmostEqual(data["copper_area_m2"], math.pi*(79.4**2-42**2)/4*1e-6)
        rod = thermal.coil_data(replace(coil, core_kind="rod"), s)
        self.assertGreater(data["core_mass_kg"], rod["core_mass_kg"])
        self.assertLess(data["copper_area_m2"], rod["copper_area_m2"])
        c.upper.enabled = False
        with self.assertRaises(ValueError):
            thermal.calculate(thermal.Coil.from_magnet(c.upper))

    def test_thermal_pot_zero_current_and_heating(self):
        coil = thermal.Coil.from_magnet(model.Magnet(core_kind="pot"))
        zero = thermal.calculate(replace(coil, current=0))
        self.assertTrue((zero.power_w == 0).all())
        self.assertTrue((zero.copper_c == 20).all())
        self.assertTrue((zero.core_c == 20).all())
        hot = thermal.calculate(coil)
        self.assertGreater(hot.copper_c[-1], 20)
        self.assertGreater(hot.core_c[-1], 20)
        self.assertGreaterEqual(hot.copper_c[-1], hot.core_c[-1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
