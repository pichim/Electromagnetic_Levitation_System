"""DC winding model and local incremental RL model; SI units, no GUI/FEMM.

    u = R*i + d(lambda)/dt
    L_diff = partial(lambda)/partial(i), other currents and position fixed
    tau = L_diff/R

The supply limit is the voltage available at the coil circuit terminals.
It does not change the imposed currents in the magnetostatic simulation.
"""
from __future__ import annotations
import math

COPPER_ALPHA = 0.00393  # 1/K, referenced to 20 °C; same default as thermal.py.
MAGNET_FIELDS = ("resistance20_ohm", "lead_resistance_ohm", "temperature_c", "voltage_limit_v")
NUMERIC_FIELDS = ("inductance_enabled", "inductance_step_percent", "inductance_min_step_a")


def errors(m):
    if not m.enabled:
        return []
    issues = []
    for key in MAGNET_FIELDS:
        v = getattr(m, key)
        if v is not None and (type(v) not in (int, float) or not math.isfinite(v)):
            issues.append("Elektrische Eingaben müssen endliche Zahlen sein.")
            return issues
    if m.resistance20_ohm is not None and m.resistance20_ohm <= 0:
        issues.append("Gemessenes R20 muss positiv sein oder leer bleiben.")
    if m.lead_resistance_ohm is None or m.lead_resistance_ohm < 0:
        issues.append("Leitungswiderstand muss mindestens 0 Ω sein.")
    if m.temperature_c is None or not -50 <= m.temperature_c <= 250:
        issues.append("Wicklungstemperatur für die Kupfernäherung: −50 bis 250 °C.")
    if m.voltage_limit_v is not None and m.voltage_limit_v <= 0:
        issues.append("Verfügbare Spannung muss positiv sein oder leer bleiben.")
    return issues


def stationary(m, wire=None):
    """Actual saved case current and temperature, with optional measured R20.

    Lead resistance is supplied at operating temperature, whereas the winding
    R20 is corrected with copper's linear temperature coefficient.
    """
    if not m.enabled:
        return None
    issues = errors(m)
    if issues:
        raise ValueError("\n".join(issues))
    r20 = m.resistance20_ohm
    source = "gemessen" if r20 is not None else "Drahtgeometrie" if wire else "unbekannt"
    if r20 is None and wire:
        r20 = wire["resistance20_ohm"]
    rc = None if r20 is None else r20*(1+COPPER_ALPHA*(m.temperature_c-20))
    r = None if rc is None else rc+m.lead_resistance_ohm
    u = None if r is None else m.current*r
    limit = m.voltage_limit_v
    reserve = None if u is None or limit is None else limit-abs(u)
    data = dict(wire or {})
    data.update(current_a=m.current, resistance20_ohm=r20, resistance_source=source,
        coil_resistance_ohm=rc, lead_resistance_ohm=m.lead_resistance_ohm,
        resistance_ohm=r, temperature_c=m.temperature_c,
        voltage_dc_signed_v=u, voltage_dc_v=None if u is None else abs(u),
        voltage_limit_v=limit, voltage_headroom_v=reserve,
        within_voltage_limit=None if reserve is None else reserve >= -1e-10,
        power_coil_w=None if rc is None else m.current*m.current*rc,
        power_total_w=None if r is None else m.current*m.current*r,
        flux_linkage_wb=None, inductance_h=None, perturbation_a=None,
        inductance_status="Noch nicht berechnet", mutual_inductance_h=None, time_constant_s=None,
        coil_time_constant_s=None, max_current_rise_a_s=None)
    if not all(v is None or not isinstance(v, (int, float)) or math.isfinite(v) for v in data.values()):
        raise ValueError("Elektrische Werte ausserhalb des berechenbaren Zahlenbereichs.")
    return data


def step(current, numerics):
    return max(abs(current)*numerics.inductance_step_percent/100, numerics.inductance_min_step_a)


def circuit_flux(properties):
    # pyFEMM returns (current, volts, flux linkage), possibly complex scalars.
    if len(properties) != 3:
        raise ValueError("FEMM-Schaltungseigenschaften unvollständig.")
    value = complex(properties[2])
    if not math.isfinite(value.real) or not math.isfinite(value.imag) or abs(value.imag) > 1e-9*max(1, abs(value.real)):
        raise ValueError("Keine reelle magnetostatische Flussverkettung von FEMM.")
    return value.real


def add_inductance(data, plus_flux, minus_flux, delta):
    """Central difference; never mask negative/invalid derivatives with abs()."""
    if not math.isfinite(delta) or delta <= 0:
        raise ValueError("Positive endliche Stromänderung für Induktivität erforderlich.")
    inductance = (plus_flux-minus_flux)/(2*delta)
    data["perturbation_a"] = delta
    if not math.isfinite(inductance) or inductance <= 0:
        data["inductance_status"] = "Nicht auswertbar: Flussdifferenz/Netz prüfen"
        return
    data["inductance_h"] = inductance
    data["inductance_status"] = "Berechnet: zentrale Stromdifferenz"
    if data["resistance_ohm"] is not None:
        data["time_constant_s"] = inductance/data["resistance_ohm"]
        data["coil_time_constant_s"] = inductance/data["coil_resistance_ohm"]
    reserve = data["voltage_headroom_v"]
    if reserve is not None and data["within_voltage_limit"]:
        data["max_current_rise_a_s"] = max(0, reserve)/inductance


