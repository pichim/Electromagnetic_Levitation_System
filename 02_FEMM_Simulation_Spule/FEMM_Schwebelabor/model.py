"""Koaxiale Magnete mit Stab- oder offenem Topfkern: Parameter, Vorschau und serieller FEMM-Worker.

Längen mm, Eingabemasse g, Strom A; FEMM liefert Kraft in N für den ganzen
achsensymmetrischen Körper. Keine zusätzliche Tiefen- oder 2π-Skalierung.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from copy import deepcopy
from pathlib import Path
import csv
import json
import math
import os
import queue
import re
import shutil
import tempfile
import threading
import time
import traceback
import uuid

from core_types import CORE_TYPES, POT_KEYS, core_parts, shape_errors, enclosed_air_points
import electrical
import core_materials

MODEL_VERSION = "axisymmetric-electrical-v3-3c91-v1"
NOTICE = ("Ein Kräftegleichgewicht ist kein Nachweis stabilen geregelten Schwebens. "
          "Seitliche Stabilität und reale Erwärmung werden hier nicht nachgewiesen.")


@dataclass
class Magnet:
    core_d: float = 40.0
    core_l: float = 80.0
    coil_id: float = 42.0
    coil_od: float = 79.4
    coil_h: float = 60.0
    coil_offset: float = 10.0
    turns: int = 918
    current: float = 2.81
    material: str = "1010 Steel"
    wire_d_mm: float | None = 1.0
    wire_od_mm: float | None = None
    enabled: bool = True
    core_kind: str = "rod"
    pot_inner_d: float = 86.0
    pot_outer_d: float = 96.0
    pot_back_h: float = 10.0
    resistance20_ohm: float | None = None
    lead_resistance_ohm: float = 0.0
    temperature_c: float = 20.0
    voltage_limit_v: float | None = None

@dataclass
class Object:
    enabled: bool = True
    kind: str = "solid"
    diameter: float = 10.0
    wall: float = 1.0
    material: str = "1010 Steel"
    density: float = 7850.0
    measured_mass_g: float | None = None
    pm_d: float = 6.0
    pm_h: float = 2.0
    pm_z: float = 0.0
    pm_material: str = "NdFeB 37 MGOe"
    pm_direction: int = 1


@dataclass
class Numerics:
    mesh_mm: float = 0.6
    air_mesh_mm: float = 10.0
    domain_factor: float = 4.0
    arc_deg: float = 3.0
    solver_precision: float = 1e-8
    equilibrium_tolerance_n: float = 0.0002
    current_tolerance_a: float = 0.0001
    inductance_enabled: bool = True
    inductance_step_percent: float = 1.0
    inductance_min_step_a: float = 0.01


@dataclass
class Config:
    title: str = "Koaxiale Elektromagnete"
    upper_gap: float = 15.0
    lower_gap: float = 15.0
    upper: Magnet = field(default_factory=Magnet)
    lower: Magnet = field(default_factory=lambda: Magnet(current=0.393))
    object: Object = field(default_factory=Object)
    numerics: Numerics = field(default_factory=Numerics)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        d = deepcopy(data)
        for name, typ in [("upper", Magnet), ("lower", Magnet), ("object", Object), ("numerics", Numerics)]:
            if typ is Magnet:
                # Alte Dateien enthalten keinen gemessenen Drahtdurchmesser.
                d[name].setdefault("wire_d_mm", None)
                d[name].setdefault("wire_od_mm", None)
            d[name] = typ(**d[name])
        return cls(**d)


DEFAULT_SWEEPS = dict(current_start=0.0,current_end=4.0,current_step=.5,
                      gap_start=10.0,gap_end=20.0,gap_step=5.0,
                      search_start=0.0,search_end=6.0,scan_points=9)


# Ausgangswerte, keine Zusage einer bestimmten Kraftgenauigkeit.
MESH_PRESETS = {
    "Grob": (1.2,20.0,6.0,"Erster Stromsweep und Feldüberblick; Kräfte danach feiner prüfen."),
    "Standard": (0.6,10.0,3.0,"Normale Stromsweeps und erste Kraft-/Haltestromberechnungen."),
    "Fein": (0.3,5.0,1.5,"Kräfte, Halteströme und auffällige Kurvenstellen genauer prüfen."),
    "Sehr fein": (0.15,2.5,0.75,"Konvergenzvergleich mit Fein; besonders für ausgewählte Einzelfälle."),
}
MESH_FIELDS = ("mesh_mm","air_mesh_mm","arc_deg")


def mesh_profile(n):
    return next((name for name,values in MESH_PRESETS.items()
                 if all(getattr(n,key)==value for key,value in zip(MESH_FIELDS,values))),
                "Benutzerdefiniert")


def mesh_summary(n):
    return (f"Netz {mesh_profile(n)}: lokal {n.mesh_mm:.6g} mm, "
            f"äussere Luft {n.air_mesh_mm:.6g} mm, Bogen {n.arc_deg:.6g}°; "
            f"Luftbereich-Faktor {n.domain_factor:.6g}")


def settings_payload(c,sweeps):
    """Vollständige, geprüfte Eingaben; enthält keine Berechnungsergebnisse."""
    data=dict(format="femm-schwebelabor-settings",version=6,config=c.to_dict(),sweeps=dict(sweeps))
    parse_settings(data)
    return data


def parse_settings(data):
    """Erst vollständig prüfen, dann kann die Oberfläche atomar übernehmen."""
    if (not isinstance(data,dict) or set(data)!={"format","version","config","sweeps"}
            or data["format"]!="femm-schwebelabor-settings" or type(data["version"]) is not int or data["version"] not in {1,3,5,6}):
        raise ValueError("Keine unterstützte Schwebelabor-Einstellungsdatei (Version 1, 3, 5 oder 6).")
    def structure(value,example,path):
        if isinstance(example,dict):
            if not isinstance(value,dict) or set(value)!=set(example):
                raise ValueError(f"{path}: Felder fehlen oder sind unbekannt.")
            for key in example:structure(value[key],example[key],path+"."+key)
        elif isinstance(example,bool):
            if type(value) is not bool:raise ValueError(f"{path}: Häkchenwert true/false erforderlich.")
        elif isinstance(example,str):
            if not isinstance(value,str):raise ValueError(f"{path}: Text erforderlich.")
        elif value is None and (example is None or path.endswith(".wire_d_mm")):
            return
        elif type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError(f"{path}: endliche Zahl erforderlich.")
    example=Config().to_dict()
    if data["version"] < 6:
        for side in ["upper", "lower"]:
            for key in electrical.MAGNET_FIELDS:
                example[side].pop(key)
        for key in electrical.NUMERIC_FIELDS:
            example["numerics"].pop(key)
    if data["version"] in {1,3}:
        del example["object"]["enabled"]
        for side in ["upper","lower"]:
            for key in ["enabled","core_kind",*POT_KEYS]:del example[side][key]
    if data["version"]==1:
        for side in ["upper","lower"]:
            for key in ["wire_d_mm","wire_od_mm"]:del example[side][key]
    structure(data["config"],example,"Aufbau")
    structure(data["sweeps"],DEFAULT_SWEEPS,"Sweeps")
    c=Config.from_dict(data["config"]);sweeps=deepcopy(data["sweeps"])
    if c.object.enabled and c.object.pm_direction not in {-1,1}:
        raise ValueError("PM-Magnetisierung muss +z oder −z sein.")
    errors,_=validate(c)
    if errors:raise ValueError("Ungültiger gespeicherter Aufbau:\n"+"\n".join(errors))
    for kind in ["current","gap"]:
        opts=dict(start=sweeps[kind+"_start"],end=sweeps[kind+"_end"],step=sweeps[kind+"_step"],fixed_lower=c.lower.current)
        if kind=="gap":opts.update({k:sweeps[k] for k in ["search_start","search_end","scan_points"]})
        validate_options(kind,c,opts,require_active=False)
    return c,sweeps


def coordinates(c):
    h = c.object.diameter + c.upper_gap + c.lower_gap
    return dict(top=h/2, bottom=-h/2, center=(c.lower_gap-c.upper_gap)/2,
                upper_gap=c.upper_gap, lower_gap=c.lower_gap, h=h)


def normalize(config, changed=""):
    """Keine automatische Korrektur oder Kopplung von Benutzereingaben."""
    return deepcopy(config), []

def mass(c):
    o = c.object
    if not o.enabled:return 0.0
    if o.measured_mass_g is not None:
        return o.measured_mass_g/1000
    if o.kind == "pm":
        raise ValueError("PM-Kugel benötigt gemessene Gesamtmasse einschliesslich Hülle und Bauteilen.")
    r = o.diameter/2000
    ri = r-o.wall/1000 if o.kind == "hollow" else 0
    return 4*math.pi/3*(r**3-ri**3)*o.density


def lower_current(c):
    return c.lower.current if c.lower.enabled else 0.0


COPPER_RHO20 = 0.017241  # Ohm mm²/m; Kupfer, Referenz 20 °C, 100 % IACS.
ROUND_WIRE_MAX_FILL = math.pi / (2 * math.sqrt(3))


def wire_data(m):
    """Elektrische DC-Schätzung aus homogen verteilter runder Kupferwicklung.

    Der magnetostatische Solver verwendet weiterhin die eingegebenen N und I.
    Anschlussdrähte, Wicklungsenden, Temperaturanstieg und PWM sind nicht enthalten.
    """
    if not m.enabled or m.wire_d_mm is None:
        return None
    values=[m.wire_d_mm,m.coil_id,m.coil_od,m.coil_h,m.turns,m.current]
    if m.wire_od_mm is not None:values.append(m.wire_od_mm)
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Draht- und Wicklungswerte müssen endlich sein.")
    if m.wire_d_mm<=0:
        raise ValueError("Kupfer-Drahtdurchmesser muss grösser als 0 mm sein.")
    if not (m.coil_od>m.coil_id>0 and m.coil_h>0 and m.turns>=1 and int(m.turns)==m.turns):
        raise ValueError("Für Drahtwerte gültigen Wickelraum und ganzzahlige Windungszahl eingeben.")
    if m.wire_od_mm is not None and m.wire_od_mm<m.wire_d_mm:
        raise ValueError("Draht-Ø mit Lack muss mindestens dem Kupfer-Ø entsprechen.")
    try:
        area=math.pi*m.wire_d_mm**2/4
        length=m.turns*math.pi*(m.coil_id+m.coil_od)/2/1000
        window=(m.coil_od-m.coil_id)/2*m.coil_h
        copper_fill=m.turns*area/window
        insulated_fill=None if m.wire_od_mm is None else m.turns*math.pi*m.wire_od_mm**2/4/window
        resistance=COPPER_RHO20*length/area
        data=dict(area_mm2=area,length_m=length,resistance20_ohm=resistance,
                  power20_w=m.current**2*resistance,voltage20_v=abs(m.current)*resistance,
                  current_density_a_mm2=abs(m.current)/area,copper_fill=copper_fill,
                  insulated_fill=insulated_fill)
        if not all(v is None or math.isfinite(v) for v in data.values()):
            raise ValueError("Drahtwerte ausserhalb des berechenbaren Zahlenbereichs.")
        return data
    except (OverflowError,ZeroDivisionError):
        raise ValueError("Drahtwerte ausserhalb des berechenbaren Zahlenbereichs.") from None


def wire_issues(m):
    """Platzprüfung liefert notwendige Grenzen, keine Wickelgarantie."""
    if not m.enabled:return [],[]
    if m.wire_d_mm is None:
        if m.wire_od_mm is not None:
            return ["Kupfer-Ø eingeben, bevor ein Draht-Ø mit Lack angegeben wird."],[]
        return [],["Draht-Ø unbekannt: elektrische Schätzung und Wickelraumprüfung fehlen."]
    try:w=wire_data(m)
    except (ValueError,TypeError):
        # Geometrie/Windungszahl werden bereits in validate geprüft.
        if m.wire_d_mm<=0:
            return ["Kupfer-Drahtdurchmesser muss positiv sein oder leer bleiben."],[]
        if m.wire_od_mm is not None and m.wire_od_mm<m.wire_d_mm:
            return ["Draht-Ø mit Lack muss mindestens dem Kupfer-Ø entsprechen."],[]
        if m.coil_od>m.coil_id>0 and m.coil_h>0 and m.turns>=1 and int(m.turns)==m.turns:
            return ["Drahtwerte ausserhalb des berechenbaren Zahlenbereichs."],[]
        return [],[]
    diameter=m.wire_od_mm if m.wire_od_mm is not None else m.wire_d_mm
    if diameter>min((m.coil_od-m.coil_id)/2,m.coil_h):
        return ["Ein einzelner Draht passt nicht in die radiale Breite bzw. Höhe des Wickelraums."],[]
    fill=w["insulated_fill"] if w["insulated_fill"] is not None else w["copper_fill"]
    if fill>ROUND_WIRE_MAX_FILL+1e-10:
        return ["Draht und Windungszahl passen nicht in den Wickelraum (Füllgrad über der idealen Runddraht-Grenze 90,7 %)."],[]
    warnings=[]
    if fill>.75:
        warnings.append("Hoher Drahtfüllgrad: Wickelanordnung und realen Platzbedarf prüfen.")
    if m.wire_od_mm is None:
        warnings.append("Wickelraumprüfung ohne Lack; Draht-Ø mit Lack optional ergänzen.")
    return [],warnings


def wire_summary(m):
    if not m.enabled:return "Deaktiviert: Kern und Wicklung fehlen in Vorschau und Simulation."
    w=wire_data(m)
    if w is None:
        return "Draht-Ø unbekannt.\n"+electrical.summary(electrical.stationary(m))
    fill=w["insulated_fill"] if w["insulated_fill"] is not None else w["copper_fill"]
    return (f"Querschnitt {w['area_mm2']:.4g} mm² · Draht ca. {w['length_m']:.4g} m\n"
            f"Drahtschätzung R bei 20 °C ≈ {w['resistance20_ohm']:.4g} Ω\n"
            f"Drahtschätzung bei 20 °C und {abs(m.current):.4g} A: U ≈ {w['voltage20_v']:.4g} V · P ≈ {w['power20_w']:.4g} W\n"
            f"Stromdichte {w['current_density_a_mm2']:.4g} A/mm²\n"
            f"Füllgrad {'mit Lack' if m.wire_od_mm is not None else 'ohne Lack'}: {fill:.1%}\n\n"+
            electrical.summary(electrical.stationary(m,w)))


def validate(c, check_current=True):
    errors, warnings = [], []
    def finite(value):
        if isinstance(value, dict):
            return all(finite(v) for v in value.values())
        return not isinstance(value, (int, float)) or math.isfinite(value)
    if not finite(c.to_dict()):
        return ["Alle Zahlen müssen endlich sein (kein NaN/Inf)."], []
    library = material_names(metadata=True)
    def check_material(name, pm=False):
        material_note = core_materials.note(name)
        if material_note:
            warnings.append(material_note)
        if not name.strip():
            errors.append("FEMM-Material fehlt.")
        elif library:
            m = library.get(name)
            if m is None:
                errors.append(f"FEMM-Bibliotheksmaterial {name!r} ist nicht verfügbar.")
            elif pm and m["hc"] <= 0:
                errors.append(f"{name}: Permanentmagnetmaterial erforderlich.")
            elif not pm and (m["hc"] != 0 or (m["mu"] <= 1 and m["bh"] == 0)):
                errors.append(f"{name}: weichmagnetisches Kern-/Stahlmaterial erforderlich.")
    for name, m in [("Oben", c.upper), ("Unten", c.lower)]:
        if type(m.enabled) is not bool:errors.append(f"{name}: Aktivierung muss ein Häkchenwert sein.")
        if m.core_kind not in CORE_TYPES.values():errors.append(f"{name}: Unbekannte Kernform.")
        if not m.enabled:continue
        errors.extend(name+": "+text for text in electrical.errors(m))
        errors.extend(name+": "+text for text in shape_errors(m))
        if any(getattr(m, k) <= 0 for k in ["core_d", "core_l", "coil_id", "coil_od", "coil_h"]):
            errors.append(f"{name}: Durchmesser, Kernlänge und Wickelhöhe müssen positiv sein.")
        if m.coil_id < m.core_d:
            errors.append(f"{name}: Spulen-Innendurchmesser muss mindestens dem Kern-Durchmesser entsprechen.")
        if m.coil_od <= m.coil_id:
            errors.append(f"{name}: Spulen-Aussendurchmesser muss grösser als Innendurchmesser sein.")
        if m.coil_offset >= m.core_l or m.coil_offset+m.coil_h <= 0:
            errors.append(f"{name}: Wicklung muss den eigenen Kern axial zumindest teilweise umgeben.")
        if m.turns < 1 or int(m.turns) != m.turns:
            errors.append(f"{name}: positive ganzzahlige Windungszahl erforderlich.")
        check_material(m.material)
        wire_errors,wire_warnings=wire_issues(m)
        errors.extend(name+": "+text for text in wire_errors)
        warnings.extend(name+": "+text for text in wire_warnings)
    o = c.object
    if type(o.enabled) is not bool:errors.append("Objekt: Aktivierung muss ein Häkchenwert sein.")
    if o.kind not in {"solid","hollow","pm"}:errors.append("Unbekannter Objekttyp.")
    if o.diameter <= 0:errors.append("Referenz-Kugeldurchmesser muss positiv sein (bestimmt den Polabstand).")
    if o.enabled:
        if o.kind not in {"solid", "hollow", "pm"}:
            errors.append("Unbekannter Objekttyp.")
        if o.diameter <= 0:
            errors.append("Kugeldurchmesser muss positiv sein.")
        if o.kind == "hollow" and not 0 < o.wall < o.diameter/2:
            errors.append("Hohlkugel: 0 < Wandstärke < Kugelradius erforderlich.")
        if o.kind in {"solid", "hollow"}:
            check_material(o.material)
            if o.density <= 0:
                errors.append("Stahldichte muss positiv sein.")
        if o.measured_mass_g is not None and o.measured_mass_g <= 0:
            errors.append("Gemessene Gesamtmasse muss positiv sein; bei Stahl alternativ leerlassen.")
        if o.kind == "pm":
            if o.pm_d <= 0 or o.pm_h <= 0 or math.hypot(o.pm_d/2, abs(o.pm_z)+o.pm_h/2) >= o.diameter/2:
                errors.append("Scheibenmagnet passt nicht vollständig mit Freiraum in die Kugel.")
            if o.pm_direction not in {-1, 1}:
                errors.append("PM-Magnetisierung muss +z oder -z sein.")
            check_material(o.pm_material, pm=True)
            if o.measured_mass_g is None:
                errors.append("PM-Kugel: Gesamtmasse inklusive Magnet und Hülle eingeben.")
    if c.upper_gap <= 0 or c.lower_gap <= 0:
        errors.append("Oberflächen-Luftspalte müssen positiv sein; Objekt darf keinen Kern berühren.")
    n = c.numerics
    if type(n.inductance_enabled) is not bool:
        errors.append("Induktivitätsberechnung muss ein Häkchenwert sein.")
    if not .01 <= n.inductance_step_percent <= 10:
        errors.append("Induktivität: relative Stromänderung muss 0,01 bis 10 % sein.")
    if not 1e-5 <= n.inductance_min_step_a <= 1:
        errors.append("Induktivität: minimale Stromänderung muss 0,00001 bis 1 A sein.")
    if n.mesh_mm <= 0:
        errors.append("Lokale Netzgrösse muss grösser als 0 mm sein.")
    if n.air_mesh_mm <= 0:
        errors.append("Netzgrösse der äusseren Luft muss grösser als 0 mm sein.")
    if not 0.1 <= n.arc_deg <= 90:
        errors.append("Kreisbogen-Schritt muss zwischen 0,1° und 90° liegen.")
    if n.domain_factor < 2:
        errors.append("Luftbereich-Faktor muss mindestens 2 sein.")
    if min(n.equilibrium_tolerance_n,n.current_tolerance_a) <= 0:
        errors.append("Suchtoleranzen müssen positiv sein.")
    if not 1e-12 <= n.solver_precision <= 1e-4:
        errors.append("Ungültige Solverpräzision.")
    if not errors:
        g = Geometry(c)
        parts = [r for r in g.rectangles if r.group != OBJECT]
        for i, a in enumerate(parts):
            for b in parts[i+1:]:
                if min(a.r1,b.r1)-max(a.r0,b.r0) > 1e-9 and min(a.z1,b.z1)-max(a.z0,b.z0) > 1e-9:
                    errors.append(f"Bauteile überschneiden sich: {a.name} und {b.name}.")
            dz = max(a.z0-g.p["center"], g.p["center"]-a.z1, 0)
            if o.enabled and math.hypot(a.r0,dz) <= o.diameter/2+1e-9:
                errors.append(f"{a.name} berührt oder überschneidet das Schwebeobjekt.")
    warnings.append("Material und Dichte müssen zum realen Bauteil passen; Wicklung wird homogenisiert.")
    if o.enabled and o.kind == "pm":
        warnings.append("Nichtmagnetische Kugel als µr=1; Gesamtmasse beeinflusst ausschliesslich das Gewicht.")
    if not o.enabled:warnings.append("Objekt deaktiviert: reine Feldsimulation ohne Objektkraft und Gewicht. Polabstand bleibt anhand der Referenzabmessungen erhalten.")
    if any(m.enabled and m.core_kind=="pot" for m in [c.upper,c.lower]):
        warnings.append("Offener Topfkern: rotationssymmetrisch, Öffnung zum Objekt; keine Wicklungsschlitze, Bohrungen oder zweite Topfhälfte.")
    warnings.append(NOTICE)
    return errors, warnings

def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    tmp.replace(path)


def save_config(c, path):
    save_json(path, c.to_dict())


def load_config(path):
    return Config.from_dict(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def material_names(kind=None, metadata=False):
    """FEMM-Bibliothek plus app-eigene Materialien, ohne COM zu starten."""
    materials = {
        "1010 Steel": dict(mu=1, hc=0, bh=1),
        "Pure Iron": dict(mu=1, hc=0, bh=1),
        "NdFeB 37 MGOe": dict(mu=1.05, hc=900000, bh=0),
    }  # Nur Auswahl-/Validierungs-Fallback, keine Solver-Materialdefinitionen.
    paths = [Path("C:/femm42/bin/matlib.dat")]
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"femm.ActiveFEMM\CLSID") as k:
                clsid = winreg.QueryValue(k, None)
            for view in [winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY]:
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "CLSID\\"+clsid+"\\LocalServer32", 0, winreg.KEY_READ|view) as k:
                        command = winreg.QueryValue(k, None)
                    exe = command.split('"')[1] if command.startswith('"') else command.split(" /", 1)[0].split(" -", 1)[0].strip()
                    paths.insert(0, Path(exe).parent/"matlib.dat")
                except OSError:
                    pass
        except OSError:
            pass
    for path in paths:
        if path.is_file():
            materials = {}
            for block in re.findall(r'<BeginBlock>(.*?)<EndBlock>', path.read_text(encoding="cp1252", errors="replace"), re.S):
                name = re.search(r'<BlockName>\s*=\s*"([^"]+)"', block)
                if not name:
                    continue
                def number(tag, default=0):
                    hit = re.search(r'<'+tag+r'>\s*=\s*([^\s]+)', block)
                    return float(hit.group(1)) if hit else default
                materials[name.group(1)] = dict(mu=number("Mu_x", 1), hc=number("H_c"), bh=number("BHPoints"))
            break
    materials.update(core_materials.metadata())
    if metadata:
        return materials
    return sorted(name for name, m in materials.items() if kind is None or
                  (kind == "soft" and m["hc"] == 0 and (m["mu"] > 1 or m["bh"] > 0)) or
                  (kind == "pm" and m["hc"] > 0))


UPPER_CORE,UPPER_COIL,LOWER_CORE,LOWER_COIL,OBJECT,AIR = 10,11,20,21,30,0

@dataclass
class Rectangle:
    name: str
    r0: float
    r1: float
    z0: float
    z1: float
    material: str
    group: int
    circuit: str = "<None>"
    turns: int = 0
    direction: float = 0.0

    def inside(self,r,z):
        return self.r0<r<self.r1 and self.z0<z<self.z1

    @property
    def center(self): return ((self.r0+self.r1)/2,(self.z0+self.z1)/2)


@dataclass
class Circle:
    name: str
    radius: float
    z: float
    material: str
    group: int


class Geometry:
    def __init__(self,c: Config):
        self.config=c
        self.p=coordinates(c)
        self.rectangles=[]
        self.circles=[]
        self.labels=[]
        for side,m,pole,sgn,gcore,gcoil in [
            ("Oben",c.upper,self.p["top"],1,UPPER_CORE,UPPER_COIL),
            ("Unten",c.lower,self.p["bottom"],-1,LOWER_CORE,LOWER_COIL)]:
            if not m.enabled:continue
            for name,r0,r1,a0,a1 in core_parts(m):
                z0,z1=sorted([pole+sgn*a0,pole+sgn*a1])
                self.rectangles.append(Rectangle(side+" "+name,r0,r1,z0,z1,m.material,gcore))
            used_h=m.coil_h
            center=pole+sgn*(m.coil_offset+m.coil_h/2)
            r0=m.coil_id/2
            coil=Rectangle(side+" Wicklung",r0,m.coil_od/2,center-used_h/2,center+used_h/2,
                           "coil",gcoil,"Oben" if sgn==1 else "Unten",int(m.turns))
            self.rectangles.append(coil)
            for radius, axial in enclosed_air_points(m):
                self.labels.append((radius, pole+sgn*axial, "air", AIR, 0, "<None>", 0))
        o=c.object
        z=self.p["center"]
        r=o.diameter/2
        if o.enabled:
            self.circles.append(Circle("Kugel-Aussenfläche",r,z,o.material if o.kind!="pm" else "air",OBJECT if o.kind!="pm" else AIR))
            if o.kind=="hollow":
                self.circles.append(Circle("Hohlraum",r-o.wall,z,"air",AIR))
                self.labels.append((r-o.wall/2,z,o.material,OBJECT,0,"<None>",0))
                self.labels.append(((r-o.wall)/2,z,"air",AIR,0,"<None>",0))
            elif o.kind=="solid":
                self.labels.append((r/2,z,o.material,OBJECT,0,"<None>",0))
            elif o.kind=="pm":
                pm=Rectangle("Innenmagnet",0,o.pm_d/2,z+o.pm_z-o.pm_h/2,z+o.pm_z+o.pm_h/2,
                             o.pm_material,OBJECT,direction=90 if o.pm_direction==1 else 270)
                self.rectangles.append(pm)
                # Sichere Luftposition im Kugelschnitt, ausserhalb des Magneten.
                candidates=[(r*fr,z+r*fz) for fr in [.9,.7,.5,.1] for fz in [0,.7,-.7,.9,-.9]]
                ar,az=next((a,b) for a,b in candidates if a*a+(b-z)**2<r*r and not pm.inside(a,b))
                self.labels.append((ar,az,"air",AIR,0,"<None>",0))
        # Lokaler Luftkreis garantiert positive Distanz zu festen Kernen.
        gaps=[self.p["upper_gap"]]+[self.p["lower_gap"]]
        nearest = min((math.hypot(rect.r0, max(rect.z0-z, z-rect.z1, 0)) for rect in self.rectangles if rect.group != OBJECT), default=float("inf"))
        pad=max(1e-6, min(min(gaps)*.35, (nearest-r)*.35, max(r*.5,2)))
        self.refinement_radius=r+pad
        if o.enabled:
            self.circles.append(Circle("Luftverfeinerung",r+pad,z,"air",AIR))
            self.labels.append((r+pad/2,z,"air",AIR,0,"<None>",0))
        for rect in self.rectangles:
            a,b=rect.center
            self.labels.append((a,b,rect.material,rect.group,rect.direction,rect.circuit,rect.turns))
        self.rmax=max([r+pad]+[rect.r1 for rect in self.rectangles])
        self.zmin=min([z-r-pad]+[rect.z0 for rect in self.rectangles])
        self.zmax=max([z+r+pad]+[rect.z1 for rect in self.rectangles])
        center=(self.zmin+self.zmax)/2
        extent=max(self.rmax,(self.zmax-self.zmin)/2)
        self.domain_r=c.numerics.domain_factor*extent
        self.domain_z0=center-self.domain_r
        self.domain_z1=center+self.domain_r

    def view_limits(self):
        margin=max(self.rmax*.12,5)
        return (-self.rmax-margin,self.rmax+margin,self.zmin-margin,self.zmax+margin)

    def axis_nodes(self):
        zvalues={self.domain_z0,self.domain_z1}
        for rect in self.rectangles:
            if rect.r0==0: zvalues.update([rect.z0,rect.z1])
        for circle in self.circles: zvalues.update([circle.z-circle.radius,circle.z+circle.radius])
        return sorted(zvalues)

    def group_at(self,r,z):
        for rect in self.rectangles:
            if rect.inside(r,z): return rect.group
        o=self.config.object
        if not o.enabled:return AIR
        q=r*r+(z-self.p["center"])**2
        if o.kind=="solid" and q<(o.diameter/2)**2: return OBJECT
        if o.kind=="hollow" and (o.diameter/2-o.wall)**2<q<(o.diameter/2)**2: return OBJECT
        return AIR

    def label_checks(self):
        """Magnetische Blockzuordnung durch unabhängige Punktklassifikation prüfen."""
        return [f"Falsches Blocklabel bei ({r:g}, {z:g}) mm, Gruppe {group}."
                for r,z,mat,group,*_ in self.labels
                if group!=AIR and self.group_at(r,z)!=group]


from matplotlib.figure import Figure
from matplotlib.patches import Rectangle as PatchRectangle, Circle as PatchCircle
COLOURS={UPPER_CORE:"#74899c",LOWER_CORE:"#74899c",OBJECT:"#c4ccd2",11:"#dca563",21:"#dca563"}


def draw_geometry(ax,c,labels=True,filled=True):
    g=Geometry(c);o=c.object;p=g.p
    if o.enabled:
        ax.add_patch(PatchCircle((0,p["center"]),o.diameter/2,facecolor="#dce5eb" if filled else "none",edgecolor="#455867",lw=1.2,zorder=5))
        if o.kind=="hollow":
            ax.add_patch(PatchCircle((0,p["center"]),o.diameter/2-o.wall,facecolor="white" if filled else "none",edgecolor="#455867",lw=1,zorder=6))
    for rect in g.rectangles:
        colour="#bd6269" if rect.name=="Innenmagnet" else COLOURS.get(rect.group,"#dddddd")
        for sign in [-1,1]:
            r0=rect.r0 if sign==1 else -rect.r1
            ax.add_patch(PatchRectangle((r0,rect.z0),rect.r1-rect.r0,rect.z1-rect.z0,
                         facecolor=colour if filled else "none",edgecolor="#455867",lw=.8,zorder=7))
    ax.axvline(0,color="#94a1ac",linestyle="-.",lw=.7,zorder=9)
    if labels:
        # Text ausserhalb der Bauteile bleibt auch bei kleinen Kernen lesbar.
        xleft=-g.rmax-max(6,g.rmax*.15)
        for side,m,pole,sign in [("Oben",c.upper,p["top"],1),("Unten",c.lower,p["bottom"],-1)]:
            if not m.enabled:continue
            ax.text(xleft,pole+sign*m.core_l/2,side,ha="right",va="center",fontsize=9,color="#455867")
        xdim=g.rmax+max(6,g.rmax*.15)
        def dimension(a,b,label):
            mid=(a+b)/2
            ax.annotate("",xy=(xdim,a),xytext=(xdim,b),arrowprops=dict(arrowstyle="<->",color="#28678b",lw=1),zorder=10)
            ax.plot([o.diameter/2,xdim],[a,a],color="#b6c8d4",lw=.65,zorder=3)
            ax.plot([o.diameter/2,xdim],[b,b],color="#b6c8d4",lw=.65,zorder=3)
            # Nicht ueberlappende Textanker im Plotrand, mit Bezugslinie.
            ytext=max(mid,p["center"]+g.refinement_radius*1.2) if a>p["center"] else min(mid,p["center"]-g.refinement_radius*1.2)
            ax.annotate(label,xy=(xdim,mid),xytext=(xdim+5,ytext),ha="left",va="center",fontsize=9,
                        color="#28678b",arrowprops=dict(arrowstyle="-",lw=.6,color="#b6c8d4"))
        if o.enabled and c.upper.enabled:dimension(p["center"]+o.diameter/2,p["top"],f"Oben\n{p['upper_gap']:.4g} mm")
        if o.enabled and c.lower.enabled:dimension(p["bottom"],p["center"]-o.diameter/2,f"Unten\n{p['lower_gap']:.4g} mm")
        if o.enabled and o.kind=="pm":
            ax.annotate("",xy=(0,p["center"]+o.pm_z+o.pm_direction*o.pm_h*.45),xytext=(0,p["center"]+o.pm_z-o.pm_direction*o.pm_h*.45),arrowprops=dict(arrowstyle="->",lw=1.2,color="white"),zorder=12)
    ax.set_aspect("equal",adjustable="box")
    ax.set_xlabel("Schnittkoordinate [mm]",fontsize=9)
    ax.set_ylabel("z [mm]",fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True,alpha=.13)
    _,_,z0,z1=g.view_limits()
    lateral=g.rmax+max(28,g.rmax*.7)
    ax.set_xlim(-lateral,lateral+10);ax.set_ylim(z0,z1)
    return g


def geometry_info(c,section="setup"):
    """Massangaben zum gewählten Eingabereiter, ohne Solverzugriff."""
    if section in {"upper","lower"}:
        m=getattr(c,section);name="Oben" if section=="upper" else "Unten"
        if not m.enabled:return f"{name} deaktiviert – Kern und Wicklung werden nicht simuliert."
        core=(f"Topfkern · Mittelpol Ø {m.core_d:.5g} mm · Gesamthöhe {m.core_l:.5g} mm\n"
              f"Topf Ø innen/aussen {m.pot_inner_d:.5g}/{m.pot_outer_d:.5g} mm · Rückwand {m.pot_back_h:.5g} mm" if m.core_kind=="pot" else
              f"Kern Ø {m.core_d:.5g} mm · Länge {m.core_l:.5g} mm")
        return (f"{name} · {core}\n"
                f"Spule Ø innen {m.coil_id:.5g} mm · Ø aussen {m.coil_od:.5g} mm · Höhe {m.coil_h:.5g} mm · Position {m.coil_offset:+.5g} mm")
    if section=="object":
        o=c.object
        if not o.enabled:return f"Objekt deaktiviert – reine Feldsimulation. Referenz-Ø {o.diameter:.5g} mm bestimmt weiterhin den Polabstand."
        text=f"Kugel Ø {o.diameter:.5g} mm"
        if o.kind=="hollow":text+=f" · Wand {o.wall:.5g} mm"
        try:text+=f" · Gesamtmasse {mass(c)*1000:.5g} g"
        except ValueError:text+=" · Gesamtmasse fehlt"
        if o.kind=="pm":
            text+=f"\nInnenmagnet Ø {o.pm_d:.5g} mm · Dicke {o.pm_h:.5g} mm · Lage z {o.pm_z:+.5g} mm"
        return text
    p=coordinates(c)
    return (f"Luftspalt oben {c.upper_gap:.5g} mm · unten {c.lower_gap:.5g} mm\n"
            f"Polabstand H {p['h']:.5g} mm · Kugelmittelpunkt z {p['center']:+.5g} mm")


def geometry_measurement(ax,c,section,parameter=""):
    """Nur das aktive Mass markieren; keine Änderungen am FEMM-Modell."""
    p=coordinates(c);colour="#126faa"
    def arrow(a,b,label,offset=(0,12),rotation=0):
        ax.annotate("",xy=a,xytext=b,arrowprops=dict(arrowstyle="<->",color=colour,lw=1.5),zorder=15)
        mid=((a[0]+b[0])/2,(a[1]+b[1])/2)
        ax.annotate(label,xy=mid,xytext=offset,textcoords="offset points",ha="center",va="center",
                    fontsize=9,color=colour,rotation=rotation,zorder=16,
                    bbox=dict(boxstyle="round,pad=.25",facecolor="white",edgecolor=colour,alpha=.94))
    if section in {"upper","lower"}:
        m=getattr(c,section);sign=1 if section=="upper" else -1;pole=p["top"] if sign==1 else p["bottom"]
        if not m.enabled:return
        key=parameter.split(".")[-1] if parameter.startswith(section+".") else "core_d"
        if key in {"core_kind","enabled"}:key="pot_outer_d" if m.core_kind=="pot" else "core_d"
        zcore=pole+sign*m.core_l/2;start=pole+sign*m.coil_offset;end=start+sign*m.coil_h
        # Die aktiven Umrisse zeigen, ob das Mass zum Kern oder zur Spule gehört.
        coil=key.startswith("coil_") or key in {"turns","current"}
        r=m.coil_od/2 if coil else (m.pot_outer_d/2 if m.core_kind=="pot" else m.core_d/2)
        group=(UPPER_COIL if sign==1 else LOWER_COIL) if coil else (UPPER_CORE if sign==1 else LOWER_CORE)
        for rect in Geometry(c).rectangles:
            if rect.group!=group:continue
            for s in [-1,1]:
                x=rect.r0 if s==1 else -rect.r1
                ax.add_patch(PatchRectangle((x,rect.z0),rect.r1-rect.r0,rect.z1-rect.z0,fill=False,edgecolor=colour,lw=2,zorder=14))
        for text in list(ax.texts):
            if text.get_text()==("Oben" if sign==1 else "Unten"):text.remove()
        if key=="core_d":arrow((-m.core_d/2,zcore),(m.core_d/2,zcore),f"{'Mittelpol' if m.core_kind=='pot' else 'Kern'} Ø {m.core_d:.5g} mm")
        elif key=="core_l":arrow((-r-5,pole),(-r-5,pole+sign*m.core_l),f"{'Gesamthöhe' if m.core_kind=='pot' else 'Länge'} {m.core_l:.5g} mm",(-12,0),90)
        elif key in {"pot_inner_d","pot_outer_d"} and m.core_kind=="pot":
            d=getattr(m,key);zz=pole+sign*(m.core_l-m.pot_back_h)/2
            arrow((-d/2,zz),(d/2,zz),f"Topf Ø {'innen' if key=='pot_inner_d' else 'aussen'} {d:.5g} mm")
        elif key=="pot_back_h" and m.core_kind=="pot":
            x=m.pot_outer_d/2+5
            arrow((x,pole+sign*(m.core_l-m.pot_back_h)),(x,pole+sign*m.core_l),f"Rückwand {m.pot_back_h:.5g} mm",(12,0),90)
        elif key in {"coil_id","coil_od"}:
            d=getattr(m,key);z=(start+end)/2
            arrow((-d/2,z),(d/2,z),f"Spule Ø {'innen' if key=='coil_id' else 'aussen'} {d:.5g} mm")
        elif key=="coil_h":arrow((r+5,start),(r+5,end),f"Höhe {m.coil_h:.5g} mm",(12,0),90)
        elif key=="coil_offset":arrow((r+5,pole),(r+5,start),f"Position {m.coil_offset:+.5g} mm",(12,0),90)
    elif section=="object":
        o=c.object
        if not o.enabled:return
        z=p["center"];r=o.diameter/2;key=parameter.split(".")[-1] if parameter else "diameter"
        ax.add_patch(PatchCircle((0,z),r,fill=False,edgecolor=colour,lw=2,zorder=14))
        if key=="wall" and o.kind=="hollow":arrow((r-o.wall,z),(r,z),f"Wand {o.wall:.5g} mm",(0,-20))
        elif key.startswith("pm_") and o.kind=="pm":
            zm=z+o.pm_z
            if key=="pm_d":arrow((-o.pm_d/2,zm),(o.pm_d/2,zm),f"Magnet Ø {o.pm_d:.5g} mm",(0,-20))
            elif key=="pm_h":arrow((o.pm_d/2+2,zm-o.pm_h/2),(o.pm_d/2+2,zm+o.pm_h/2),f"Dicke {o.pm_h:.5g} mm",(50,0))
            elif key=="pm_z":arrow((o.pm_d/2+2,z),(o.pm_d/2+2,zm),f"Lage z {o.pm_z:+.5g} mm",(45,0))
        elif key in {"diameter","kind"}:arrow((-r,z),(r,z),f"Kugel Ø {o.diameter:.5g} mm",(0,-20))


def geometry_figure(c,figure=None,section="setup",parameter=""):
    from matplotlib.patches import Patch
    fig=figure or Figure(figsize=(7.6,7),dpi=100)
    fig.clear();ax=fig.add_subplot(111)
    draw_geometry(ax,c)
    geometry_measurement(ax,c,section,parameter)
    ax.set_title("Massstäbliche Geometrie",fontsize=11,pad=14)
    handles=[]
    if c.upper.enabled or c.lower.enabled:
        handles.extend([Patch(facecolor=COLOURS[UPPER_CORE],label="Kern"),
                        Patch(facecolor=COLOURS[UPPER_COIL],label="Wicklung")])
    if c.object.enabled:handles.append(Patch(facecolor="#dce5eb",label="Objekt"))
    if handles:ax.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,-.12),
                         ncol=3,frameon=False,fontsize=8)
    fig.subplots_adjust(left=.12,right=.94,bottom=.19,top=.90)
    return fig




import hashlib
import importlib.metadata
_LOCK=threading.Lock()

class FemmSession:
    """COM-Objekt wird im aufrufenden Worker erzeugt und dort wieder freigegeben.

    DispatchEx erzeugt eine eigene FEMM-Instanz. Der vorhandene FEMM-Desktop
    wird weder für Modelle benutzt noch durch closefemm geschlossen.
    """
    def __enter__(self):
        if os.name!="nt": raise RuntimeError("Solverbetrieb benötigt Windows mit FEMM 4.2. Vorschau bleibt verfügbar.")
        if not _LOCK.acquire(blocking=False): raise RuntimeError("Eine FEMM-Berechnung läuft bereits.")
        self.initialized=False
        self.connected=False
        self.mutex=None
        try:
            import ctypes
            # Prozessübergreifend: keine konkurrierenden pyFEMM-Aufrufe dieser Anwendung.
            self.kernel=ctypes.windll.kernel32
            self.kernel.CreateMutexW.restype=ctypes.c_void_p
            self.kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
            self.kernel.ReleaseMutex.argtypes=[ctypes.c_void_p]
            self.kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            self.mutex=self.kernel.CreateMutexW(None,False,"Local\\FEMM_Schwebelabor_Solver")
            status=self.kernel.WaitForSingleObject(self.mutex,0)
            if status not in (0,0x80): raise RuntimeError("Eine andere Schwebelabor-Instanz rechnet. Bitte dort fertig rechnen lassen.")
            self.owns_mutex=True
            import pythoncom
            import win32com.client
            import femm
            self.pythoncom=pythoncom
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            self.initialized=True
            self.femm=femm
            femm.HandleToFEMM=win32com.client.DispatchEx("femm.ActiveFEMM")
            self.connected=True
            femm.main_minimize()
            # Solverinstallation im Ergebnis dokumentieren: COM-Server/Executable.
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,r"femm.ActiveFEMM\CLSID") as k:
                clsid=winreg.QueryValue(k,None)
            command=""
            for view in [winreg.KEY_WOW64_32KEY,winreg.KEY_WOW64_64KEY,0]:
                try:
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,"CLSID\\"+clsid+"\\LocalServer32",0,winreg.KEY_READ|view) as k:
                        command=winreg.QueryValue(k,None)
                    break
                except FileNotFoundError:continue
            if not command:
                candidates=[Path("C:/femm42/bin/femm.exe"),Path(os.environ.get("ProgramFiles","C:/Program Files"))/"femm42/bin/femm.exe"]
                command=next((str(p) for p in candidates if p.is_file()),"COM-Server "+clsid)
            if command.startswith('"'): exe=command.split('"')[1]
            else: exe=command.split(" /",1)[0].split(" -",1)[0].strip()
            path=Path(exe)
            self.signature={"pyfemm":importlib.metadata.version("pyfemm"),"server":command,
                            "binary_sha256":hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else command}
            return self
        except Exception:
            self.__exit__(None,None,None)
            raise

    def __exit__(self,*exc):
        if self.connected:
            try: self.femm.closefemm()
            except Exception: pass
            self.femm.HandleToFEMM=None
        if self.initialized: self.pythoncom.CoUninitialize()
        if self.mutex:
            if getattr(self,"owns_mutex",False): self.kernel.ReleaseMutex(self.mutex)
            self.kernel.CloseHandle(self.mutex)
        _LOCK.release()



class Solver:
    def __init__(self, session, directory):
        self.session, self.f = session, session.femm
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.last = None

    def close_documents(self):
        for fun in [self.f.mo_close, self.f.mi_close]:
            try:
                fun()
            except Exception:
                pass

    def solve(self, c, progress=lambda text: None, field_image=False):
        errors, warnings = validate(c)
        if errors:
            raise ValueError("\n".join(errors))
        g = Geometry(c)
        if g.label_checks():
            raise ValueError("\n".join(g.label_checks()))
        directory = self.directory / (time.strftime("%Y%m%d_%H%M%S")+"_"+uuid.uuid4().hex[:8])
        directory.mkdir()
        started = time.monotonic()
        self.close_documents()
        try:
            progress("Gemeinsames achsensymmetrisches Modell aufbauen")
            self.build(c, g, directory)
            progress("FEMM vernetzt und löst magnetostatisch")
            self.f.mi_analyze(1)
            self.f.mi_loadsolution()
            self.f.mo_smooth("off")
            magnetic=volume=volume_error=0.0
            if c.object.enabled:
                progress("Weighted-Stress-Tensor auf Objektgruppe 30; Integral 19")
                self.f.mo_clearblock()
                self.f.mo_groupselectblock(OBJECT)
                magnetic = float(self.f.mo_blockintegral(19))
                volume = float(self.f.mo_blockintegral(10))
                self.f.mo_clearblock()
                volume_error = abs(volume-self.magnetic_volume(c))/self.magnetic_volume(c)
            else:
                progress("Objekt deaktiviert: reine Feldsimulation, keine Kraftauswertung")
            if volume_error > 0.02:
                raise RuntimeError(f"Objektvolumen weicht um {volume_error:.2%} ab; Blockauswahl/Netz prüfen.")
            if not math.isfinite(magnetic):
                raise RuntimeError("FEMM lieferte keine endliche Kraft.")
            mg = mass(c)*9.81
            result = dict(model_version=MODEL_VERSION, directory=str(directory.resolve()),
                          solver=self.session.signature, config=c.to_dict(), warnings=warnings,
                          upper_current_a=c.upper.current if c.upper.enabled else 0.0, lower_current_a=lower_current(c),
                          mass_kg=mass(c), weight_n=mg, magnetic_force_z_n=magnetic,
                          net_force_n=magnetic-mg, magnetic_volume_m3=volume,
                          volume_relative_error=volume_error, seconds=time.monotonic()-started)
            result["electrical"]={side:electrical.stationary(m,wire_data(m)) for side,m in [("upper",c.upper),("lower",c.lower)]}
            self.calculate_inductance(c, result, progress)
            for side, name in [("upper", "Oben"), ("lower", "Unten")]:
                data = result["electrical"][side]
                if data and data["within_voltage_limit"] is False:
                    warnings.append(name+": benötigte DC-Spannung überschreitet die verfügbare Spannung.")
            self.last = result
            if field_image:
                progress("FEMM-Felddaten für die Gesamtansicht auslesen")
                self.export_field_data(result)
            result["seconds"] = time.monotonic()-started
            return result
        except Exception:
            (directory/"error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise

    def calculate_inductance(self, c, result, progress=lambda text: None):
        """Central flux-linkage derivative on the unchanged geometry and mesh.

        Each other current is fixed. Using a separate input filename ensures
        force/field exports and the saved model retain the original operating
        point, not the last perturbation. No FEMM circuit voltage is used:
        the magnetic winding intentionally has zero conductivity.
        """
        active = [(side, name, getattr(c, side)) for side, name in [("upper", "Oben"), ("lower", "Unten")]
                  if getattr(c, side).enabled]
        if not active:
            return
        data = result["electrical"]
        try:
            for side, name, m in active:
                data[side]["flux_linkage_wb"] = electrical.circuit_flux(self.f.mo_getcircuitproperties(name))
        except Exception as error:
            for side, _, _ in active:
                data[side]["inductance_status"] = "FEMM-Flussverkettung nicht verfügbar: "+str(error)
            result["warnings"].append("Induktivität nicht verfügbar: "+str(error))
            return
        if not c.numerics.inductance_enabled:
            for side, _, _ in active:
                data[side]["inductance_status"] = "Berechnung im Reiter Netz abgeschaltet"
            return
        directory = Path(result["directory"])
        probe_dir = directory/"induktivitaet"
        probe_dir.mkdir()
        try:
            for side, name, m in active:
                delta = electrical.step(m.current, c.numerics)
                flux = []
                for sign in (1, -1):
                    progress(f"Induktivität {name}: Teststrom {m.current+sign*delta:+.6g} A (±{delta:.4g} A)")
                    self.f.mo_close()
                    for _, circuit, magnet in active:
                        self.f.mi_modifycircprop(circuit, 1, magnet.current)
                    self.f.mi_modifycircprop(name, 1, m.current+sign*delta)
                    self.f.mi_saveas(str((probe_dir/"probe.fem").resolve()))
                    self.f.mi_analyze(1)
                    self.f.mi_loadsolution()
                    flux.append({s:electrical.circuit_flux(self.f.mo_getcircuitproperties(n)) for s,n,_ in active})
                electrical.add_inductance(data[side], flux[0][side], flux[1][side], delta)
                for other, _, _ in active:
                    if other != side:
                        data[other]["mutual_inductance_h"] = (flux[0][other]-flux[1][other])/(2*delta)
                if data[side]["inductance_h"] is None:
                    result["warnings"].append(name+": "+data[side]["inductance_status"])
        except Exception as error:
            for side, _, _ in active:
                if data[side]["inductance_h"] is None:
                    data[side]["inductance_status"] = "Induktivitätsberechnung fehlgeschlagen: "+str(error)
            result["warnings"].append("Induktivitätsberechnung unvollständig: "+str(error))
        finally:
            # Restore original input AND its original solution, without solving
            # again or overwriting its .ans file with perturbed currents.
            self.close_documents()
            self.f.opendocument(str((directory/"model.fem").resolve()))
            self.f.mi_loadsolution()
            self.f.mo_smooth("off")
        result["inductance_matrix_h"] = [[
            data[a].get("inductance_h" if a == b else "mutual_inductance_h") if data[a] else None
            for b in ("upper", "lower")] for a in ("upper", "lower")]

    def export_field_data(self, result):
        """Originales FEMM-Netz, nodaler Fluss und elementweise Flussdichte.

        Die Lua-Schleifen laufen innerhalb von FEMM. Damit sind nicht tausende
        einzelner COM-Aufrufe nötig. Keine erneute Lösung oder Kraftänderung.
        mo_geta liefert im achsensymmetrischen Fall den Fluss 2πrA in Wb.
        """
        directory=Path(result["directory"])
        nodes=directory/"feld_knoten.csv"
        elements=directory/"feld_elemente.csv"
        def quoted(path):
            return '"'+path.resolve().as_posix().replace('"','\\"')+'"'
        script='\n'.join([
            'do',
            'local fn=openfile('+quoted(nodes)+',"w")',
            'local fe=openfile('+quoted(elements)+',"w")',
            'if fn==nil or fe==nil then error("Felddateien nicht schreibbar") end',
            'write(fn,"r_mm,z_mm,flux_Wb\\n")',
            'write(fe,"n1,n2,n3,B_T,group\\n")',
            'for i=1,mo_numnodes() do',
            'local r,z=mo_getnode(i)',
            'local flux=mo_getpointvalues(r,z)',
            'write(fn,format("%.16g,%.16g,%.16g\\n",r,z,flux))',
            'end',
            'for i=1,mo_numelements() do',
            'local n1,n2,n3,r,z,area,group=mo_getelement(i)',
            'local flux,br,bz=mo_getpointvalues(r,z)',
            'write(fe,format("%d,%d,%d,%.16g,%d\\n",n1,n2,n3,sqrt(br*br+bz*bz),group))',
            'end',
            'closefile(fn)',
            'closefile(fe)',
            'end'])
        self.f.mo_smooth("off")
        lua_file=directory/"export_feld.lua"
        lua_file.write_text(script+"\nreturn 1\n",encoding="utf-8")
        try:
            completed=self.f.callfemm("dofile("+quoted(lua_file)+")")
        except Exception as e:
            raise RuntimeError("FEMM-Feldexport fehlgeschlagen; Details in export_feld.lua und error.txt.") from e
        if completed!=1:
            raise RuntimeError("FEMM-Feldexport wurde nicht abgeschlossen.")
        if not nodes.is_file() or not elements.is_file():
            raise RuntimeError("FEMM-Felddaten konnten nicht exportiert werden.")
        result["field_data"]={"nodes":str(nodes.resolve()),"elements":str(elements.resolve())}

    def show_field(self, result, destination=None):
        """Native FEMM-Ansicht auf ausdrücklichen Klick; zusätzlich zur Python-Ansicht."""
        path = Path(result["directory"])/"model.ans"
        if not path.is_file():
            raise FileNotFoundError(f"Lösung fehlt: {path}")
        self.close_documents()
        self.f.opendocument(str(path.resolve()))
        self.f.main_restore()
        self.f.main_resize(1050, 850)
        self.f.mo_maximize()
        self.f.mo_smooth("off")
        self.f.hidepointprops()
        self.f.mo_showdensityplot(1, 0, 2.0, 0.0, "bmag")
        self.f.callfemm("mo_showcontourplot(-1)")
        self.f.callfemm("mo_shownames(0)")
        g = Geometry(Config.from_dict(result["config"]))
        _, r1, z0, z1 = g.view_limits()
        # Hauptfensteränderungen werden vom FEMM-GUI-Thread verarbeitet.
        time.sleep(0.15)
        self.f.mo_zoom(-r1*0.25, z0, r1*1.25, z1)
        self.f.mo_refreshview()
        if destination:
            destination = Path(destination)
            if destination.suffix.lower() != ".bmp":
                raise ValueError("Echtes FEMM-Feldbild als .bmp speichern.")
            self.f.mo_savebitmap(str(destination.resolve()))
            if not destination.is_file():
                raise RuntimeError("FEMM-Feldbild wurde nicht geschrieben.")

    def build(self,c,g,directory):
        f=self.f
        f.newdocument(0)
        f.mi_probdef(0,"millimeters","axi",c.numerics.solver_precision,0,30,0)
        f.mi_smartmesh(0)
        f.mi_addmaterial("air",1,1,0,0,0)
        f.mi_addmaterial("coil",1,1,0,0,0) # DC-Feld, elektrische Werte separat aus tatsächlichem Draht.
        names = {m.material for m in [c.upper,c.lower] if m.enabled}
        if c.object.enabled:names.add(c.object.pm_material if c.object.kind == "pm" else c.object.material)
        for name in sorted(names):
            if core_materials.add_to_femm(f, name):
                continue
            try: f.mi_getmaterial(name)
            except Exception as e: raise ValueError(f"FEMM-Bibliotheksmaterial {name!r} nicht verfügbar: {e}") from e
        if c.upper.enabled:f.mi_addcircprop("Oben",c.upper.current,1)
        if c.lower.enabled:f.mi_addcircprop("Unten",lower_current(c),1)
        f.mi_addboundprop("A0",0,0,0,0,0,0,0,0,0)
        nodes=set()
        segments=set()
        def part_mesh(group):
            size=c.numerics.mesh_mm
            for magnet,gcore in [(c.upper,UPPER_CORE),(c.lower,LOWER_CORE)]:
                if group==gcore and magnet.enabled and magnet.core_kind=="pot":
                    size=min(size,magnet.pot_back_h/3,(magnet.pot_outer_d-magnet.pot_inner_d)/6,magnet.core_d/6)
            return size
        def node(r,z):
            key=(round(r,10),round(z,10))
            if key not in nodes:
                f.mi_addnode(r,z);nodes.add(key)
        def segment(r0,z0,r1,z1,bound="",group=0,mesh=None):
            a,b=(round(r0,10),round(z0,10)),(round(r1,10),round(z1,10))
            key=tuple(sorted([a,b]))
            if key in segments:return
            node(r0,z0);node(r1,z1)
            f.mi_addsegment(r0,z0,r1,z1)
            f.mi_selectsegment((r0+r1)/2,(z0+z1)/2)
            f.mi_setsegmentprop(bound or "<None>",mesh if mesh is not None else part_mesh(group),0,0,group)
            f.mi_clearselected();segments.add(key)
        # Gemeinsame Teilkanten am Topf in identische Segmente zerlegen.
        vertices={(r,z) for rect in g.rectangles for r in (rect.r0,rect.r1) for z in (rect.z0,rect.z1)}
        def split_edge(a,b,group):
            points=[p for p in vertices if
                    (a[0]==b[0]==p[0] and min(a[1],b[1])<=p[1]<=max(a[1],b[1])) or
                    (a[1]==b[1]==p[1] and min(a[0],b[0])<=p[0]<=max(a[0],b[0]))]
            points=sorted(set([a,b]+points))
            for p,q in zip(points,points[1:]):segment(*p,*q,group=group)
        for rect in g.rectangles:
            r0,r1,z0,z1=rect.r0,rect.r1,rect.z0,rect.z1
            split_edge((r0,z0),(r1,z0),rect.group)
            split_edge((r1,z0),(r1,z1),rect.group)
            split_edge((r1,z1),(r0,z1),rect.group)
            if r0>0:split_edge((r0,z1),(r0,z0),rect.group)
        for circle in g.circles:
            r,z=circle.radius,circle.z
            points=[(0,z-r),(r,z),(0,z+r)]
            size=c.numerics.mesh_mm
            if c.object.kind=="hollow" and circle.group==OBJECT:size=min(size,c.object.wall/3)
            angle=min(c.numerics.arc_deg,math.degrees(size/r))
            for a,b in zip(points,points[1:]):
                node(*a);node(*b)
                f.mi_addarc(*a,*b,90,max(.1,angle))
                mid=(r/math.sqrt(2),z+(-1 if a[0]==0 else 1)*r/math.sqrt(2))
                f.mi_selectarcsegment(*mid)
                f.mi_setarcsegmentprop(max(.1,angle),"<None>",0,circle.group)
                f.mi_clearselected()
        # Eine vollständig zerlegte Achse verhindert überlappende Achsensegmente.
        znodes=g.axis_nodes()
        for a,b in zip(znodes,znodes[1:]):segment(0,a,0,b,"A0",mesh=c.numerics.mesh_mm)
        segment(0,g.domain_z0,g.domain_r,g.domain_z0,"A0",mesh=c.numerics.air_mesh_mm)
        segment(g.domain_r,g.domain_z0,g.domain_r,g.domain_z1,"A0",mesh=c.numerics.air_mesh_mm)
        segment(g.domain_r,g.domain_z1,0,g.domain_z1,"A0",mesh=c.numerics.air_mesh_mm)
        for r,z,mat,group,direction,circuit,turns in g.labels:
            mesh=part_mesh(group)
            if mat=="coil":mesh=max(mesh,1.0)
            if mat=="air" and group==0:mesh=c.numerics.mesh_mm
            if c.object.kind=="hollow" and group==OBJECT:mesh=min(mesh,c.object.wall/3)
            f.mi_addblocklabel(r,z);f.mi_selectlabel(r,z)
            f.mi_setblockprop(mat,0,mesh,circuit,direction,group,turns);f.mi_clearselected()
        f.mi_addblocklabel(g.domain_r*.85,(g.domain_z0+g.domain_z1)/2)
        f.mi_selectlabel(g.domain_r*.85,(g.domain_z0+g.domain_z1)/2)
        f.mi_setblockprop("air",0,c.numerics.air_mesh_mm,"<None>",0,0,0);f.mi_clearselected()
        # Feinere Luftpunkte nahe der Polflächen, ohne zusätzliche Materialgrenzen.
        for pole,sgn,m in [(g.p["top"],1,c.upper),(g.p["bottom"],-1,c.lower)]:
            if not m.enabled:continue
            for rr in [.25*m.core_d,.5*m.core_d+.3]:
                z=pole-sgn*min(1.0,g.p["upper_gap"]*.2 if sgn==1 else g.p["lower_gap"]*.2)
                if math.hypot(rr,z-g.p["center"])<=g.refinement_radius:continue
                f.mi_addnode(rr,z);f.mi_selectnode(rr,z);f.mi_setnodeprop("<None>",0);f.mi_clearselected()
                # Lokale Elementgrösse über Punkt-Umgebung gibt FEMM nicht vor;
                # Polflächen sind bereits mit mesh_mm segmentiert.
        f.mi_saveas(str((directory/"model.fem").resolve()))

    @staticmethod
    def magnetic_volume(c):
        o=c.object
        if not o.enabled:return 0.0
        if o.kind=="pm":return math.pi*(o.pm_d/2000)**2*(o.pm_h/1000)
        r=o.diameter/2000
        inner=r-o.wall/1000 if o.kind=="hollow" else 0
        return 4*math.pi/3*(r**3-inner**3)


def field_arrays(result):
    """Netz an r=0 spiegeln: achsensymmetrischer Meridianschnitt, keine neue FEM."""
    import numpy as np
    data=result.get("field_data")
    if not data:
        raise ValueError("Dieser Fall besitzt keine integrierte Feldansicht; einen Einzelfall berechnen.")
    nodes=np.loadtxt(data["nodes"],delimiter=",",skiprows=1,ndmin=2)
    elements=np.loadtxt(data["elements"],delimiter=",",skiprows=1,ndmin=2)
    if (nodes.shape[1]!=3 or elements.shape[1]!=5 or len(nodes)<3 or not len(elements)
            or not np.isfinite(nodes).all() or not np.isfinite(elements).all()
            or (nodes[:,0]<0).any() or (elements[:,3]<0).any()
            or not np.equal(elements[:,:3],np.floor(elements[:,:3])).all()
            or not np.equal(elements[:,4],np.floor(elements[:,4])).all()):
        raise ValueError("Ungültige FEMM-Felddateien.")
    triangles=elements[:,:3].astype(int)-1
    if triangles.min()<0 or triangles.max()>=len(nodes):
        raise ValueError("FEMM-Netz enthält ungültige Knotennummern.")
    right=nodes[:,0]>0
    mirror=np.arange(len(nodes))
    mirror[right]=len(nodes)+np.arange(right.sum())
    full_nodes=np.vstack([nodes,nodes[right]*np.array([-1,1,1])])
    full_triangles=np.vstack([triangles,mirror[triangles][:,[0,2,1]]])
    return full_nodes,full_triangles,np.tile(elements[:,3],2),np.tile(elements[:,4].astype(int),2)


def field_figure(result,figure=None,scale="log",whole_field=True):
    """Flusskonturen auf dem echten FEMM-Netz, gemeinsam mit derselben Geometrie.

    Turbo zeigt schwache Felder blau und starke rot. Standard: logarithmisch
    über drei Dekaden, auch in den Bauteilen. FEMM-Werte bleiben unverändert.
    """
    import numpy as np
    from matplotlib.tri import Triangulation
    from matplotlib.patches import Patch
    from matplotlib.colors import LogNorm, Normalize
    from matplotlib import colormaps, patheffects
    from matplotlib.ticker import NullLocator
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    from field_measurements import FieldSampler
    nodes,triangles,bmag,groups=field_arrays(result)
    c=Config.from_dict(result["config"])
    fig=figure or Figure(figsize=(8.5,7.5),dpi=100)
    fig.clear();ax=fig.add_subplot(111)
    if scale not in {"log","linear"}:
        raise ValueError("Unbekannte Feldfarbskala.")
    draw_geometry(ax,c,filled=not whole_field)
    ax.grid(False)
    ax.field_domain=(float(nodes[:,0].min()),float(nodes[:,0].max()),
                     float(nodes[:,1].min()),float(nodes[:,1].max()))
    tri=Triangulation(nodes[:,0],nodes[:,1],triangles)
    ax.field_sampler=FieldSampler(tri,bmag)
    centers=nodes[triangles,:2].mean(axis=1)
    x0,x1=ax.get_xlim();z0,z1=ax.get_ylim()
    visible=((groups==AIR) | whole_field)&(centers[:,0]>=x0)&(centers[:,0]<=x1)&(centers[:,1]>=z0)&(centers[:,1]<=z1)
    maximum=float(bmag[visible].max()) if visible.any() else 0
    use_log=scale=="log" and maximum>0
    lower=maximum/1000 if use_log else 0
    norm=LogNorm(lower,maximum) if use_log else Normalize(0,max(maximum,1e-9))
    cmap=colormaps["turbo"].copy()
    cmap.set_under(cmap(0.0));cmap.set_over(cmap(1.0))
    # Log(0) ist undefiniert: Nullwerte bekommen nur für die Farbdarstellung
    # einen Wert unterhalb der Skala, statt weiss/transparent zu verschwinden.
    # Glatte Anzeige aus flächengewichteten Nachbarelementen. Für jede
    # Materialgruppe separat: an Luft/Eisen-Grenzen wird nicht gemittelt.
    # Das exportierte FEMM-Netz, B-Werte und sämtliche Kräfte bleiben unverändert.
    xy=nodes[triangles,:2]
    u=xy[:,1]-xy[:,0];v=xy[:,2]-xy[:,0]
    areas=abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])/2
    colour=None
    for group in np.unique(groups) if whole_field else [AIR]:
        selected=groups==group
        if not selected.any():continue
        corners=triangles[selected].ravel()
        weights=np.repeat(areas[selected],3)
        sums=np.bincount(corners,weights=weights*np.repeat(bmag[selected],3),minlength=len(nodes))
        totals=np.bincount(corners,weights=weights,minlength=len(nodes))
        smooth=np.divide(sums,totals,out=np.zeros(len(nodes)),where=totals>0)
        display_b=np.where(smooth>0,smooth,lower/10) if use_log else smooth
        group_tri=Triangulation(nodes[:,0],nodes[:,1],triangles,mask=~selected)
        layer=ax.tripcolor(group_tri,display_b,shading="gouraud",cmap=cmap,norm=norm,zorder=0)
        if group==AIR or colour is None:colour=layer
    ax.field_scale="log" if use_log else "linear"
    ax.field_colour_note=("Logarithmisch · gleiche Farbintervalle = gleiche Faktoren · "
                          "untere Farbgrenze schliesst 0 T ein" if use_log else
                          "Nullfeld: überall 0 T" if maximum==0 else
                          "Linear · gleiche Farbintervalle = gleiche Unterschiede")
    ax.field_colour=colour
    if whole_field:
        # Die Konturen bleiben auf hellen und dunklen Feldfarben lesbar.
        for patch in ax.patches:
            patch.set_edgecolor("#172331")
            patch.set_path_effects([patheffects.withStroke(linewidth=2,foreground="white",alpha=.7)])
    psi=nodes[:,2]
    visible_nodes=(nodes[:,0]>=x0)&(nodes[:,0]<=x1)&(nodes[:,1]>=z0)&(nodes[:,1]<=z1)
    low,high=float(psi[visible_nodes].min()),float(psi[visible_nodes].max())
    if high-low>1e-18:
        levels=np.linspace(low,high,23)[1:-1]
        contours=ax.tricontour(tri,psi,levels=levels,colors="#172331",linewidths=.5,alpha=.8,zorder=10)
        effects=[patheffects.withStroke(linewidth=1.1,foreground="white",alpha=.35)]
        if hasattr(contours,"set_path_effects"):
            contours.set_path_effects(effects)
        else:
            for collection in contours.collections:collection.set_path_effects(effects)
    # Eine an die tatsächliche Schnittbreite angehängte Skala hält den
    # Aufbau mittig, auch wenn das Fenster sehr breit oder hoch ist.
    cax=make_axes_locatable(ax).append_axes("right",size="4%",pad=.15)
    cb=fig.colorbar(colour,cax=cax,extend="min" if use_log else "neither")
    cb.ax.set_navigate(False)
    cb.set_label("|B| [T]"+(" · logarithmisch" if use_log else " · linear"),fontsize=9)
    cb.ax.set_title("stark",fontsize=8,pad=0)
    # Die logarithmische Skala besitzt eine Spitze unterhalb ihrer Achse.
    # Relativer Abstand hält das Wort auch bei grosser Fensterhöhe darunter.
    cb.ax.field_weak_label=cb.ax.text(.5,-.085,"schwach",transform=cb.ax.transAxes,
                                     ha="center",va="top",fontsize=8,clip_on=False)
    if use_log:
        decades=10.0**np.arange(math.ceil(math.log10(lower)),math.floor(math.log10(maximum))+1)
        ticks=[lower]+[float(v) for v in decades if
                       math.log10(v/lower)>.17 and math.log10(maximum/v)>.17]+[maximum]
        cb.set_ticks(ticks)
        cb.set_ticklabels(["≤ "+format(lower,".3g")]+[format(v,".3g") for v in ticks[1:]])
        cb.ax.yaxis.set_minor_locator(NullLocator())
    elif maximum==0:
        cb.set_ticks([0]);cb.set_ticklabels(["0"])
    cb.ax.tick_params(labelsize=8)
    for text in ax.texts:
        text.set_clip_on(True)
        if text.get_text():
            text.set_zorder(12)
            text.set_bbox(dict(facecolor="white",edgecolor="none",alpha=.85,pad=1))
    fig.suptitle("Magnetische Flussdichte und Feldlinien",fontsize=11,y=.99)
    handles=[]
    if not whole_field and (c.upper.enabled or c.lower.enabled):
        handles.extend([Patch(facecolor=COLOURS[UPPER_CORE],label="Kern"),
                        Patch(facecolor=COLOURS[UPPER_COIL],label="Wicklung")])
    if c.object.enabled and not whole_field:handles.append(Patch(facecolor="#dce5eb",label="Objekt"))
    if handles:ax.legend(handles=handles,loc="upper center",bbox_to_anchor=(.5,-.12),
                         ncol=3,frameon=False,fontsize=8)
    if whole_field:
        note=("Farbe zeigt |B| in allen Materialien · Bauteile als Konturen\n"+
              ("logarithmisch, untere Grenze inkl. 0 T" if use_log else "Nullfeld" if maximum==0 else "linear")+
              " · geglättete Anzeige")
    else:
        note="Feldfarben nur in Luft · "+("logarithmisch" if use_log else "Nullfeld" if maximum==0 else "linear")+" · geglättete Anzeige"
    fig.text(.5,.025,note,ha="center",fontsize=8,color="#596773")
    fig.subplots_adjust(left=.11,right=.91,bottom=.19,top=.90)
    return fig


class Cancelled(Exception):
    pass


def sweep_values(start, end, step):
    if not all(math.isfinite(x) for x in [start, end, step]) or step <= 0 or end < start:
        raise ValueError("Sweep: Ende ≥ Start und Schrittweite > 0 erforderlich.")
    count = int(math.floor((end-start)/step+1e-9))+1
    if count > 1000:
        raise ValueError("Maximal 1000 Sweep-Punkte; Schrittweite vergrössern.")
    values = [start+i*step for i in range(count)]
    if values[-1] < end-1e-9:
        values.append(end)
    return values


def validate_options(kind, c, options, require_active=True):
    if require_active and (not c.object.enabled or not c.upper.enabled):
        raise ValueError("Strom- und Haltestrom-Sweeps benötigen die obere Spule und ein aktives Objekt. Ohne Objekt einen Einzelfall für das Magnetfeld berechnen.")
    sweep_values(options["start"], options["end"], options["step"])
    if not math.isfinite(options["fixed_lower"]):
        raise ValueError("Fester unterer Strom muss endlich sein.")
    cc = deepcopy(c)
    cc.upper.current = 0
    cc.lower.current = options["fixed_lower"]
    errors, _ = validate(cc)
    if errors:
        raise ValueError("\n".join(errors))
    if kind == "gap":
        if options["start"] <= 0:
            raise ValueError("Luftspalte müssen > 0 sein.")
        lo, hi, n = (options[x] for x in ["search_start", "search_end", "scan_points"])
        if not all(math.isfinite(x) for x in [lo, hi, n]) or hi <= lo or int(n) != n or not 3 <= n <= 101:
            raise ValueError("Haltestromsuche: Ende > Start, 3–101 ganzzahlige Grobscanpunkte.")


def at_gap(base, gap):
    c = deepcopy(base)
    c.upper_gap = c.lower_gap = gap
    return c

def find_roots(c, options, evaluate, cancel):
    """Endlicher Scan, Vorzeichenintervalle und lokale Residualminima.

    Jede akzeptierte Lösung besitzt eine tatsächliche FEMM-Einzelberechnung.
    Ungültige Scanpunkte unterbrechen die Intervallsuche; es wird nie über sie
    hinweg interpoliert. Sehr schmale Äste können im endlichen Scan fehlen.
    """
    if not c.object.enabled or not c.upper.enabled:
        raise ValueError("Haltestromsuche benötigt ein aktives Objekt und die obere Spule.")
    memo, scans, errors = {}, [], []
    target = mass(c)*9.81
    tolerance = c.numerics.equilibrium_tolerance_n

    def calc(i, phase):
        if cancel.is_set():
            raise Cancelled()
        key = round(i, 12)
        if key not in memo:
            case = deepcopy(c)
            case.upper.current = float(i)
            invalid, _ = validate(case)
            if invalid:
                memo[key] = None
                errors.append(dict(current_a=float(i), errors=invalid))
            else:
                memo[key] = evaluate(case, phase)
        return memo[key]

    n = int(options["scan_points"])
    xs = [options["search_start"]+j*(options["search_end"]-options["search_start"])/(n-1) for j in range(n)]
    coarse = [calc(i, "Grobstromscan") for i in xs]
    residuals = [r["magnetic_force_z_n"]-target if r else None for r in coarse]
    for i, r in zip(xs, coarse):
        scans.append(dict(current_a=i, force_n=r["magnetic_force_z_n"] if r else None,
                          status="berechnet" if r else "ungültiger Strom", directory=r["directory"] if r else None))
    roots = []

    def accept(i, r, method):
        if r and abs(r["magnetic_force_z_n"]-target) <= tolerance:
            if not any(abs(i-a["current_a"]) <= c.numerics.current_tolerance_a*2 for a in roots):
                case=deepcopy(c);case.upper.current=float(i)
                data={s:result_electrical(r,s) if "config" in r else electrical.stationary(getattr(case,s),wire_data(getattr(case,s)))
                      for s in ("upper","lower")}
                active=[e for e in data.values() if e]
                feasible=False if any(e["within_voltage_limit"] is False for e in active) else None if any(e["within_voltage_limit"] is None for e in active) else True
                roots.append(dict(current_a=float(i), force_n=r["magnetic_force_z_n"],
                                  residual_n=r["magnetic_force_z_n"]-target, directory=r["directory"], method=method,
                                  electrical=data, within_voltage_limit=feasible))

    for i, r in zip(xs, coarse):
        accept(i, r, "Grobstromscan; FEMM direkt")
    for j in range(n-1):
        a, b, fa, fb = xs[j], xs[j+1], residuals[j], residuals[j+1]
        if fa is None or fb is None or fa*fb >= 0 or abs(fa) <= tolerance or abs(fb) <= tolerance:
            continue
        for _ in range(45):
            mid = (a+b)/2
            r = calc(mid, "Vorzeichenintervall verfeinern")
            if not r:
                break
            fm = r["magnetic_force_z_n"]-target
            if abs(fm) <= tolerance:
                accept(mid, r, "Bisektion; FEMM nachgerechnet")
                break
            if b-a <= c.numerics.current_tolerance_a:
                break
            if fa*fm <= 0:
                b, fb = mid, fm
            else:
                a, fa = mid, fm
    # Tangentiale Gleichgewichte: erkennbare lokale Minima ohne Vorzeichenwechsel.
    phi = (math.sqrt(5)-1)/2
    for j in range(1, n-1):
        left, mid, right = residuals[j-1:j+2]
        if any(x is None for x in [left, mid, right]):
            continue
        if abs(mid) <= tolerance:
            continue  # Dieser Scanpunkt wurde bereits als Gleichgewicht akzeptiert.
        if not (abs(mid) < abs(left) and abs(mid) < abs(right)) or left*mid <= 0 or mid*right <= 0:
            continue
        a, b = xs[j-1], xs[j+1]
        u, v = b-phi*(b-a), a+phi*(b-a)
        ru, rv = calc(u, "Residualminimum suchen"), calc(v, "Residualminimum suchen")
        for _ in range(32):
            if not ru or not rv:
                break
            best_i, best = (u, ru) if abs(ru["magnetic_force_z_n"]-target) <= abs(rv["magnetic_force_z_n"]-target) else (v, rv)
            if abs(best["magnetic_force_z_n"]-target) <= tolerance:
                accept(best_i, best, "Residualminimum; FEMM nachgerechnet")
                break
            if b-a <= c.numerics.current_tolerance_a:
                break
            if abs(ru["magnetic_force_z_n"]-target) < abs(rv["magnetic_force_z_n"]-target):
                b, v, rv = v, u, ru
                u = b-phi*(b-a)
                ru = calc(u, "Residualminimum suchen")
            else:
                a, u, ru = u, v, rv
                v = a+phi*(b-a)
                rv = calc(v, "Residualminimum suchen")
    roots.sort(key=lambda r: r["current_a"])
    valid = [r for r in memo.values() if r]
    return dict(roots=roots, scans=scans, scan_errors=errors, target_n=target,
                status="Gleichgewicht gefunden" if roots else "nicht erreichbar im untersuchten Scan / kein Gleichgewicht erkannt",
                max_sampled_force_n=max((r["magnetic_force_z_n"] for r in valid), default=None),
                min_abs_residual_n=min((abs(r["magnetic_force_z_n"]-target) for r in valid), default=None),
                search_note="Endlicher Scan; schmale Äste können fehlen. Strom- und Krafttoleranz sowie Netz prüfen.")


def run_job(kind, c, options, solver, cancel, emit=lambda kind, data: None):
    started = time.monotonic()
    directory = solver.directory.parent
    job = dict(kind=kind, config=c.to_dict(), options=deepcopy(options), cases=[], summary=[], accuracy=[],
               status="läuft", directory=str(directory.resolve()), model_version=MODEL_VERSION)
    if kind == "force_map":
        from force_map import validate_options as validate_map
        validate_map(c, options)
        job["map_errors"] = []
    emit("job", deepcopy(job))
    current_x = None

    def evaluate(case, phase):
        if cancel.is_set():
            raise Cancelled()
        p = coordinates(case)
        prefix = (f"Fall {len(job['cases'])+1} / {phase}: I oben={case.upper.current if case.upper.enabled else 0:+.5g} A, "
                  f"I unten={lower_current(case):+.5g} A, g oben={p['upper_gap']:.5g} mm")
        emit("progress", prefix)
        result = solver.solve(case, lambda text: emit("progress", prefix+" · "+text), field_image=kind == "single")
        result["phase"], result["sweep_x"] = phase, current_x
        job["cases"].append(result)
        emit("case", deepcopy(result))
        return result

    def summary(row):
        job["summary"].append(row)
        emit("summary", deepcopy(row))

    try:
        if kind == "single":
            evaluate(c, "Einzelberechnung")
        elif kind == "accuracy":
            base = evaluate(c, "Basisnetz")
            fine = deepcopy(c)
            fine.numerics.mesh_mm *= 0.5
            fine.numerics.air_mesh_mm *= 0.5
            fine.numerics.arc_deg *= 0.5
            refined = evaluate(fine, "Feineres Netz")
            bigger = deepcopy(fine)
            bigger.numerics.domain_factor *= 1.5
            expanded = evaluate(bigger, "Feines Netz und grösserer Luftbereich")
            for label, a, b in [("Netzverfeinerung", base, refined), ("Grösserer Luftbereich", refined, expanded)]:
                delta = b["magnetic_force_z_n"]-a["magnetic_force_z_n"]
                reference = abs(b["magnetic_force_z_n"])
                row = dict(check=label, base_force_n=a["magnetic_force_z_n"], checked_force_n=b["magnetic_force_z_n"],
                           signed_change_n=delta, absolute_change_n=abs(delta),
                           relative_change=abs(delta)/reference if reference > 1e-12 else None,
                           base_directory=a["directory"], checked_directory=b["directory"])
                job["accuracy"].append(row)
        elif kind == "force_map":
            from force_map import axes as map_axes, case_at
            currents, gaps = map_axes(options)
            for gap in gaps:
                for current in currents:
                    current_x = current
                    case = case_at(c, options, current, gap)
                    try:
                        r = evaluate(case, f"Kraftkennfeld {len(job['cases'])+1}/{len(currents)*len(gaps)}")
                    except Cancelled:
                        raise
                    except Exception as error:
                        job["map_errors"].append(dict(current_a=current, gap_mm=gap, error=str(error)))
                        raise
                    summary(dict(x=current, current_a=current, gap_mm=gap,
                                 status="berechnet", force_n=r["magnetic_force_z_n"],
                                 directory=r["directory"]))
        elif kind in {"current", "gap"}:
            validate_options(kind, c, options)
            base = deepcopy(c)
            base.lower.current = options["fixed_lower"]
            for x in sweep_values(options["start"], options["end"], options["step"]):
                if cancel.is_set():
                    raise Cancelled()
                current_x = x
                case = deepcopy(base) if kind == "current" else at_gap(base, x)
                if kind == "current":
                    case.upper.current = x
                    errors, _ = validate(case)
                    if errors:
                        summary(dict(x=x, status="ungültig", errors=errors, lower_current_a=lower_current(case)))
                        continue
                    r = evaluate(case, "Stromsweep")
                    summary(dict(x=x, status="berechnet", force_n=r["magnetic_force_z_n"],
                                 weight_n=r["weight_n"], lower_current_a=lower_current(case), directory=r["directory"]))
                else:
                    errors, _ = validate(case, check_current=False)
                    if errors:
                        summary(dict(x=x, status="ungültige Geometrie", errors=errors, roots=[]))
                        continue
                    row = find_roots(case, options, evaluate, cancel)
                    row.update(x=x, lower_current_a=lower_current(case), centered=True)
                    summary(row)
        else:
            raise ValueError("Unbekannter Auftrag.")
        job["status"] = "Fertig"
    except Cancelled:
        job["status"] = "Abgebrochen; abgeschlossene Ergebnisse erhalten"
    except Exception as e:
        job["status"] = "Fehler: "+str(e)
        (directory/"error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    finally:
        job["seconds"] = time.monotonic()-started
        emit("done", deepcopy(job))
    return job


class Worker:
    """Ein langlebiger Worker; alle COM-Zugriffe bleiben in dessen STA-Thread.

    Nach Einzelberechnungen bleibt die eigene FEMM-Lösung zur Ansicht offen.
    Kein Zugriff auf die Instanz eines schon geöffneten FEMM-Fensters.
    """
    def __init__(self, events):
        self.events, self.commands = events, queue.Queue()
        self.cancel, self.stop = threading.Event(), threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True, name="FEMM-COM-Worker")
        self.thread.start()

    def submit(self, kind, config, options):
        self.cancel.clear()
        self.commands.put((kind, deepcopy(config), deepcopy(options)))

    def shutdown(self):
        self.stop.set()
        self.cancel.set()
        self.commands.put(None)

    def _loop(self):
        session = None
        workspace = tempfile.TemporaryDirectory(prefix="FEMM_Schwebelabor_")
        output = Path(workspace.name)
        try:
            while not self.stop.is_set():
                command = self.commands.get()
                if command is None or self.stop.is_set():
                    break
                kind, c, options = command
                try:
                    if session is None:
                        self.events.put(("progress", "Eigene FEMM-COM-Instanz starten"))
                        session = FemmSession().__enter__()
                    if kind == "field":
                        solver = Solver(session, output/"faelle")
                        solver.show_field(options["result"], options.get("destination"))
                        self.events.put(("field_done", options.get("destination")))
                    else:
                        directory = output/(time.strftime("%Y%m%d_%H%M%S")+"_"+kind+"_"+uuid.uuid4().hex[:6])
                        directory.mkdir(parents=True, exist_ok=True)
                        solver = Solver(session, directory/"faelle")
                        run_job(kind, c, options, solver, self.cancel, lambda k, d: self.events.put((k, d)))
                except Exception as e:
                    self.events.put(("error", str(e)))
                    if session:
                        session.__exit__(None, None, None)
                        session = None
        finally:
            try:
                if session:
                    session.__exit__(None, None, None)
            finally:
                workspace.cleanup()


def save_job(job, destination):
    """Explicitly save a complete, portable result without changing the live job.

    FEMM needs temporary .fem/.ans files while computing. Only this function
    creates permanent job exports. A unique child folder avoids overwriting
    earlier measurements; failed writes do not leave a partial result folder.
    """
    if not job.get("cases"):
        raise ValueError("Keine abgeschlossenen Ergebnisse zum Speichern.")
    destination = Path(destination).resolve()
    if not destination.is_dir():
        raise ValueError("Bitte einen vorhandenen Zielordner wählen.")
    name = Path(job["directory"]).name
    target = destination/name
    if target.exists():
        target = destination/(name+"_"+uuid.uuid4().hex[:6])
    stage = Path(tempfile.mkdtemp(prefix=".schwebelabor_", dir=destination))
    stored = deepcopy(job)
    old_root = Path(job["directory"]).resolve()

    def relocate(value):
        if isinstance(value, dict):
            return {k: relocate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relocate(v) for v in value]
        if isinstance(value, str):
            try:
                relative = Path(value).relative_to(old_root)
            except ValueError:
                return value
            return (Path(".")/relative).as_posix() or "."
        return value

    try:
        for result in job["cases"]:
            source = Path(result["directory"])
            relative = source.resolve().relative_to(old_root)
            case_dir = stage/relative
            case_dir.mkdir(parents=True, exist_ok=True)
            # Perturbation solves are internal calculations, not saved cases.
            if source.is_dir():
                for file in source.iterdir():
                    if file.is_file() and file.suffix.lower() in {".fem", ".ans", ".csv"}:
                        shutil.copy2(file, case_dir/file.name)
            save_config(Config.from_dict(result["config"]), case_dir/"config.json")
            saved_case=relocate(result)
            saved_case["path_base"]="/".join([".."]*len(relative.parts)) or "."
            save_json(case_dir/"result.json", saved_case)
            if result.get("field_data"):
                field_figure(result).savefig(case_dir/"feld.png", dpi=160)
        stored = relocate(stored)
        stored["directory"] = "."
        stored["path_base"] = "."
        stored["path_note"] = "Alle Ergebnis-Dateipfade sind relativ zum Ordner der job.json."
        save_json(stage/"job.json", stored)
        export_job(stored, stage/"ergebnisse.csv")
        if stored.get("accuracy"):
            save_json(stage/"accuracy.json", stored["accuracy"])
        geometry_figure(Config.from_dict(job["config"])).savefig(stage/"geometrie.png", dpi=160)
        if job["kind"] in {"current", "gap"}:
            sweep_figure(job).savefig(stage/"diagramm.png", dpi=160)
        if job["kind"] == "force_map":
            from force_map import export, save_figures
            export(stored, stage)
            save_figures(stored, stage)
        for side in ("upper", "lower"):
            for view, (key, _, _) in electrical.VIEWS.items():
                if any(result_electrical(row,side) and result_electrical(row,side).get(key) is not None for row in job["cases"]):
                    name={"voltage_dc_v":"spannung", "inductance_h":"induktivitaet", "time_constant_s":"zeitkonstante"}[key]
                    german="oben" if side=="upper" else "unten"
                    electrical.figure(job,side,view).savefig(stage/(f"elektrik_{german}_{name}.png"),dpi=160)
        if stored.get("impedance_check"):
            from impedance import export as export_impedance
            export_impedance(stored["impedance_check"],stage)
        stage.rename(target)
        return target
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def summary_text(row):
    x = row.get("x", "?")
    if "gap_mm" in row:
        return f"I={row['current_a']:g} A, s={row['gap_mm']:g} mm: Fz={row['force_n']:+.6g} N"
    if "roots" in row:
        roots = "; ".join(f"{r['current_a']:+.6g} A (Residual {r['residual_n']:+.4g} N)"+
                          (" [DC-Spannungsgrenze überschritten]" if r.get("within_voltage_limit") is False else "") for r in row["roots"])
        return f"g={x} mm: {row['status']}"+("; Lösungen: "+roots if roots else "")+("; ungültige Scanpunkte: "+str(len(row["scan_errors"])) if row.get("scan_errors") else "")
    return f"I oben={x} A: {row['status']}"+(f"; Fz={row['force_n']:+.6g} N" if "force_n" in row else "; "+"; ".join(row.get("errors", [])))


def result_electrical(result, side):
    """Saved results take precedence; older force-only files lack electrical data."""
    data = result.get("electrical", {}).get(side)
    if data is not None and "voltage_dc_v" in data:
        return data
    magnet = getattr(Config.from_dict(result["config"]), side)
    return electrical.stationary(magnet, wire_data(magnet))


ELECTRICAL_COLUMNS = [("Temperatur","C","temperature_c"),("R_Betrieb","Ohm","resistance_ohm"),
    ("R20_Spule","Ohm","resistance20_ohm"),
    ("R_Spule_Betrieb","Ohm","coil_resistance_ohm"),("R_Leitungen","Ohm","lead_resistance_ohm"),
    ("U_DC","V","voltage_dc_v"),("U_DC_Vorzeichen","V","voltage_dc_signed_v"),
    ("U_verfuegbar","V","voltage_limit_v"),("U_Reserve","V","voltage_headroom_v"),
    ("U_Grenze_eingehalten","Bool","within_voltage_limit"),("P_Spule_Betrieb","W","power_coil_w"),
    ("Flussverkettung","Wb","flux_linkage_wb"),("L_differenziell","H","inductance_h"),
    ("Gegeninduktivitaet","H","mutual_inductance_h"),
    ("Tau","s","time_constant_s"),("Tau_nur_Spule","s","coil_time_constant_s"),
    ("Strom_Testschritt","A","perturbation_a"),("L_Status","Text","inductance_status"),
    ("R_Quelle","Text","resistance_source"),("Stromanstiegsreserve","A_s","max_current_rise_a_s")]


def export_job(job, path):
    columns = ["Typ", "Status", "Phase", "Sweepwert", "I_oben_A", "I_unten_A", "g_oben_mm", "g_unten_mm",
               "Polabstand_mm", "z_mm", "Masse_g", "Gewicht_N", "Magnetkraft_z_N", "Nettokraft_N",
               "Netz_lokal_mm", "Netz_Luft_mm", "Bogen_grad", "Luftbereich_Faktor", "Details",
               "Spule_oben_aktiv", "Spule_unten_aktiv", "Objekt_aktiv", "Kernform_oben", "Kernform_unten"]
    for side in ["oben","unten"]:
        columns.extend(key+"_"+side+"_"+unit for key,unit,_ in ELECTRICAL_COLUMNS)
        columns.extend(key+"_"+side+"_"+unit for key,unit in [
            ("Kupferdraht","mm"),("Draht_mit_Lack","mm"),("Drahtlaenge","m"),
            ("R20","Ohm"),("Verlust20","W"),("Spannung20_DC","V"),
            ("Stromdichte","A_mm2"),("Kupferfuellgrad","Anteil"),("Lackfuellgrad","Anteil")])
    rows = []
    for r in job["cases"]:
        c = Config.from_dict(r["config"]);p = coordinates(c);n=c.numerics
        rows.append(dict(Typ="FEMM", Status="berechnet", Phase=r.get("phase"), Sweepwert=r.get("sweep_x"),
                         I_oben_A=r["upper_current_a"], I_unten_A=r["lower_current_a"], g_oben_mm=p["upper_gap"],
                         g_unten_mm=p["lower_gap"], Polabstand_mm=p["h"], z_mm=p["center"], Masse_g=r["mass_kg"]*1000,
                         Gewicht_N=r["weight_n"], Magnetkraft_z_N=r["magnetic_force_z_n"], Nettokraft_N=r["net_force_n"],
                         Netz_lokal_mm=n.mesh_mm, Netz_Luft_mm=n.air_mesh_mm,
                         Bogen_grad=n.arc_deg, Luftbereich_Faktor=n.domain_factor,
                         Spule_oben_aktiv=c.upper.enabled, Spule_unten_aktiv=c.lower.enabled, Objekt_aktiv=c.object.enabled,
                         Kernform_oben=c.upper.core_kind, Kernform_unten=c.lower.core_kind))
        for german,m in [("oben",c.upper),("unten",c.lower)]:
            e=result_electrical(r,"upper" if german=="oben" else "lower")
            if e is not None:
                for key,unit,source in ELECTRICAL_COLUMNS:
                    rows[-1][key+"_"+german+"_"+unit]=e.get(source)
            w=wire_data(m)
            rows[-1].update({"Kupferdraht_"+german+"_mm":m.wire_d_mm,
                             "Draht_mit_Lack_"+german+"_mm":m.wire_od_mm})
            if w is not None:
                for key,unit,source in [("Drahtlaenge","m","length_m"),("R20","Ohm","resistance20_ohm"),
                        ("Verlust20","W","power20_w"),("Spannung20_DC","V","voltage20_v"),
                        ("Stromdichte","A_mm2","current_density_a_mm2"),
                        ("Kupferfuellgrad","Anteil","copper_fill"),("Lackfuellgrad","Anteil","insulated_fill")]:
                    rows[-1][key+"_"+german+"_"+unit]=w[source]
    for r in job.get("summary", []):
        roots = r.get("roots", [])
        for root in roots or [None]:
            rows.append(dict(Typ="Auswertung", Status=r["status"], Sweepwert=r.get("x"),
                             I_oben_A=root["current_a"] if root else None, I_unten_A=r.get("lower_current_a"),
                             Magnetkraft_z_N=root["force_n"] if root else r.get("force_n"),
                             Nettokraft_N=root["residual_n"] if root else None,
                             Details=json.dumps(r, ensure_ascii=False, allow_nan=False)))
            if root:
                for side,german in [("upper","oben"),("lower","unten")]:
                    e=root.get("electrical",{}).get(side)
                    if e:
                        for key,unit,source in ELECTRICAL_COLUMNS:
                            rows[-1][key+"_"+german+"_"+unit]=e.get(source)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+".tmp")
    with tmp.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)

def sweep_figure(job, figure=None):
    fig = figure or Figure(figsize=(8.2, 5.5), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)
    c = Config.from_dict(job["config"])
    rows, options = job.get("summary", []), job["options"]
    lower = options.get("fixed_lower", 0)
    if job["kind"] == "current":
        xs = [r["x"] for r in rows]
        ys = [r.get("force_n", float("nan")) for r in rows]
        ax.plot(xs, ys, "o-", color="#176b98",linewidth=2,markersize=5,label="Magnetkraft Fz (FEMM)")
        ax.axhline(mass(c)*9.81, color="#a45523", linestyle="--", label="Gewichtskraft m·9,81")
        ax.axhline(0, color="#777777", linewidth=0.6)
        ax.set_xlabel("Oberer Strom [A]")
        ax.set_ylabel("Vertikalkraft [N] · + nach oben")
        ax.set_title("Kraft über Strom\n"+f"Unterer Strom fest: {lower:+.5g} A")
    else:
        ranks = max((len(r.get("roots", [])) for r in rows), default=0)
        for rank in range(ranks):
            good = [(r["x"], r["roots"][rank]["current_a"]) for r in rows if len(r.get("roots", [])) > rank]
            ax.scatter([x for x, y in good], [y for x, y in good], label=f"Lösung {rank+1} nach Strom sortiert (FEMM)")
        limited=[(row["x"],root["current_a"]) for row in rows for root in row.get("roots",[]) if root.get("within_voltage_limit") is False]
        if limited:
            ax.scatter([x for x,y in limited],[y for x,y in limited],marker="x",color="#a45523",s=65,
                       label="DC-Spannungsgrenze überschritten",zorder=4)
        bad = [r["x"] for r in rows if not r.get("roots")]
        if bad:
            ax.scatter(bad, [0.025]*len(bad), marker="x", color="#b3272e", transform=ax.get_xaxis_transform(), label="Nicht erreicht / ungültig", clip_on=False)
        # Marker am unteren Rand haben keine Stromkoordinate. Ihre Abstände
        # müssen trotzdem in den sichtbaren x-Bereich aufgenommen werden.
        if rows:
            lo,hi=min(r["x"] for r in rows),max(r["x"] for r in rows)
            pad=.04*(hi-lo) if hi>lo else max(abs(lo)*.04,.5)
            ax.set_xlim(lo-pad,hi+pad)
        ax.set_xlabel("Gleicher Luftspalt oben und unten [mm]")
        ax.set_ylabel("Benötigter oberer Strom [A]")
        ax.set_title("Haltestrom über Luftspalt\n"+f"Unterer Strom fest: {lower:+.5g} A")
        fig.text(.5,.025,"FEMM-Gleichgewichte · endlicher Stromscan\nSchmale Lösungsbereiche können fehlen.",ha="center",fontsize=8,color="#596773")
    ax.grid(alpha=0.2)
    handles, _ = ax.get_legend_handles_labels()
    if handles:
        ax.legend(fontsize=9, loc="best")
    fig.subplots_adjust(left=.13, right=.97, top=.85, bottom=.17)
    return fig
