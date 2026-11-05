"""Logiktests ohne FEMM. Synthetische Kräfte dienen nur dem Suchalgorithmustest."""
from copy import deepcopy
import math
import json
import threading
import unittest
from unittest.mock import patch
from io import StringIO
import numpy as np
import model

class LogicTests(unittest.TestCase):
    def test_default_and_independent(self):
        c=model.Config();self.assertFalse(model.validate(c)[0])
        c.lower.core_d=30
        self.assertEqual(c.upper.core_d,40);self.assertFalse(model.validate(c)[0])
    def test_invalid_not_corrected(self):
        c=model.Config();c.upper.core_d=70;original=deepcopy(c)
        result,changes=model.normalize(c)
        self.assertEqual(result,original);self.assertEqual(changes,[])
        self.assertTrue(model.validate(c)[0])
        for value in [float('nan'),float('inf')]:
            c.upper.current=value;self.assertTrue(model.validate(c)[0])
    def test_turns_and_dimensions(self):
        for field,value in [('turns',1.5),('turns',0),('coil_od',40),('core_l',-1)]:
            c=model.Config();setattr(c.upper,field,value)
            self.assertTrue(model.validate(c)[0],field)
    def test_positions(self):
        c=model.Config(upper_gap=16,lower_gap=24);p=model.coordinates(c)
        self.assertEqual((p['h'],p['center']),(50,4))
        p=model.coordinates(model.at_gap(c,20))
        self.assertEqual((p['upper_gap'],p['lower_gap'],p['center']),(20,20,0))
        c.lower_gap=0;self.assertTrue(model.validate(c)[0])
    def test_collisions_and_overhang(self):
        c=model.Config();c.upper.coil_offset=-5
        self.assertFalse(model.validate(c)[0])
        c.upper.coil_id=c.upper.core_d;self.assertFalse(model.validate(c)[0])
        c.upper.coil_offset=-55
        self.assertTrue(any('überschneiden' in e for e in model.validate(c)[0]))
        c=model.Config();c.object.diameter=60;c.upper.coil_offset=-30
        self.assertTrue(any('Schwebeobjekt' in e for e in model.validate(c)[0]))
    def test_hollow_mass(self):
        c=model.Config();c.object.kind='hollow';g=model.Geometry(c)
        self.assertEqual(g.group_at(.5,0),model.AIR);self.assertEqual(g.group_at(4.5,0),model.OBJECT)
        volume=model.Solver.magnetic_volume(c);calculated=model.mass(c)
        c.object.measured_mass_g=40
        self.assertEqual(model.mass(c),.04);self.assertNotEqual(calculated,.04)
        self.assertEqual(model.Solver.magnetic_volume(c),volume);self.assertEqual(g.label_checks(),[])
        c.object.wall=5;self.assertTrue(model.validate(c)[0])
    def test_pm(self):
        c=model.Config();c.object.kind='pm';self.assertTrue(model.validate(c)[0])
        c.object.measured_mass_g=2;self.assertFalse(model.validate(c)[0])
        self.assertFalse(model.Geometry(c).label_checks())
        c.object.pm_z=4;self.assertTrue(model.validate(c)[0])
    def test_multiple_and_tangent_roots(self):
        c=model.Config();target=model.mass(c)*9.81;options=dict(search_start=-4,search_end=4,scan_points=9)
        def evaluate(case,phase):
            i=case.upper.current
            return dict(magnetic_force_z_n=target+(i+1.2)*(i-2.2),directory='TEST-ONLY')
        roots=model.find_roots(c,options,evaluate,threading.Event())['roots']
        self.assertEqual(len(roots),2);self.assertLess(roots[0]['current_a'],0)
        self.assertTrue(all(abs(r['residual_n'])<=c.numerics.equilibrium_tolerance_n for r in roots))
        def tangent(case,phase):
            return dict(magnetic_force_z_n=target+(case.upper.current-1.2)**2,directory='TEST-ONLY')
        self.assertEqual(len(model.find_roots(c,options,tangent,threading.Event())['roots']),1)
    def test_unreachable_and_cancel(self):
        c=model.Config();opts=dict(search_start=0,search_end=4,scan_points=9)
        def impossible(case,phase):
            return dict(magnetic_force_z_n=0,directory='TEST-ONLY')
        result=model.find_roots(c,opts,impossible,threading.Event())
        self.assertFalse(result['roots']);self.assertIn('nicht erreichbar',result['status'])
        event=threading.Event();event.set()
        with self.assertRaises(model.Cancelled):model.find_roots(c,opts,impossible,event)
    def test_preview_without_femm(self):
        c=model.Config()
        with patch.dict('sys.modules',{'femm':None,'pythoncom':None}):
            fig=model.geometry_figure(c)
            self.assertEqual(float(fig.axes[0].get_aspect()),1);self.assertTrue(fig.axes[0].patches)
        c.upper.material='DOES NOT EXIST'
        if model.material_names(metadata=True):self.assertTrue(model.validate(c)[0])
    def test_sweep_limits(self):
        self.assertEqual(model.sweep_values(-1,1,.75),[-1,-.25,.5,1])
        for start,end,step in [(2,1,1),(0,1,0),(0,float('inf'),1)]:
            with self.assertRaises(ValueError):model.sweep_values(start,end,step)

    def test_field_mirror_keeps_axis_flux_and_triangle_orientation(self):
        nodes=StringIO('r,z,flux\n0,-1,0\n1,-1,0.1\n1,1,0.2\n0,1,0\n')
        elements=StringIO('n1,n2,n3,B,group\n1,2,3,0.1,0\n1,3,4,0.2,30\n')
        result=dict(config=model.Config().to_dict(),field_data=dict(nodes=nodes,elements=elements))
        n,t,b,g=model.field_arrays(result)
        self.assertEqual((n.shape,t.shape),((6,3),(4,3)))
        self.assertEqual(sum(n[:,0]==0),2)
        np.testing.assert_array_equal(n[4:,:],n[1:3,:]*[-1,1,1])
        np.testing.assert_array_equal(b,[.1,.2,.1,.2])
        np.testing.assert_array_equal(g,[0,30,0,30])
        p=n[t,:2];a=p[:,1]-p[:,0];z=p[:,2]-p[:,0]
        self.assertTrue((a[:,0]*z[:,1]-a[:,1]*z[:,0]>0).all())
        nodes.seek(0);elements.seek(0)
        with patch.dict('sys.modules',{'femm':None,'pythoncom':None}):
            self.assertEqual(len(model.field_figure(result).axes),2)

    def test_field_rejects_broken_mesh(self):
        for entry in ['1,2,9,0.1,0','1.5,2,3,0.1,0','1,2,3,-0.1,0','1,2,3,nan,0']:
            nodes=StringIO('r,z,flux\n0,0,0\n1,0,0.1\n1,1,0.2\n')
            elements=StringIO('n1,n2,n3,B,group\n'+entry+'\n')
            result=dict(field_data=dict(nodes=nodes,elements=elements))
            with self.assertRaises(ValueError):model.field_arrays(result)

    def test_context_dimensions_and_signed_positions(self):
        c=model.Config();c.upper.core_l=90;c.lower.coil_offset=-5
        self.assertIn('90 mm',model.geometry_info(c,'upper'))
        self.assertIn('Position -5 mm',model.geometry_info(c,'lower'))
        for side,sign in [('upper',1),('lower',-1)]:
            f=model.geometry_figure(c,section=side,parameter=side+'.core_l')
            text=next(t for t in f.axes[0].texts if t.get_text().startswith('Länge '))
            pole=model.coordinates(c)['top' if side=='upper' else 'bottom']
            self.assertAlmostEqual(text.xy[1],pole+sign*getattr(c,side).core_l/2)
        for side in ['upper','lower']:
            for key in ['core_d','coil_id','coil_od','coil_h','coil_offset']:
                f=model.geometry_figure(c,section=side,parameter=side+'.'+key)
                self.assertTrue(any('mm' in t.get_text() and t.get_bbox_patch() for t in f.axes[0].texts))

    def test_object_dimensions_do_not_change_mass_geometry(self):
        c=model.Config();c.object.kind='hollow'
        self.assertIn('Wand 1 mm',model.geometry_info(c,'object'))
        before=model.Solver.magnetic_volume(c)
        c.object.measured_mass_g=40
        self.assertIn('Gesamtmasse 40 g',model.geometry_info(c,'object'))
        model.geometry_figure(c,section='object',parameter='object.wall')
        self.assertEqual(model.Solver.magnetic_volume(c),before)
        c.object.kind='pm';c.object.pm_z=-1
        self.assertIn('Lage z -1 mm',model.geometry_info(c,'object'))
        for key in ['diameter','pm_d','pm_h','pm_z']:
            f=model.geometry_figure(c,section='object',parameter='object.'+key)
            self.assertTrue(any('mm' in t.get_text() and t.get_bbox_patch() for t in f.axes[0].texts))

    def test_unreachable_gap_remains_in_visible_chart(self):
        job=dict(kind='gap',config=model.Config().to_dict(),options=dict(fixed_lower=.393),
                 summary=[dict(x=15,roots=[dict(current_a=2.8)]),dict(x=50,roots=[])])
        ax=model.sweep_figure(job).axes[0]
        lo,hi=ax.get_xlim()
        self.assertLess(lo,15);self.assertGreater(hi,50)
        self.assertEqual(float(ax.collections[-1].get_offsets()[0,0]),50)

    def test_settings_roundtrip_all_objects(self):
        for kind in ['solid','hollow','pm']:
            c=model.Config();c.object.kind=kind;c.object.measured_mass_g=35
            c.upper.current=-2.456789012345678;c.lower.core_d=30;c.upper_gap=17;c.lower_gap=26
            c.object.pm_direction=-1
            c.numerics=model.Numerics(mesh_mm=.247,air_mesh_mm=4.7,arc_deg=1.25,domain_factor=6)
            sweeps=dict(model.DEFAULT_SWEEPS,current_start=-2,search_start=-4,scan_points=17)
            data=model.settings_payload(c,sweeps)
            loaded,steps=model.parse_settings(json.loads(json.dumps(data)))
            self.assertEqual(loaded.to_dict(),c.to_dict());self.assertEqual(steps,sweeps)

    def test_mesh_inputs_invalid_without_correction(self):
        for key,value in [("mesh_mm",0),("mesh_mm",-1),("air_mesh_mm",0),("air_mesh_mm",float('nan')),
                          ("mesh_mm",float('inf')),("arc_deg",.05),("arc_deg",91),("domain_factor",1.9)]:
            c=model.Config();setattr(c.numerics,key,value)
            self.assertTrue(model.validate(c)[0],(key,value))
            result,_=model.normalize(c)
            actual=getattr(result.numerics,key)
            self.assertTrue(math.isnan(actual) if math.isnan(value) else actual==value)
            with self.assertRaises(ValueError):model.settings_payload(c,model.DEFAULT_SWEEPS)

    def test_settings_reject_unknown_or_incomplete_files(self):
        good=model.settings_payload(model.Config(),model.DEFAULT_SWEEPS)
        for field,value in [('format','other'),('version',2),('version',True),('config',[]),('sweeps',{})]:
            data=deepcopy(good);data[field]=value
            with self.assertRaises(ValueError):model.parse_settings(data)
        data=deepcopy(good);del data['config']['lower']['core_l']
        with self.assertRaises(ValueError):model.parse_settings(data)

    def test_settings_reject_wrong_types_and_invalid_geometry(self):
        good=model.settings_payload(model.Config(),model.DEFAULT_SWEEPS)
        for value in ['2.8',True,float('nan'),float('inf')]:
            data=deepcopy(good);data['config']['upper']['current']=value
            with self.assertRaises(ValueError):model.parse_settings(data)
        data=deepcopy(good);data['config']['upper']['core_d']=70
        with self.assertRaises(ValueError):model.parse_settings(data)
        data=deepcopy(good);data['config']['object']['pm_direction']=0
        with self.assertRaises(ValueError):model.parse_settings(data)

    def test_settings_reject_invalid_sweep_without_correction(self):
        for key,value in [('current_step',0),('gap_start',-1),('scan_points',2.5),('search_end',-1)]:
            sweeps=dict(model.DEFAULT_SWEEPS);sweeps[key]=value
            before=deepcopy(sweeps)
            with self.assertRaises(ValueError):model.settings_payload(model.Config(),sweeps)
            self.assertEqual(sweeps,before)

