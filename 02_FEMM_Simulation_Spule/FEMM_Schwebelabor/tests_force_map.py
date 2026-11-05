"""Kennfeld-, Export- und Abbruchtests; synthetische Werte sind keine FEMM-Daten."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import csv
import json
import tempfile
import threading
import unittest
import numpy as np
import force_map
import model


class FakeSolver:
    def __init__(self, directory, event=None, fail_at=None):
        self.directory = Path(directory)/"faelle"
        self.directory.mkdir(parents=True)
        self.event, self.fail_at, self.count = event, fail_at, 0

    def solve(self, c, progress, field_image=False):
        self.count += 1
        if self.count == self.fail_at: raise RuntimeError("TESTFEHLER")
        force = c.upper.current - 2*c.lower.current + c.upper_gap/1000
        if self.event: self.event.set()
        return dict(config=c.to_dict(), upper_current_a=c.upper.current if c.upper.enabled else 0,
                    lower_current_a=c.lower.current if c.lower.enabled else 0,
                    magnetic_force_z_n=force, weight_n=model.mass(c)*9.81,
                    net_force_n=force-model.mass(c)*9.81, mass_kg=model.mass(c),
                    directory=str(self.directory/self.__class__.__name__),
                    volume_relative_error=0, warnings=[], solver="SYNTHETIC TEST ONLY")


class ForceMapTests(unittest.TestCase):
    def setUp(self):
        self.c = model.Config()
        self.options = dict(force_map.DEFAULTS, current_start=-1, current_end=1, current_step=1,
                            gap_start=10, gap_end=20, gap_step=10)

    def make_job(self, directory, event=None, fail_at=None):
        return model.run_job("force_map", self.c, self.options,
                             FakeSolver(directory, event, fail_at), event or threading.Event())

    def test_fixed_magnets_and_independent_currents(self):
        before = deepcopy(self.c)
        p = model.coordinates(self.c)
        changed = force_map.case_at(self.c, self.options, -2, 22)
        after = model.coordinates(changed)
        self.assertEqual(self.c, before)
        self.assertEqual((p["top"], p["bottom"], p["h"]), (after["top"], after["bottom"], after["h"]))
        self.assertEqual(changed.lower.current, self.c.lower.current)
        self.assertEqual((changed.upper_gap, changed.lower_gap), (22, 8))
        self.assertEqual(after["center"]-p["center"], -7)

    def test_lower_axis(self):
        self.options["current_side"] = "lower"
        changed = force_map.case_at(self.c, self.options, -2, 22)
        self.assertEqual((changed.lower.current, changed.upper.current), (-2, self.c.upper.current))
        self.assertEqual((changed.lower_gap, changed.upper_gap), (22, 8))

    def test_single_magnet_large_gap(self):
        self.c.lower.enabled = False
        self.options.update(gap_start=50, gap_end=60)
        force_map.validate_options(self.c, self.options)
        case = force_map.case_at(self.c, self.options, 0, 60)
        self.assertEqual(case.lower_gap, self.c.lower_gap)
        self.assertEqual(case.upper_gap, 60)

    def test_contact_disabled_and_invalid_axes(self):
        for changes in (dict(gap_end=30), dict(gap_start=0), dict(current_step=0),
                        dict(current_end=float("nan")), dict(current_start=True), dict(current_side="bad"),
                        dict(current_step=.0001)):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                force_map.validate_options(self.c, dict(self.options, **changes))
        self.c.object.enabled = False
        with self.assertRaises(ValueError): force_map.validate_options(self.c, self.options)
        self.c.object.enabled = True
        self.c.upper.enabled = False
        with self.assertRaises(ValueError): force_map.validate_options(self.c, self.options)

    def test_fixed_axis_and_endpoints(self):
        opts = dict(self.options, current_start=2, current_end=2, gap_end=10)
        self.assertEqual(force_map.axes(opts), ([2], [10]))
        self.assertEqual(force_map.axes(dict(opts, current_end=3, current_step=.6))[0], [2, 2.6, 3])

    def test_run_matrix_units_and_sign(self):
        with tempfile.TemporaryDirectory() as directory:
            job = self.make_job(directory)
            self.assertEqual(job["status"], "Fertig")
            currents, gaps, force = force_map.grid(job)
            self.assertEqual(force.shape, (2, 3))
            expected = np.array([[i-2*self.c.lower.current+g/1000 for i in currents] for g in gaps])
            np.testing.assert_array_equal(force, expected)
            self.assertLess(force[0, 0], 0)
            self.assertFalse((Path(directory)/"kraftkennfeld.npz").exists())
            self.assertFalse((Path(directory)/"job.json").exists())
            force_map.export(job, directory)
            npz = np.load(Path(directory)/"kraftkennfeld.npz")
            np.testing.assert_array_equal(npz["gap_m"], [.01, .02])
            np.testing.assert_array_equal(npz["magnetic_force_z_n"], force)
            npz.close()
            with (Path(directory)/"kraftkennfeld.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f, delimiter=";"))
            self.assertEqual(len(rows), 6)
            self.assertEqual(float(rows[0]["gap_m"]), .01)
            self.assertEqual(float(rows[0]["magnetic_force_z_n"]), force[0, 0])
            with (Path(directory)/"kraftmatrix_strom_abstand.csv").open(encoding="utf-8-sig", newline="") as f:
                transposed = list(csv.reader(f, delimiter=";"))
            self.assertEqual(float(transposed[1][2]), force[1, 0])
            data = json.loads((Path(directory)/"kraftkennfeld.json").read_text(encoding="utf-8"))
            self.assertEqual(data["config"], self.c.to_dict())
            self.assertEqual(data["completed_points"], 6)
            heatmap = force_map.figure(job, force_map.VIEWS[2])
            self.assertEqual(heatmap.axes[0].get_xlim(), (-1, 1))
            self.assertEqual(heatmap.axes[0].get_ylim(), (10, 20))

    def test_cancel_preserves_missing_points(self):
        with tempfile.TemporaryDirectory() as directory:
            job = self.make_job(directory, threading.Event())
            self.assertTrue(job["status"].startswith("Abgebrochen"))
            self.assertEqual(len(job["cases"]), 1)
            force = force_map.grid(job)[2]
            self.assertEqual(np.isfinite(force).sum(), 1)
            force_map.export(job, directory)
            data = json.loads((Path(directory)/"kraftkennfeld.json").read_text(encoding="utf-8"))
            self.assertIsNone(data["magnetic_force_z_n"][0][1])
            npz = np.load(Path(directory)/"kraftkennfeld.npz")
            self.assertTrue(np.isnan(npz["magnetic_force_z_n"][0, 1]))
            npz.close()

    def test_failure_preserves_completed_points(self):
        with tempfile.TemporaryDirectory() as directory:
            job = self.make_job(directory, fail_at=2)
            self.assertTrue(job["status"].startswith("Fehler"))
            self.assertEqual(len(job["cases"]), 1)
            self.assertEqual(job["map_errors"][0]["current_a"], 0)
            force_map.export(job, directory)
            with (Path(directory)/"kraftkennfeld.csv").open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.DictReader(f, delimiter=";"))
            self.assertEqual(rows[1]["status"], "Fehler")
            self.assertEqual(rows[1]["magnetic_force_z_n"], "")
            self.assertEqual(rows[2]["status"], "nicht berechnet")

    def test_views_fixed_slice_and_single_point(self):
        with tempfile.TemporaryDirectory() as directory:
            self.options.update(current_start=2, current_end=2, gap_start=15, gap_end=15)
            job = self.make_job(directory)
            for view in force_map.VIEWS:
                with self.subTest(view=view):
                    fig = force_map.figure(job, view)
                    fig.savefig(Path(directory)/(view.replace(" ", "_")+".png"))
            fig = force_map.figure(job, force_map.VIEWS[0], fixed=15)
            self.assertEqual(len(fig.axes[0].lines), 1)


if __name__ == "__main__": unittest.main()
