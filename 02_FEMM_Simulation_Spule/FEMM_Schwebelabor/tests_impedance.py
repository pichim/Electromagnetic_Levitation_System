"""Independent RL references; synthetic electrical cases are not FEMM measurements."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import json
import math
import unittest
import numpy as np
import electrical
import impedance
import model


class ImpedanceTests(unittest.TestCase):
    def test_defaults_and_grid(self):
        result=impedance.calculate(impedance.Settings())
        self.assertEqual([r['current_a'] for r in result['rows']],list(range(11)))
        self.assertEqual(result['rows'][0]['voltage_sine_rms_v'],0)
        self.assertEqual(result['rows'][10]['voltage_pwm_hold_v'],40)
        self.assertEqual(result['rows'][10]['time_constant_s'],.025)
        self.assertFalse(result['rows'][10]['pwm_current_ok'])
        self.assertEqual(impedance.currents(replace(impedance.Settings(),current_start_a=.2,current_end_a=1,current_step_a=.3)),[.2,.5,.8])

    def test_345_phasor_reference_and_peak_limit(self):
        # R=3, XL=4 -> |Z|=5. Resistive and inductive voltages are orthogonal.
        s=impedance.Settings(current_start_a=2,current_end_a=2,resistance20_ohm=3,
            frequency_hz=100,inductance_mh=1000*4/(2*math.pi*100),voltage_limit_v=12)
        r=impedance.calculate(s)['rows'][0]
        self.assertAlmostEqual(r['reactance_ohm'],4)
        self.assertAlmostEqual(r['impedance_ohm'],5)
        self.assertAlmostEqual(r['phase_deg'],53.130102354156)
        self.assertAlmostEqual(r['voltage_resistive_v'],6)
        self.assertAlmostEqual(r['voltage_inductive_sine_rms_v'],8)
        self.assertAlmostEqual(r['voltage_sine_rms_v'],10)
        self.assertAlmostEqual(r['voltage_sine_peak_v'],math.sqrt(2)*10)
        self.assertFalse(r['sine_voltage_ok'])  # RMS fits 12 V; peak does not.
        self.assertTrue(r['hold_ok'])

    def test_temperature_and_frequency(self):
        s=impedance.Settings(temperature_c=80,lead_resistance_ohm=.5)
        a=impedance.calculate(s)['rows'][2]
        b=impedance.calculate(replace(s,frequency_hz=40000))['rows'][2]
        self.assertAlmostEqual(a['resistance_ohm'],4*1.2358+.5)
        self.assertAlmostEqual(b['reactance_ohm'],2*a['reactance_ohm'])
        self.assertEqual(a['voltage_pwm_hold_v'],b['voltage_pwm_hold_v'])
        self.assertAlmostEqual(a['pwm_duty'],b['pwm_duty'])
        self.assertLess(b['pwm_ripple_pp_a'],a['pwm_ripple_pp_a'])

    def test_pwm_against_independent_time_integration(self):
        # Integrate di/dt=(u-Ri)/L by RK4 to periodic steady state, not the code's closed form.
        for mode,low in [('slow',0),('bipolar',-12)]:
            r,l,current,u,f=3,.005,2,12,500
            duty=(r*current-low)/(u-low);dt=1/f/2000;i=0;trace=[]
            for period in range(35):
                trace=[]
                for step in range(2000):
                    voltage=u if step<round(2000*duty) else low
                    k1=(voltage-r*i)/l;k2=(voltage-r*(i+dt*k1/2))/l
                    k3=(voltage-r*(i+dt*k2/2))/l;k4=(voltage-r*(i+dt*k3))/l
                    trace.append(i);i+=dt*(k1+2*k2+2*k3+k4)/6
            actual=impedance.pwm_stats(r,l,current,u,f,mode)
            self.assertAlmostEqual(np.mean(trace),current,places=5)
            self.assertAlmostEqual(actual['average_current_a'],current,places=12)
            self.assertAlmostEqual(actual['current_min_a'],min(trace),places=8)
            self.assertAlmostEqual(actual['current_max_a'],max(trace),places=8)
            self.assertAlmostEqual(actual['rms_current_a'],math.sqrt(np.mean(np.square(trace))),places=5)

    def test_pwm_zero_full_duty_unreachable_and_bipolar(self):
        self.assertEqual(impedance.pwm_stats(4,.1,0,48,20000,'slow')['ripple_pp_a'],0)
        full=impedance.pwm_stats(4,.1,12,48,20000,'slow')
        self.assertEqual(full['duty'],1);self.assertAlmostEqual(full['rms_current_a'],12)
        self.assertIsNone(impedance.pwm_stats(4,.1,13,48,20000,'slow'))
        self.assertIsNone(impedance.pwm_stats(4,0,2,48,20000,'slow'))
        bipolar=impedance.pwm_stats(4,.1,0,48,20000,'bipolar')
        self.assertAlmostEqual(bipolar['average_current_a'],0,places=12)
        self.assertGreater(bipolar['ripple_pp_a'],0)
        self.assertGreater(bipolar['rms_current_a'],0)

    def test_local_rise_fall_and_copper_rms_power(self):
        s=impedance.Settings(current_start_a=1,current_end_a=1,delta_current_a=1,transition_ms=10,lead_resistance_ohm=1)
        r=impedance.calculate(s)['rows'][0]
        self.assertEqual(r['voltage_rise_v'],15);self.assertEqual(r['voltage_fall_v'],-5)
        self.assertFalse(r['fall_ok'])
        self.assertAlmostEqual(r['pwm_power_coil_w'],4*r['pwm_current_rms_a']**2)
        bipolar=impedance.calculate(replace(s,pwm_mode='bipolar'))['rows'][0]
        self.assertTrue(bipolar['fall_ok'])

    def case(self,current,l=.1):
        c=model.Config();c.upper.current=current;c.upper.resistance20_ohm=4
        d=electrical.stationary(c.upper,model.wire_data(c.upper));d['inductance_h']=l
        return dict(config=c.to_dict(),upper_current_a=current,lower_current_a=c.lower.current,
                    electrical=dict(upper=d,lower=None))

    def test_femm_local_interpolation_no_extrapolation_or_cross_config(self):
        anchor=self.case(2,.08);zero=self.case(0,.12)
        different_gap=self.case(1,99);different_gap['config']['upper_gap']+=1
        different_other_current=self.case(1,99);different_other_current['config']['lower']['current']+=1
        different_mesh=self.case(1,99);different_mesh['config']['numerics']['mesh_mm']*=2
        job=dict(cases=[zero,anchor,different_gap,different_other_current,different_mesh]);before=deepcopy(job)
        result=impedance.calculate(impedance.Settings(source='femm',current_end_a=3),job,anchor)
        self.assertAlmostEqual(result['rows'][1]['inductance_h'],.1)
        self.assertEqual(result['rows'][1]['provenance'],'Linear zwischen FEMM-Punkten')
        self.assertIsNone(result['rows'][3]['impedance_ohm'])
        self.assertIsNone(result['rows'][3]['voltage_pwm_hold_v'])
        self.assertEqual(job,before)
        anchor['config']['upper']['current']=99
        self.assertEqual(result['femm_reference']['config']['upper']['current'],2)

    def test_femm_missing_l_stays_unknown_but_r_is_available(self):
        a=self.case(0,None);b=self.case(2,.1)
        result=impedance.calculate(impedance.Settings(source='femm'),dict(cases=[a,b]),b)
        self.assertEqual(result['rows'][1]['voltage_pwm_hold_v'],4)
        self.assertIsNone(result['rows'][1]['impedance_ohm'])
        self.assertIsNone(result['rows'][1]['pwm_duty'])
        self.assertIsNone(impedance.calculate(impedance.Settings(source='femm'))['rows'][0]['inductance_h'])

    def test_settings_roundtrip_and_invalid_inputs(self):
        original=asdict(impedance.Settings());restored=impedance.parse_settings(original)
        self.assertEqual(original,restored);restored['frequency_hz']=1;self.assertEqual(original['frequency_hz'],20000)
        for key,value in [('frequency_hz',0),('current_step_a',0),('inductance_mh',-1),('source','other'),
                          ('voltage_limit_v',float('nan')),('current_limit_a',True),('temperature_c',300)]:
            with self.assertRaises(ValueError,msg=key):impedance.parse_settings(dict(original,**{key:value}))
        with self.assertRaises(ValueError):impedance.parse_settings(dict(original,extra=1))

    def test_explicit_export_preserves_settings_and_units(self):
        assessment=impedance.calculate(impedance.Settings())
        with TemporaryDirectory() as tmp:
            directory=Path(tmp)
            self.assertEqual(list(directory.iterdir()),[])  # calculating creates no result files.
            impedance.export(assessment,directory)
            self.assertEqual(json.loads((directory/'impedanz.json').read_text())['settings'],assessment['settings'])
            with (directory/'impedanz.csv').open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f,delimiter=';'))
            self.assertEqual(len(rows),11)
            self.assertAlmostEqual(float(rows[2]['reactance_ohm']),2*math.pi*20000*.1)
            for name in ('sinus','pwm','widerstand'):
                self.assertTrue((directory/f'impedanz_{name}.png').is_file())
            ax=impedance.figure(assessment,'Sinus / XL').axes[0]
            self.assertAlmostEqual(ax.lines[-1].get_ydata()[0],48/math.sqrt(2))
            ax=impedance.figure(assessment,'PWM').axes[0]
            self.assertIn('Mittelstrom',ax.get_xlabel())


if __name__=='__main__':unittest.main()