class WireTests(unittest.TestCase):
    def test_copper_dc_reference_and_scaling(self):
        # Independente Referenz: 100 Windungen, mittlerer Durchmesser 30 mm,
        # 1 mm Kupferdraht, 2 A -> 9,42478 m und 0,206892 Ohm.
        m=model.Magnet(coil_id=20,coil_od=40,coil_h=60,turns=100,current=2,wire_d_mm=1)
        w=model.wire_data(m)
        self.assertAlmostEqual(w['area_mm2'],math.pi/4)
        self.assertAlmostEqual(w['length_m'],3*math.pi)
        self.assertAlmostEqual(w['resistance20_ohm'],.206892)
        self.assertAlmostEqual(w['power20_w'],.827568)
        before=deepcopy(w);m.wire_d_mm=.5;m.current=-2
        w=model.wire_data(m)
        self.assertAlmostEqual(w['resistance20_ohm'],4*before['resistance20_ohm'])
        self.assertAlmostEqual(w['current_density_a_mm2'],4*before['current_density_a_mm2'])
        self.assertEqual(w['length_m'],before['length_m'])
        self.assertAlmostEqual(w['voltage20_v'],2*w['resistance20_ohm'])
        m.current=0;self.assertEqual(model.wire_data(m)['power20_w'],0)

    def test_impossible_wire_and_insulation_are_rejected(self):
        for key,value in [('wire_d_mm',0),('wire_d_mm',-1),('wire_d_mm',2),
                          ('wire_d_mm',float('nan')),('wire_d_mm',float('inf')),('wire_od_mm',.9),('wire_od_mm',2)]:
            c=model.Config();setattr(c.upper,key,value)
            self.assertTrue(model.validate(c)[0],(key,value))
        c=model.Config();c.upper.wire_d_mm=None;c.upper.wire_od_mm=1.1
        self.assertTrue(model.validate(c)[0])
        c=model.Config();c.upper.turns=1;c.upper.wire_d_mm=19
        self.assertTrue(any('einzelner Draht' in v for v in model.validate(c)[0]))
        c=model.Config();c.upper.wire_od_mm=1.1
        self.assertFalse(model.validate(c)[0]);self.assertTrue(any('Hoher' in v for v in model.validate(c)[1]))

    def test_legacy_settings_preserve_unknown_wire_and_roundtrip(self):
        c=model.Config();c.upper.wire_d_mm=.8;c.lower.wire_d_mm=.6;c.upper.wire_od_mm=.86
        data=model.settings_payload(c,model.DEFAULT_SWEEPS)
        loaded,_=model.parse_settings(json.loads(json.dumps(data)))
        self.assertEqual(loaded.to_dict(),c.to_dict())
        data['version']=1
        for side in ['upper','lower']:
            for key in model.electrical.MAGNET_FIELDS:del data['config'][side][key]
        for key in model.electrical.NUMERIC_FIELDS:del data['config']['numerics'][key]
        del data['config']['object']['enabled']
        for side in ['upper','lower']:
            for key in ['enabled','core_kind',*model.POT_KEYS]:del data['config'][side][key]
        for side in ['upper','lower']:
            for key in ['wire_d_mm','wire_od_mm']:del data['config'][side][key]
        loaded,_=model.parse_settings(data)
        self.assertIsNone(loaded.upper.wire_d_mm);self.assertIsNone(loaded.lower.wire_d_mm)
        self.assertIsNone(model.wire_data(loaded.upper));self.assertFalse(model.validate(loaded)[0])
        again,_=model.parse_settings(model.settings_payload(loaded,model.DEFAULT_SWEEPS))
        self.assertEqual(again.to_dict(),loaded.to_dict())

    def test_wire_diameter_does_not_change_magnetic_geometry(self):
        c=model.Config();before=model.Geometry(c)
        c.upper.wire_d_mm=.4;c.upper.wire_od_mm=.45
        after=model.Geometry(c)
        self.assertEqual(before.rectangles,after.rectangles)
        self.assertEqual(before.labels,after.labels)
        self.assertEqual(c.upper.turns,918);self.assertEqual(c.upper.current,2.81)

    def test_export_uses_saved_case_current_and_unknowns_are_blank(self):
        c=model.Config();c.upper.current=-1.5;c.upper.wire_d_mm=.7;c.lower.wire_d_mm=None
        case=dict(config=c.to_dict(),upper_current_a=-1.5,lower_current_a=c.lower.current,
                  mass_kg=.04,weight_n=.3924,magnetic_force_z_n=.4,net_force_n=.0076)
        saved={}
        class Capture(StringIO):
            def close(self):saved['csv']=self.getvalue();super().close()
        with patch('pathlib.Path.open',return_value=Capture()),patch('pathlib.Path.mkdir'),patch('pathlib.Path.replace'):
            model.export_job(dict(cases=[case]),'wire.csv')
        import csv
        row=next(csv.DictReader(StringIO(saved['csv']),delimiter=';'))
        self.assertEqual(float(row['Kupferdraht_oben_mm']),.7)
        self.assertAlmostEqual(float(row['Verlust20_oben_W']),model.wire_data(c.upper)['power20_w'])
        self.assertEqual(row['Kupferdraht_unten_mm'],'');self.assertEqual(row['R20_unten_Ohm'],'')

if __name__=='__main__':unittest.main(verbosity=2)