def summary(data):
    if data is None:
        return "Deaktiviert."
    def n(v, factor=1):
        return "unbekannt" if v is None else f"{v*factor:.5g}"
    text = [f"R20 {n(data['resistance20_ohm'])} Ω ({data['resistance_source']}) · T {n(data['temperature_c'])} °C",
        f"R Spule {n(data['coil_resistance_ohm'])} Ω · R mit Leitungen {n(data['resistance_ohm'])} Ω",
        f"|U DC| {n(data['voltage_dc_v'])} V · P Spule {n(data['power_coil_w'])} W"]
    if data["voltage_limit_v"] is not None:
        text.append(f"Verfügbar {n(data['voltage_limit_v'])} V · Reserve {n(data['voltage_headroom_v'])} V")
        if data["within_voltage_limit"] is False:
            text.append("Spannungsgrenze überschritten: dieser Strom ist stationär nicht erreichbar.")
        elif data["within_voltage_limit"] is True:
            text.append("DC-Spannung innerhalb der Grenze; Stromänderungen benötigen zusätzliche Spannung.")
    else:
        text.append("Keine Spannungsgrenze eingetragen; Erreichbarkeit noch nicht geprüft.")
    text.append(f"L differenziell {n(data['inductance_h'],1000)} mH · τ = L/R {n(data['time_constant_s'],1000)} ms")
    if data["lead_resistance_ohm"]:
        text.append(f"τ nur Spule {n(data['coil_time_constant_s'],1000)} ms")
    if data["perturbation_a"] is not None:
        text.append(f"Teststromänderung ±{n(data['perturbation_a'])} A · {data['inductance_status']}")
    else:
        text.append(data["inductance_status"])
    if data["max_current_rise_a_s"] is not None:
        text.append(f"Lokale Stromanstiegsreserve ≈ {n(data['max_current_rise_a_s'])} A/s (Objekt fest, anderer Strom konstant)")
    if data.get("mutual_inductance_h") is not None:
        text.append(f"Gegeninduktivität zur anderen Spule {n(data['mutual_inductance_h'],1000)} mH")
    return "\n".join(text)


VIEWS = {
    "Spannung über Strom": ("voltage_dc_v", 1, "Benötigte DC-Spannung |U| [V]"),
    "Induktivität über Strom": ("inductance_h", 1000, "Differenzielle Induktivität [mH]"),
    "Zeitkonstante über Strom": ("time_constant_s", 1000, "Elektrische Zeitkonstante τ [ms]"),
}


def figure(job, side="upper", view="Spannung über Strom", fig=None):
    from matplotlib.figure import Figure
    from model import result_electrical, Config
    fig = fig or Figure(figsize=(8, 5), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)
    key, scale, ylabel = VIEWS[view]
    groups = {}
    for row in (job or {}).get("cases", []):
        data = result_electrical(row, side)
        if not data or data.get(key) is None:
            continue
        other = "lower" if side == "upper" else "upper"
        group = (row["config"][side+"_gap"], row[other+"_current_a"])
        groups.setdefault(group, []).append((data["current_a"], data[key]*scale, data))
    for (gap, other), points in sorted(groups.items()):
        points.sort(key=lambda p: p[0])
        ax.plot([p[0] for p in points], [p[1] for p in points], "o-", linewidth=1.6,
                markersize=4, label=f"s = {gap:g} mm · anderer I = {other:g} A")
        bad = [p for p in points if p[2]["within_voltage_limit"] is False]
        if bad:
            ax.scatter([p[0] for p in bad], [p[1] for p in bad], marker="x", color="#a45523", zorder=4)
    if key == "voltage_dc_v" and job:
        limit = getattr(Config.from_dict(job["config"]), side).voltage_limit_v
        if limit is not None:
            ax.axhline(limit, color="#a45523", linestyle="--", label=f"Verfügbar: {limit:g} V")
    if not groups:
        ax.text(.5, .5, "Noch keine Werte verfügbar.\nFür L und τ: Induktivität im Reiter Netz aktivieren und neu berechnen.",
                transform=ax.transAxes, ha="center", va="center", color="#596773", fontsize=10)
    ax.set_xlabel(("Oberer" if side == "upper" else "Unterer")+" Strom [A]")
    ax.set_ylabel(ylabel)
    ax.set_title(view+" · "+("obere" if side == "upper" else "untere")+" Spule")
    ax.grid(alpha=.18)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=8, loc="best")
    fig.text(.5, .02, "Linien verbinden berechnete Punkte · Kreuze: DC-Spannungsgrenze überschritten",
             ha="center", fontsize=8, color="#596773")
    fig.subplots_adjust(left=.14, right=.97, top=.89, bottom=.16)
    return fig
