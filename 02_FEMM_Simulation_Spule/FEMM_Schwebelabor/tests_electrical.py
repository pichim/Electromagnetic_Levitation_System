"""Independent analytic references; synthetic fluxes are NOT real FEMM data."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import csv
import json
import math
import threading
import unittest
import numpy as np
import electrical
import model
import force_map
import thermal
from tests_force_map import FakeSolver


class CircuitFemm:
    """Biased, coupled nonlinear circuit with an analytically known derivative."""
    a = {"Oben": .08, "Unten": .06}
    b = {"Oben": .004, "Unten": .002}
    bias = {"Oben": 5., "Unten": -3.}
    mutual = .003

    def __init__(self, c, fail_at=None):
        self.base = {"Oben":c.upper.current,"Unten":c.lower.current}
        self.currents = dict(self.base)
        self.path = None
        self.analyses, self.fail_at = 0, fail_at
        self.restored = False

    def mo_getcircuitproperties(self, name):
        i = self.currents[name]
        other = self.currents["Unten" if name == "Oben" else "Oben"]
        return i, 0, self.bias[name]+self.a[name]*i+self.b[name]*i**3+self.mutual*other

    def mi_modifycircprop(self, name, index, current):
        assert index == 1
        self.currents[name] = current

    def mi_saveas(self, path):
        self.path = Path(path)
        self.path.write_text(json.dumps(self.currents))

    def mi_analyze(self, flag):
        self.analyses += 1
        if self.analyses == self.fail_at:
            raise RuntimeError("synthetic perturbation failure")
        self.path.with_suffix(".ans").write_text(json.dumps(self.currents))

    def opendocument(self, path):
        self.path = Path(path)
        self.currents = json.loads(self.path.read_text())
        self.restored = True

    def __getattr__(self, name):
        return lambda *args: None


class ElectricalTests(unittest.TestCase):
    def magnet(self, **kwargs):
        return model.Magnet(coil_id=20,coil_od=40,coil_h=60,turns=100,wire_d_mm=1,current=2,**kwargs)

    def test_dc_reference_temperature_sign_and_limit(self):
        # R = rho*(100*pi*.03)/(pi*.001^2/4) = .206892 ohm.
        m = self.magnet(voltage_limit_v=.45)
        d = electrical.stationary(m,model.wire_data(m))
        self.assertAlmostEqual(d["resistance_ohm"],.206892)
        self.assertAlmostEqual(d["voltage_dc_v"],.413784)
        self.assertTrue(d["within_voltage_limit"])
        m.temperature_c=80
        warm=electrical.stationary(m,model.wire_data(m))
        self.assertAlmostEqual(warm["resistance_ohm"],.206892*1.2358)
        self.assertFalse(warm["within_voltage_limit"])
        m.current=-2
        reverse=electrical.stationary(m,model.wire_data(m))
        self.assertEqual(reverse["voltage_dc_v"],warm["voltage_dc_v"])
        self.assertLess(reverse["voltage_dc_signed_v"],0)
        m.current=0
        self.assertEqual(electrical.stationary(m,model.wire_data(m))["voltage_dc_v"],0)

    def test_measured_resistance_unknown_wire_and_time_constant(self):
        m=self.magnet(resistance20_ohm=2,lead_resistance_ohm=.5,voltage_limit_v=10)
        m.wire_d_mm=None
        d=electrical.stationary(m)
        electrical.add_inductance(d,.02,-.02,.01)  # 2 H independent reference.
        self.assertEqual(d["resistance_source"],"gemessen")
        self.assertEqual(d["voltage_dc_v"],5)
        self.assertAlmostEqual(d["time_constant_s"],.8)
        self.assertEqual(d["coil_time_constant_s"],1)
        self.assertEqual(d["max_current_rise_a_s"],2.5)
        m.resistance20_ohm=None
        unknown=electrical.stationary(m)
        electrical.add_inductance(unknown,.02,-.02,.01)
        self.assertEqual(unknown["inductance_h"],2)
        self.assertIsNone(unknown["time_constant_s"])
        self.assertIsNone(unknown["within_voltage_limit"])

    def test_invalid_inputs_disabled_unknown_and_bad_derivatives(self):
        for key,value in [("resistance20_ohm",0),("resistance20_ohm",-1),("lead_resistance_ohm",-1),
                          ("temperature_c",300),("temperature_c",float("nan")),("voltage_limit_v",0)]:
            c=model.Config();setattr(c.upper,key,value)
            self.assertTrue(model.validate(c)[0],(key,value))
        m=self.magnet();m.enabled=False
        self.assertIsNone(electrical.stationary(m))
        for high,low in [(0,0),(-1,1),(float("nan"),1)]:
            data=electrical.stationary(self.magnet(),model.wire_data(self.magnet()))
            electrical.add_inductance(data,high,low,.01)
            self.assertIsNone(data["inductance_h"])
            self.assertIsNone(data["time_constant_s"])
        for p in [[1,2], [0,0,complex(1,1)], [0,0,float("inf")]]:
            with self.assertRaises(ValueError):electrical.circuit_flux(p)

    def result(self,c,path):
        return dict(directory=str(path),warnings=[],electrical={
            s:electrical.stationary(getattr(c,s),model.wire_data(getattr(c,s))) for s in ["upper","lower"]})

    def test_nonlinear_bias_coupling_and_original_solution_restored(self):
        c=model.Config();c.upper.current=2;c.lower.current=-.7
        with TemporaryDirectory() as folder:
            path=Path(folder);f=CircuitFemm(c)
            (path/"model.fem").write_text(json.dumps(f.base))
            (path/"model.ans").write_text("ORIGINAL OPERATING POINT")
            result=self.result(c,path)
            model.Solver(SimpleNamespace(femm=f),path).calculate_inductance(c,result)
            self.assertEqual(f.analyses,4)
            self.assertEqual(f.currents,f.base)
            self.assertTrue(f.restored)
            self.assertEqual((path/"model.ans").read_text(),"ORIGINAL OPERATING POINT")
            for side,name in [("upper","Oben"),("lower","Unten")]:
                e=result["electrical"][side];i=getattr(c,side).current;h=e["perturbation_a"]
                expected=f.a[name]+3*f.b[name]*i*i+f.b[name]*h*h
                self.assertAlmostEqual(e["inductance_h"],expected,places=10)
                self.assertAlmostEqual(e["mutual_inductance_h"],f.mutual,places=10)
                self.assertAlmostEqual(e["time_constant_s"],expected/e["resistance_ohm"])
            self.assertEqual(len(result["inductance_matrix_h"]),2)

    def test_zero_current_with_bias_and_failure_restore(self):
        c=model.Config();c.upper.current=0;c.lower.enabled=False
        for fail in [None,2]:
            with self.subTest(fail=fail),TemporaryDirectory() as folder:
                path=Path(folder);f=CircuitFemm(c,fail)
                (path/"model.fem").write_text(json.dumps(f.base))
                result=self.result(c,path)
                model.Solver(SimpleNamespace(femm=f),path).calculate_inductance(c,result)
                self.assertEqual(f.currents,f.base)
                if fail:
                    self.assertIsNone(result["electrical"]["upper"]["inductance_h"])
                    self.assertIn("fehlgeschlagen",result["electrical"]["upper"]["inductance_status"])
                else:
                    self.assertAlmostEqual(result["electrical"]["upper"]["inductance_h"],.0800004,places=9)
                    self.assertIsNone(result["electrical"]["lower"])

    def test_disabled_inductance_and_legacy_v5_settings(self):
        c=model.Config();c.numerics.inductance_enabled=False
        with TemporaryDirectory() as folder:
            f=CircuitFemm(c);p=Path(folder);result=self.result(c,p)
            model.Solver(SimpleNamespace(femm=f),p).calculate_inductance(c,result)
            self.assertEqual(f.analyses,0)
            self.assertFalse((p/"induktivitaet").exists())
        data=json.loads(Path("beispiele/topfkern.json").read_text())
        data.pop("temperature",None);data.pop("force_map",None)
        old,_=model.parse_settings(data)
        self.assertIsNone(old.upper.voltage_limit_v)
        self.assertTrue(old.numerics.inductance_enabled)
        old.upper.voltage_limit_v=48;old.upper.resistance20_ohm=4.5;old.upper.temperature_c=60
        self.assertEqual(model.parse_settings(model.settings_payload(old,model.DEFAULT_SWEEPS))[0],old)

    def test_measured_resistance_is_shared_with_thermal_model(self):
        m=self.magnet(resistance20_ohm=2)
        m.core_d=10
        d=thermal.coil_data(thermal.Coil.from_magnet(m),thermal.Settings())
        self.assertEqual(d["resistance20_ohm"],2)
        self.assertAlmostEqual(d["length_m"],3*math.pi)
        m.resistance20_ohm=-1
        with self.assertRaises(ValueError):thermal.coil_data(thermal.Coil.from_magnet(m),thermal.Settings())

    def test_hold_equilibrium_can_be_voltage_unreachable(self):
        c=model.Config();c.lower.enabled=False;c.upper.resistance20_ohm=2;c.upper.voltage_limit_v=1
        target=model.mass(c)*9.81
        def solve(case,phase):
            return dict(config=case.to_dict(),magnetic_force_z_n=target+(case.upper.current-1),directory="TEST")
        row=model.find_roots(c,dict(search_start=0,search_end=2,scan_points=3),solve,threading.Event())
        self.assertEqual(len(row["roots"]),1)
        self.assertFalse(row["roots"][0]["within_voltage_limit"])
        self.assertIn("DC-Spannungsgrenze",model.summary_text(dict(row,x=15)))

    def test_saved_case_csv_and_npz_electrical_units(self):
        c=model.Config();c.lower.enabled=False;c.upper.resistance20_ohm=2;c.upper.voltage_limit_v=3
        options=dict(force_map.DEFAULTS,current_start=0,current_end=2,current_step=1,gap_start=15,gap_end=15)
        with TemporaryDirectory() as folder:
            job=model.run_job("force_map",c,options,FakeSolver(folder),threading.Event())
            for row in job["cases"]:
                saved=model.Config.from_dict(row["config"])
                row["electrical"]={"upper":electrical.stationary(saved.upper,model.wire_data(saved.upper)),"lower":None}
                electrical.add_inductance(row["electrical"]["upper"],.001,-.001,.01)
            c.upper.resistance20_ohm=100 # Live changes must not enter exported snapshots.
            model.export_job(job,Path(folder)/"values.csv")
            with (Path(folder)/"values.csv").open(encoding="utf-8-sig") as stream:
                rows=[r for r in csv.DictReader(stream,delimiter=";") if r["Typ"]=="FEMM"]
            self.assertEqual(float(rows[-1]["U_DC_oben_V"]),4)
            self.assertEqual(float(rows[-1]["L_differenziell_oben_H"]),.1)
            self.assertEqual(float(rows[-1]["Tau_oben_s"]),.05)
            self.assertEqual(rows[-1]["U_Grenze_eingehalten_oben_Bool"],"False")
            force_map.export(job,folder)
            with np.load(Path(folder)/"kraftkennfeld.npz",allow_pickle=False) as data:
                np.testing.assert_allclose(data["upper_voltage_dc_v"],[[0,2,4]])
                np.testing.assert_allclose(data["upper_inductance_h"],[[.1,.1,.1]])
                np.testing.assert_allclose(data["upper_time_constant_s"],[[.05,.05,.05]])
                np.testing.assert_allclose(data["upper_within_voltage_limit"],[[1,1,0]])
                self.assertTrue(np.isnan(data["lower_inductance_h"]).all())
            for view in electrical.VIEWS:
                fig=electrical.figure(job,view=view)
                self.assertEqual(len(fig.axes[0].lines),2 if view.startswith("Spannung") else 1)


class SavingTests(unittest.TestCase):
    def job(self,root):
        path=Path(root)/"20261009_single_abc";case=path/"faelle"/"one";case.mkdir(parents=True)
        (case/"model.fem").write_text("ORIGINAL MODEL")
        (case/"model.ans").write_text("ORIGINAL SOLUTION")
        (case/"induktivitaet").mkdir()
        (case/"induktivitaet"/"probe.fem").write_text("DO NOT EXPORT")
        c=model.Config();c.lower.enabled=False
        row=dict(config=c.to_dict(),directory=str(case),upper_current_a=c.upper.current,lower_current_a=0,
                 mass_kg=model.mass(c),weight_n=model.mass(c)*9.81,magnetic_force_z_n=.04,
                 net_force_n=.04-model.mass(c)*9.81,volume_relative_error=0,warnings=[])
        return dict(kind="single",directory=str(path),config=c.to_dict(),cases=[row],summary=[],accuracy=[],
                    options={},status="Fertig",model_version=model.MODEL_VERSION)

    def test_explicit_save_is_portable_repeat_safe_and_keeps_live_data(self):
        with TemporaryDirectory() as scratch,TemporaryDirectory() as target:
            job=self.job(scratch);original=deepcopy(job)
            saved=model.save_job(job,target)
            self.assertEqual(job,original)
            data=json.loads((saved/"job.json").read_text())
            self.assertEqual(data["directory"],".")
            self.assertEqual(data["cases"][0]["directory"],"faelle/one")
            self.assertNotIn(str(scratch),json.dumps(data))
            self.assertEqual((saved/"faelle/one/model.ans").read_text(),"ORIGINAL SOLUTION")
            self.assertFalse((saved/"faelle/one/induktivitaet").exists())
            second=model.save_job(job,target)
            self.assertNotEqual(saved,second)
            self.assertTrue((saved/"ergebnisse.csv").is_file())
            self.assertTrue((saved/"geometrie.png").is_file())

    def test_failed_save_cleans_partial_files(self):
        with TemporaryDirectory() as scratch,TemporaryDirectory() as target:
            job=self.job(scratch)
            with patch("model.export_job",side_effect=OSError("disk full")),self.assertRaises(OSError):
                model.save_job(job,target)
            self.assertEqual(list(Path(target).iterdir()),[])

    def test_no_result_exports_until_explicit_save(self):
        with TemporaryDirectory() as scratch:
            c=model.Config()
            job=model.run_job("current",c,dict(start=0,end=2,step=1,fixed_lower=0),FakeSolver(scratch),threading.Event())
            self.assertEqual(len(job["cases"]),3)
            self.assertFalse((Path(scratch)/"job.json").exists())
            self.assertFalse((Path(scratch)/"ergebnisse.csv").exists())
            self.assertFalse(list(Path(scratch).glob("*.png")))


if __name__=="__main__":unittest.main()
