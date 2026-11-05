"""Zwei mittlere Temperaturen bei konstantem Strom; ohne FEMM oder Tkinter.

Ccu*Tcu' = I²*R20*(1+alpha*(Tcu-20)) - Gcu*(Tcu-Ta) - Gk*(Tcu-Tfe)
Cfe*Tfe' = Gk*(Tcu-Tfe) - Gfe*(Tfe-Ta)

Konstante Wärmekapazitäten und Wärmeleitwerte. Die symmetrisch transformierte
2x2-Matrix wird analytisch gelöst, auch im neutralen und instabilen Grenzfall.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import csv
import math
import numpy as np
from core_types import shape_errors, core_volume_mm3, pot_exterior_area_mm2

RHO20 = 0.017241  # Ohm mm²/m, wie in der elektrischen Schätzung des Tools
MODEL_MAX_C = 300.0
NOTICE = "Schätzung mittlerer Temperaturen von Wicklung und Kern; keine maximale lokale Temperatur."
COOLING_PRESETS = {"Ruhende Luft (Annahme)": 8.0,
                   "Luftstrom (Annahme)": 30.0}


@dataclass(frozen=True)
class Coil:
    core_d: float
    core_l: float
    coil_id: float
    coil_od: float
    coil_h: float
    coil_offset: float
    turns: float
    wire_d_mm: float | None
    current: float
    material: str = "Eisen/Stahl"
    wire_od_mm: float | None = None
    enabled: bool = True
    core_kind: str = "rod"
    pot_inner_d: float = 86.0
    pot_outer_d: float = 96.0
    pot_back_h: float = 10.0
    resistance20_ohm: float | None = None

    @classmethod
    def from_magnet(cls, magnet):
        return cls(**{key: getattr(magnet, key) for key in cls.__dataclass_fields__})


@dataclass(frozen=True)
class Settings:
    ambient_c: float = 20.0
    duration_min: float = 60.0
    limit_c: float = 100.0
    h_copper: float = 8.0
    h_core: float = 8.0
    coupling_w_k: float = 0.3
    copper_exposed_percent: float = 100.0
    core_exposed_percent: float = 100.0
    initial_c: float | None = None
    copper_density: float = 8930.0
    copper_cp: float = 385.0
    core_density: float = 7870.0
    core_cp: float = 450.0
    copper_alpha: float = 0.00393


def validate_settings(s):
    bounds = {
        "ambient_c": (-50, 150, "Umgebungstemperatur [°C]"),
        "duration_min": (1e-6, 10080, "Betriebsdauer [min]"),
        "limit_c": (-50, 200, "Temperaturgrenzwert [°C]"),
        "h_copper": (0, 10000, "Wärmeabgabe der Wicklung [W/(m² K)]"),
        "h_core": (0, 10000, "Wärmeabgabe des Kerns [W/(m² K)]"),
        "coupling_w_k": (0, 10000, "Wärmeübergang Wicklung–Kern [W/K]"),
        "copper_exposed_percent": (0, 100, "Freie Wicklungsfläche [%]"),
        "core_exposed_percent": (0, 100, "Freie Kernfläche [%]"),
        "copper_density": (1, 30000, "Kupferdichte [kg/m³]"),
        "core_density": (1, 30000, "Kerndichte [kg/m³]"),
        "copper_cp": (1, 10000, "Spezifische Wärmekapazität Kupfer [J/(kg K)]"),
        "core_cp": (1, 10000, "Spezifische Wärmekapazität Kern [J/(kg K)]"),
        "copper_alpha": (0, .02, "Kupfer-Temperaturkoeffizient [1/K]"),
    }
    for key, (lower, upper, label) in bounds.items():
        value = getattr(s, key)
        if type(value) not in (int, float) or not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f"{label}: endliche Zahl zwischen {lower:g} und {upper:g} eingeben.")
    if s.initial_c is not None and (type(s.initial_c) not in (int, float)
            or not math.isfinite(s.initial_c) or not -50 <= s.initial_c <= 200):
        raise ValueError("Starttemperatur: leer lassen oder Zahl zwischen −50 und 200 °C eingeben.")
    initial = s.ambient_c if s.initial_c is None else s.initial_c
    if min(1+s.copper_alpha*(s.ambient_c-20), 1+s.copper_alpha*(initial-20)) <= 0:
        raise ValueError("Temperaturkoeffizient ergibt einen nicht positiven Kupferwiderstand.")


def coil_data(c, s):
    """Massen, freie Oberflächen und DC-Widerstand aus den vorhandenen Abmessungen."""
    if not c.enabled:raise ValueError("Gewählte Spule ist deaktiviert. Vor der Temperaturrechnung aktivieren.")
    for key in ["core_d", "core_l", "coil_id", "coil_od", "coil_h"]:
        value = getattr(c, key)
        if type(value) not in (int, float) or not math.isfinite(value) or not .001 <= value <= 10000:
            raise ValueError(f"Spulenabmessung {key}: Zahl zwischen 0,001 und 10000 mm eingeben.")
    for key in ["coil_offset", "turns", "current"]:
        value = getattr(c, key)
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"Spulenwert {key}: endliche Zahl eingeben.")
    if not 1 <= c.turns <= 1e7 or int(c.turns) != c.turns:
        raise ValueError("Windungszahl muss ganzzahlig und zwischen 1 und 10000000 sein.")
    if abs(c.current) > 10000:
        raise ValueError("Spulenstrom liegt ausserhalb des berechenbaren Bereichs (±10000 A).")
    if not c.coil_od > c.coil_id >= c.core_d:
        raise ValueError("Aussen-Ø muss grösser als Innen-Ø sein; der Kern muss in die Wicklung passen.")
    errors=shape_errors(c)
    if errors:raise ValueError("\n".join(errors))
    if c.wire_d_mm is None:
        raise ValueError("Kupfer-Drahtdurchmesser fehlt. Im Reiter Oben bzw. Unten eintragen.")
    if type(c.wire_d_mm) not in (int, float) or not math.isfinite(c.wire_d_mm) or c.wire_d_mm <= 0:
        raise ValueError("Kupfer-Drahtdurchmesser muss positiv und endlich sein.")
    diameter = c.wire_d_mm if c.wire_od_mm is None else c.wire_od_mm
    if type(diameter) not in (int, float) or not math.isfinite(diameter) or diameter < c.wire_d_mm:
        raise ValueError("Draht-Ø mit Lack muss endlich und mindestens so gross wie der Kupfer-Ø sein.")
    width = (c.coil_od-c.coil_id)/2
    if diameter > min(width, c.coil_h):
        raise ValueError("Ein einzelner Draht passt nicht in den Wickelraum.")
    fill = c.turns*math.pi*diameter**2/4/(width*c.coil_h)
    if fill > math.pi/(2*math.sqrt(3))+1e-10:
        raise ValueError("Draht und Windungszahl passen nicht in den Wickelraum (über 90,7 % Füllgrad).")
    area_mm2 = math.pi*c.wire_d_mm**2/4
    length_m = c.turns*math.pi*(c.coil_id+c.coil_od)/2000
    copper_mass = length_m*area_mm2*1e-6*s.copper_density
    core_mass = core_volume_mm3(c)*1e-9*s.core_density
    copper_area = (math.pi*c.coil_od*c.coil_h
                   + math.pi*(c.coil_od**2-c.coil_id**2)/2)*1e-6
    overlap = max(0, min(c.core_l, c.coil_offset+c.coil_h)-max(0, c.coil_offset))
    core_area = (math.pi*c.core_d*(c.core_l-overlap)+math.pi*c.core_d**2/2)*1e-6
    if c.core_kind=="pot":
        # Die eingeschlossene Wicklung kühlt direkt nur über die offene Front;
        # Wärme zum Kern wird separat durch coupling_w_k beschrieben.
        copper_area=math.pi*(c.coil_od**2-c.coil_id**2)/4*1e-6
        core_area=pot_exterior_area_mm2(c)*1e-6
    copper_area *= s.copper_exposed_percent/100
    core_area *= s.core_exposed_percent/100
    if c.resistance20_ohm is not None and (type(c.resistance20_ohm) not in (int,float) or
            not math.isfinite(c.resistance20_ohm) or c.resistance20_ohm <= 0):
        raise ValueError("Gemessenes R20 muss positiv und endlich sein oder leer bleiben.")
    data = dict(length_m=length_m, area_mm2=area_mm2,
                resistance20_ohm=c.resistance20_ohm if c.resistance20_ohm is not None else RHO20*length_m/area_mm2,
                copper_mass_kg=copper_mass, core_mass_kg=core_mass,
                copper_capacity_j_k=copper_mass*s.copper_cp,
                core_capacity_j_k=core_mass*s.core_cp,
                copper_area_m2=copper_area, core_area_m2=core_area,
                g_copper_w_k=s.h_copper*copper_area,
                g_core_w_k=s.h_core*core_area, coupling_w_k=s.coupling_w_k,
                core_overlap_mm=overlap)
    if not all(math.isfinite(v) for v in data.values()):
        raise ValueError("Spulenwerte liegen ausserhalb des berechenbaren Zahlenbereichs.")
    return data


class _Solution:
    def __init__(self, c, s, d):
        self.ambient = s.ambient_c
        self.capacity = np.array([d["copper_capacity_j_k"], d["core_capacity_j_k"]])
        self.root_c = np.sqrt(self.capacity)
        p20 = c.current**2*d["resistance20_ohm"]
        gcu, gfe, gk = d["g_copper_w_k"], d["g_core_w_k"], s.coupling_w_k
        self.heat_matrix = np.array([[p20*s.copper_alpha-gcu-gk, gk], [gk, -gk-gfe]])
        self.source = np.array([p20*(1+s.copper_alpha*(s.ambient_c-20)), 0.0])
        symmetric = self.heat_matrix/np.outer(self.root_c, self.root_c)
        self.rates, self.vectors = np.linalg.eigh(symmetric)
        initial = s.ambient_c if s.initial_c is None else s.initial_c
        self.initial_modes = self.vectors.T@(self.root_c*(initial-s.ambient_c))
        self.forcing_modes = self.vectors.T@(self.source/self.root_c)
        self.derivative_coefficients = (self.vectors/self.root_c[:, None]
                * (self.rates*self.initial_modes+self.forcing_modes)[None, :])
        tolerance = 32*np.finfo(float).eps*max(abs(self.rates))
        self.stable = bool(self.rates[-1] < -tolerance)
        self.steady = None
        if self.stable:
            self.steady = np.linalg.solve(-self.heat_matrix, self.source)+s.ambient_c

    def at(self, seconds):
        times = np.atleast_1d(np.asarray(seconds, dtype=float))
        exponent = times[:, None]*self.rates
        # Solche Werte dienen nur zur Suche nach dem Modellende; die ausgegebene
        # Kurve endet vorher bei 300 °C. Verhindert Overflow bei instabilen Fällen.
        bounded = np.clip(exponent, -745, 600)
        integral = np.empty_like(exponent)
        for j, rate in enumerate(self.rates):
            if rate == 0:
                integral[:, j] = times
            else:
                integral[:, j] = np.expm1(bounded[:, j])/rate
        modes = np.exp(bounded)*self.initial_modes+integral*self.forcing_modes
        values = (modes@self.vectors.T)/self.root_c+self.ambient
        return values[0] if np.ndim(seconds) == 0 else values

    def first_crossing(self, node, limit, duration):
        """Erster Grenzübertritt, unabhängig von der Anzahl der Plot-Stützstellen.

        Die Ableitung ist die Summe zweier Exponentialfunktionen. Ihr möglicher
        Nulldurchgang trennt monotone Abschnitte, auch bei warmem Start.
        """
        if self.at(0)[node] >= limit:
            return 0.0
        points = [0.0, duration]
        a, b = self.derivative_coefficients[node]
        difference = self.rates[1]-self.rates[0]
        if a != 0 and b != 0 and (a > 0) != (b > 0) and difference != 0:
            extreme = (math.log(abs(a))-math.log(abs(b)))/difference
            if 0 < extreme < duration:
                points.insert(1, extreme)
        for lower, upper in zip(points[:-1], points[1:]):
            if self.at(upper)[node] >= limit:
                for _ in range(80):
                    middle = (lower+upper)/2
                    if self.at(middle)[node] >= limit:
                        upper = middle
                    else:
                        lower = middle
                return upper
        return None


@dataclass
class Result:
    coil: Coil
    settings: Settings
    data: dict
    times_s: np.ndarray
    copper_c: np.ndarray
    core_c: np.ndarray
    resistance_ohm: np.ndarray
    power_w: np.ndarray
    stable: bool
    steady_c: tuple | None
    limit_times_s: tuple
    model_truncated: bool


def calculate(coil, settings=Settings(), samples=601):
    validate_settings(settings)
    if type(samples) is not int or not 2 <= samples <= 20000:
        raise ValueError("Anzahl der Stützstellen muss zwischen 2 und 20000 liegen.")
    d = coil_data(coil, settings)
    solution = _Solution(coil, settings, d)
    duration = settings.duration_min*60
    model_ends = [solution.first_crossing(i, MODEL_MAX_C, duration) for i in (0, 1)]
    stop = min([duration]+[t for t in model_ends if t is not None])
    hits = tuple(solution.first_crossing(i, settings.limit_c, stop) for i in (0, 1))
    times = np.unique(np.r_[np.linspace(0, stop, samples), [t for t in hits if t is not None]])
    temperatures = solution.at(times)
    resistance = d["resistance20_ohm"]*(1+settings.copper_alpha*(temperatures[:, 0]-20))
    power = coil.current**2*resistance
    if (not np.isfinite(temperatures).all() or not np.isfinite(power).all()
            or not np.isfinite(resistance).all() or np.any(resistance <= 0)):
        raise ValueError("Thermisches Ergebnis liegt ausserhalb des berechenbaren Bereichs.")
    steady = None if solution.steady is None else tuple(map(float, solution.steady))
    return Result(coil, settings, d, times, temperatures[:, 0], temperatures[:, 1],
                  resistance, power, solution.stable, steady, hits, stop < duration)


def draw_figure(result, fig):
    fig.clear()
    # Achsenbeschriftungen behalten beim Verkleinern ihren Platz.
    fig.set_layout_engine("constrained", h_pad=.05, w_pad=.05)
    ax = fig.add_subplot(111)
    ax.plot(result.times_s/60, result.copper_c, color="#ad5727", lw=2, label="Kupferwicklung (Mittel)")
    ax.plot(result.times_s/60, result.core_c, color="#276889", lw=2, label="Kern (Mittel)")
    ax.axhline(result.settings.limit_c, color="#b3272e", ls="--", label="Temperaturgrenzwert")
    ax.axhline(result.settings.ambient_c, color="#7b8791", ls=":", label="Umgebung")
    for hit, values, colour in zip(result.limit_times_s, [result.copper_c, result.core_c], ["#ad5727", "#276889"]):
        if hit is not None:
            ax.plot(hit/60, np.interp(hit, result.times_s, values), "o", color=colour)
    ax.set(xlabel="Betriebsdauer [min]", ylabel="Temperatur\n[°C]")
    ax.set_xlim(0,max(result.times_s[-1]/60,.001))
    ax.grid(alpha=.25)
    ax.legend(fontsize=8, loc="best")
    ax.ticklabel_format(axis="y", useOffset=False)


def export_csv(result, path, side="upper"):
    path = Path(path)
    columns = ["Zeit_s", "Wicklung_Mittel_C", "Kern_Mittel_C", "Widerstand_Ohm", "Kupferverluste_W"]
    metadata = {"Modell": "Zwei mittlere Temperaturen, konstanter Strom", "Hinweis": NOTICE,
                "Spule": side, "Stabiles_Gleichgewicht": result.stable,
                "Dauertemperaturen_C": result.steady_c, "Grenzzeiten_s": result.limit_times_s,
                "Modellende_300C": result.model_truncated}
    metadata.update({"Spule_"+k: v for k, v in asdict(result.coil).items()})
    metadata.update({"Annahme_"+k: v for k, v in asdict(result.settings).items()})
    metadata.update(result.data)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        for key, value in metadata.items():
            writer.writerow(["# "+key, value])
        writer.writerow(columns)
        writer.writerows(zip(result.times_s, result.copper_c, result.core_c, result.resistance_ohm, result.power_w))
