"""Eigene Ferritdefinition bis zum Modellaufbau, ohne FEMM/COM."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import core_materials as cm
import model
from tests_core_switch import RecordingFemm


class FerriteTests(unittest.TestCase):
    def test_choices_without_femm_library(self):
        with patch.object(Path, "is_file", return_value=False):
            self.assertIn(cm.NAME_3C91, model.material_names("soft"))
            self.assertNotIn(cm.NAME_3C91, model.material_names("pm"))
            self.assertIn("1010 Steel", model.material_names("soft"))
            c = model.Config()
            c.upper.material = c.lower.material = cm.NAME_3C91
            self.assertEqual(model.validate(c)[0], [])
            self.assertTrue(any("geschätzte" in w for w in model.validate(c)[1]))

    def test_merge_with_installed_library_and_name_collision(self):
        library = ('<BeginBlock><BlockName> = "Example Steel"\n'
                   '<Mu_x> = 2000\n<EndBlock>\n'
                   '<BeginBlock><BlockName> = "' + cm.NAME_3C91 + '"\n'
                   '<Mu_x> = 1\n<H_c> = 99\n<EndBlock>')
        with patch.object(Path, "is_file", return_value=True), \
             patch.object(Path, "read_text", return_value=library):
            self.assertEqual(model.material_names("soft"),
                             [cm.NAME_3C91, "Example Steel"])
            self.assertNotIn(cm.NAME_3C91, model.material_names("pm"))

    def test_bh_origin_slope_reference_and_saturated_tail(self):
        self.assertEqual(cm.BH_3C91[0], (0, 0))
        for (b0, h0), (b1, h1) in zip(cm.BH_3C91, cm.BH_3C91[1:]):
            self.assertGreater(b1, b0)
            self.assertGreater(h1, h0)
        self.assertAlmostEqual(cm.flux_density_3c91(1200), .470, places=6)
        slope = cm.flux_density_3c91(.001)/.001
        self.assertAlmostEqual(slope/cm.MU0, 3000, places=4)
        b0, h0 = cm.BH_3C91[-2]
        b1, h1 = cm.BH_3C91[-1]
        self.assertAlmostEqual((b1-b0)/(h1-h0), cm.MU0, places=12)

    def test_solver_build_and_config_roundtrip(self):
        for kind in ("rod", "pot"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                c = model.Config()
                c.upper.material = c.lower.material = cm.NAME_3C91
                c.upper.core_kind = c.lower.core_kind = kind
                path = Path(folder)/"config.json"
                model.save_config(c, path)
                loaded = model.load_config(path)
                self.assertEqual(c, loaded)
                femm = RecordingFemm()
                model.Solver(SimpleNamespace(femm=femm), folder).build(
                    loaded, model.Geometry(loaded), Path(folder))
                imported = [args[0] for name, args in femm.calls if name == "mi_getmaterial"]
                self.assertEqual(imported, ["1010 Steel"])
                added = [args for name, args in femm.calls
                         if name == "mi_addmaterial" and args[0] == cm.NAME_3C91]
                self.assertEqual(added, [(cm.NAME_3C91, 3000, 3000, 0, 0, 2e-7)])
                points = [args[1:] for name, args in femm.calls if name == "mi_addbhpoint"]
                self.assertEqual(points, list(cm.BH_3C91))
                assigned = [args[0] for name, args in femm.calls if name == "mi_setblockprop"]
                self.assertIn(cm.NAME_3C91, assigned)


if __name__ == "__main__":
    unittest.main()
