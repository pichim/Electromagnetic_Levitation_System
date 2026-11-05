"""Frequency comparison for an ideal series RL winding, and PWM mean current.

Sinusoidal mode: I and U are RMS; XL=2*pi*f*L, |Z|=hypot(R,XL).
PWM mode: grid currents are means; frequency determines ripple, not an
extra DC resistance. This module does not solve frequency-dependent FEMM.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from copy import deepcopy
from bisect import bisect_left
import csv
import json
import math
from pathlib import Path
from electrical import COPPER_ALPHA


@dataclass
class Settings:
    current_start_a: float = 0.0
    current_end_a: float = 10.0
    current_step_a: float = 1.0
    frequency_hz: float = 20000.0
    resistance20_ohm: float = 4.0
    temperature_c: float = 20.0
    lead_resistance_ohm: float = 0.0
    inductance_mh: float = 100.0
    voltage_limit_v: float = 48.0
    current_limit_a: float = 10.0
    delta_current_a: float = 1.0
    transition_ms: float = 10.0
    source: str = "manual"
    side: str = "upper"
    pwm_mode: str = "slow"


ASSUMPTIONS = (
    "Sinus: eingegebener Strom als Effektivwert; Ueff = Ieff·sqrt(R²+(2πfL)²). "
    "Die Spitzenspannung sqrt(2)·Ueff wird mit dem verfügbaren Ausgangsbetrag verglichen. "
    "PWM: dieselben Zahlen als Mittelströme; Haltespannung R·Imittel, ideale PWM-Stufen "
    "0/+U oder −U/+U, R und L lokal konstant, f bestimmt die Welligkeit. "
    "Keine Bewegungsinduktion, Kopplungsströme, Totzeiten oder Kernverluste. "
    "Magnetostatisches FEMM-L ist keine gemessene Hochfrequenzinduktivität. "
    "Sinuswerte sind ein ideales RL-Vergleichsmodell, keine PWM-Versorgungsanforderung."
)


def validate(s):
    for key,value in asdict(s).items():
        if key in {"source","side","pwm_mode"}:continue
        if type(value) not in (int,float) or not math.isfinite(value):
            raise ValueError("R / XL: alle Zahlen müssen endlich sein.")
    if s.source not in {"manual","femm"} or s.side not in {"upper","lower"} or s.pwm_mode not in {"slow","bipolar"}:
        raise ValueError("R / XL: ungültige Quelle, Spule oder PWM-Art.")
    if not 0 <= s.current_start_a <= s.current_end_a <= 1000 or s.current_step_a <= 0:
        raise ValueError("Strombereich: 0 bis 1000 A, Ende mindestens Start, Schritt positiv.")
    if (s.current_end_a-s.current_start_a)/s.current_step_a > 1000:
        raise ValueError("Maximal 1001 Strompunkte; Schrittweite vergrössern.")
    if not 1 <= s.frequency_hz <= 1e7:
        raise ValueError("Frequenz: 1 Hz bis 10 MHz.")
    if not 0 < s.resistance20_ohm <= 1e6 or not 0 <= s.lead_resistance_ohm <= 1e6:
        raise ValueError("R20 muss positiv, Leitungswiderstand mindestens null sein.")
    if not -50 <= s.temperature_c <= 250 or not 0 <= s.inductance_mh <= 1e6:
        raise ValueError("Temperatur: −50 bis 250 °C; L: 0 bis 1 000 000 mH.")
    if not 0 < s.voltage_limit_v <= 1e6 or not 0 < s.current_limit_a <= 1000:
        raise ValueError("Spannung und Stromgrenze müssen positiv sein.")
    if not 0 <= s.delta_current_a <= 1000 or not 1e-6 <= s.transition_ms <= 1e9:
        raise ValueError("Stromänderung darf nicht negativ sein; Änderungszeit muss positiv sein.")
    return s


def parse_settings(data):
    if not isinstance(data,dict) or set(data) != set(asdict(Settings())):
        raise ValueError("R / XL: fehlende oder unbekannte Einstellungen.")
    validate(Settings(**data))
    return deepcopy(data)


def currents(s):
    validate(s)
    count=math.floor((s.current_end_a-s.current_start_a)/s.current_step_a+1e-10)
    return [min(s.current_end_a,s.current_start_a+i*s.current_step_a) for i in range(count+1)]


def _moments(i0, equilibrium, duration, tau):
    h=duration/tau;k=equilibrium-i0
    if h<.001:
        f=h*h*(.5-h/6+h*h/24-h**3/120+h**4/720)
        g=h**3*(1/3-h/4+7*h*h/60-h**3/24+31*h**4/2520)
    else:
        f=h+math.expm1(-h);g=h+2*math.expm1(-h)-.5*math.expm1(-2*h)
    return i0*duration+k*tau*f,i0*i0*duration+2*i0*k*tau*f+k*k*tau*g


def pwm_stats(r,l,current,voltage,frequency,mode):
    """Exact periodic linear RL solution for ideal synchronous PWM states."""
    if r is None or l is None or l <= 0:return None
    low=0.0 if mode=="slow" else -voltage
    duty=(r*current-low)/(voltage-low)
    if not -1e-12 <= duty <= 1+1e-12:return None
    duty=max(0,min(1,duty))
    period=1/frequency;tau=l/r;ton=duty*period;toff=period-ton
    b=math.exp(-toff/tau)
    minimum=((low/r)*(-math.expm1(-toff/tau))+b*(voltage/r)*(-math.expm1(-ton/tau)))/(-math.expm1(-period/tau))
    maximum=minimum+(voltage/r-minimum)*(-math.expm1(-ton/tau))
    mean_on,square_on=_moments(minimum,voltage/r,ton,tau)
    mean_off,square_off=_moments(maximum,low/r,toff,tau)
    return dict(duty=duty,ripple_pp_a=maximum-minimum,current_min_a=minimum,current_max_a=maximum,
                rms_current_a=math.sqrt(max(0,(square_on+square_off)/period)),
                average_current_a=(mean_on+mean_off)/period,
                peak_abs_a=max(abs(minimum),abs(maximum)))


def samples(job,anchor,side):
    """Only cases of the same assembly, gap, other current and numerical mesh."""
    from model import result_electrical
    if not job or not anchor:return []
    def signature(row):
        cfg=deepcopy(row["config"]);cfg[side].pop("current",None)
        return json.dumps(cfg,sort_keys=True,allow_nan=False)
    wanted=signature(anchor);points={}
    for row in job.get("cases",[]):
        if signature(row)!=wanted:continue
        d=result_electrical(row,side)
        if not d:continue
        points[d["current_a"]]=dict(current_a=d["current_a"],resistance_ohm=d["resistance_ohm"],
            coil_resistance_ohm=d["coil_resistance_ohm"],inductance_h=d["inductance_h"])
    return [points[i] for i in sorted(points)]


def interpolate(points,current):
    axis=[p["current_a"] for p in points]
    k=bisect_left(axis,current)
    for index in (k,k-1):
        if 0<=index<len(points) and math.isclose(axis[index],current,rel_tol=1e-10,abs_tol=1e-10):
            return deepcopy(points[index]),"FEMM-Punkt"
    if k==0 or k==len(points):return None,"Ausserhalb der berechneten FEMM-Ströme"
    a,b=points[k-1],points[k];fraction=(current-a["current_a"])/(b["current_a"]-a["current_a"])
    out={"current_a":current}
    for key in ("resistance_ohm","coil_resistance_ohm","inductance_h"):
        out[key]=None if a[key] is None or b[key] is None else a[key]+fraction*(b[key]-a[key])
    return out,"Linear zwischen FEMM-Punkten"


def calculate(s,job=None,anchor=None):
    validate(s)
    points=samples(job,anchor,s.side) if s.source=="femm" else []
    rows=[];rate=s.delta_current_a/(s.transition_ms/1000)
    manual_coil=s.resistance20_ohm*(1+COPPER_ALPHA*(s.temperature_c-20))
    for current in currents(s):
        if s.source=="manual":
            data=dict(resistance_ohm=manual_coil+s.lead_resistance_ohm,coil_resistance_ohm=manual_coil,inductance_h=s.inductance_mh/1000)
            provenance="Manuelle R-/L-Annahme"
        else:
            data,provenance=interpolate(points,current)
            if data is None:data={key:None for key in ("resistance_ohm","coil_resistance_ohm","inductance_h")}
        r,rc,l=(data[key] for key in ("resistance_ohm","coil_resistance_ohm","inductance_h"))
        xl=None if l is None else 2*math.pi*s.frequency_hz*l
        z=None if r is None or xl is None else math.hypot(r,xl)
        ur=None if r is None else current*r
        ul=None if xl is None else current*xl
        uac=None if z is None else current*z
        peak=None if uac is None else math.sqrt(2)*uac
        rise=None if ur is None or l is None else ur+l*rate
        fall=None if ur is None or l is None else ur-l*rate
        lower=0 if s.pwm_mode=="slow" else -s.voltage_limit_v
        def check(v):return None if v is None else lower-1e-10<=v<=s.voltage_limit_v+1e-10
        cycle=pwm_stats(r,l,current,s.voltage_limit_v,s.frequency_hz,s.pwm_mode)
        row=dict(current_a=current,resistance_ohm=r,coil_resistance_ohm=rc,inductance_h=l,
            time_constant_s=None if r is None or l is None else l/r,
            reactance_ohm=xl,impedance_ohm=z,phase_deg=None if r is None or xl is None else math.degrees(math.atan2(xl,r)),
            voltage_resistive_v=ur,voltage_inductive_sine_rms_v=ul,voltage_sine_rms_v=uac,voltage_sine_peak_v=peak,
            sine_voltage_ok=None if peak is None else peak<=s.voltage_limit_v+1e-10,
            sine_current_ok=math.sqrt(2)*current<=s.current_limit_a+1e-10,
            voltage_pwm_hold_v=ur,voltage_rise_v=rise,voltage_fall_v=fall,
            hold_ok=check(ur),rise_ok=check(rise),fall_ok=False if current==0 and rate>0 and s.pwm_mode=="slow" else check(fall),
            pwm_duty=None,pwm_ripple_pp_a=None,pwm_current_peak_a=None,pwm_current_rms_a=None,pwm_power_coil_w=None,
            pwm_current_ok=None,provenance=provenance)
        if cycle:
            row.update(pwm_duty=cycle["duty"],pwm_ripple_pp_a=cycle["ripple_pp_a"],pwm_current_peak_a=cycle["peak_abs_a"],
                pwm_current_rms_a=cycle["rms_current_a"],pwm_power_coil_w=None if rc is None else cycle["rms_current_a"]**2*rc,
                pwm_current_ok=cycle["peak_abs_a"]<=s.current_limit_a+1e-10)
        rows.append(row)
    reference=None if s.source!="femm" or not anchor else dict(config=deepcopy(anchor["config"]),
                     upper_current_a=anchor["upper_current_a"],lower_current_a=anchor["lower_current_a"])
    return dict(format="femm-impedance-comparison",version=1,settings=asdict(s),assumptions=ASSUMPTIONS,
                femm_reference=reference,rows=rows)


def figure(assessment,view="Sinus / XL",fig=None):
    from matplotlib.figure import Figure
    fig=fig or Figure(figsize=(8,5),dpi=100);fig.clear();ax=fig.add_subplot(111)
    rows=(assessment or {}).get("rows",[])
    if view=="Blindwiderstand":
        keys=(("resistance_ohm","R"),("reactance_ohm","XL = 2πfL"),("impedance_ohm","|Z|"));ylabel="Widerstand / Reaktanz [Ω]"
    elif view=="PWM":
        keys=(("voltage_pwm_hold_v","Halten"),("voltage_rise_v","Erhöhen"),("voltage_fall_v","Senken"));ylabel="Mittlere Spannung [V]"
    else:
        keys=(("voltage_resistive_v","UR,eff"),("voltage_inductive_sine_rms_v","UL,eff"),("voltage_sine_rms_v","Ugesamt,eff"));ylabel="Sinusspannung, Effektivwert [V]"
    for key,label in keys:
        points=[r for r in rows if r[key] is not None]
        if points:ax.plot([r["current_a"] for r in points],[r[key] for r in points],"o-",label=label,markersize=4)
    if assessment and view!="Blindwiderstand":
        s=Settings(**assessment["settings"])
        limit=s.voltage_limit_v/math.sqrt(2) if view=="Sinus / XL" else s.voltage_limit_v
        ax.axhline(limit,color="#a45523",linestyle="--",label=f"Grenze: {limit:.5g} V")
        if view=="PWM":ax.axhline(0 if s.pwm_mode=="slow" else -s.voltage_limit_v,color="#a45523",linestyle="--")
    ax.set_xlabel("Sinusstrom, effektiv [A]" if view!="PWM" else "PWM-Mittelstrom [A]")
    ax.set_ylabel(ylabel);ax.set_title(view+" · ideales RL-Modell");ax.grid(alpha=.18)
    if ax.lines:ax.legend(fontsize=8,loc="best")
    else:ax.text(.5,.5,"Keine passenden R-/L-Werte verfügbar.",transform=ax.transAxes,ha="center")
    fig.text(.5,.02,"Sinus: Ieff·|Z| · PWM: R·Imittel und Stromänderung · keine Kern-/Schaltverluste",ha="center",fontsize=8,color="#596773")
    fig.subplots_adjust(left=.15,right=.97,top=.9,bottom=.17)
    return fig


def export(assessment,directory):
    """Explicitly requested export; no automatic directory creation."""
    from model import save_json
    directory=Path(directory)
    if not directory.is_dir():raise ValueError("Vorhandenen Zielordner wählen.")
    save_json(directory/"impedanz.json",assessment)
    rows=assessment["rows"]
    with (directory/"impedanz.csv").open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),delimiter=";")
        writer.writeheader();writer.writerows(rows)
    for view,name in (("Sinus / XL","sinus"),("PWM","pwm"),("Blindwiderstand","widerstand")):
        figure(assessment,view).savefig(directory/(f"impedanz_{name}.png"),dpi=160)
