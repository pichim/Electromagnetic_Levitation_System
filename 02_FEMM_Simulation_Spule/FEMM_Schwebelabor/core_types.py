"""Kerngeometrien: mm, rotationssymmetrisch; ohne FEMM oder GUI."""
import math

CORE_TYPES = {"Zylinderkern (Stabkern)": "rod", "Topfkern (offen)": "pot"}
POT_KEYS = ("pot_inner_d", "pot_outer_d", "pot_back_h")


def shape_errors(m):
    errors = []
    if m.core_kind not in CORE_TYPES.values():
        return ["Unbekannte Kernform."]
    if m.core_kind == "pot":
        if any(type(getattr(m, k)) not in (int, float) or
               not math.isfinite(getattr(m, k)) or getattr(m, k) <= 0 for k in POT_KEYS):
            return ["Topfkern: Innen-/Aussen-Ø und Rückwandstärke müssen positiv und endlich sein."]
        if not m.core_d < m.pot_inner_d < m.pot_outer_d:
            errors.append("Topfkern: Mittelpol-Ø < Topf-Innen-Ø < Topf-Aussen-Ø erforderlich.")
        if not 0 < m.pot_back_h < m.core_l:
            errors.append("Topfkern: Rückwandstärke muss kleiner als die Gesamthöhe sein.")
        if m.coil_od > m.pot_inner_d:
            errors.append("Topfkern: Wicklungs-Aussen-Ø darf den Topf-Innen-Ø nicht überschreiten.")
        if m.coil_offset < 0 or m.coil_offset + m.coil_h > m.core_l - m.pot_back_h + 1e-9:
            errors.append("Topfkern: Wicklung muss zwischen Öffnung und Rückwand liegen.")
    return errors


def core_parts(m):
    """Nicht überlappende Rechtecke: Name, r0, r1, Abstand vom Pol a0, a1."""
    if m.core_kind == "rod":
        return [("Kern", 0, m.core_d / 2, 0, m.core_l)]
    if m.core_kind != "pot":
        raise ValueError("Unbekannte Kernform.")
    rp, ri, ro = m.core_d / 2, m.pot_inner_d / 2, m.pot_outer_d / 2
    back = m.core_l - m.pot_back_h
    return [("Mittelpol", 0, rp, 0, m.core_l),
            ("Rückwand", rp, ro, back, m.core_l),
            ("Aussenwand", ri, ro, 0, back)]


def core_volume_mm3(m):
    return sum(math.pi * (r1*r1-r0*r0) * (a1-a0)
               for _, r0, r1, a0, a1 in core_parts(m))


def enclosed_air_points(m):
    """Luft hinter einer Wicklung, die den Topf radial vollständig ausfüllt.

    Dieser Raum ist vom Aussenraum getrennt und braucht ein eigenes FEMM-Label.
    Sonstige Freiräume sind durch die offene Topffront mit der Aussenluft verbunden.
    Rückgabe: Radius, Abstand von der objektseitigen Polfläche, jeweils in mm.
    """
    if m.core_kind != "pot":
        return []
    rear = m.core_l - m.pot_back_h
    end = m.coil_offset + m.coil_h
    if m.coil_id == m.core_d and m.coil_od == m.pot_inner_d and end < rear:
        return [((m.core_d + m.pot_inner_d) / 4, (end + rear) / 2)]
    return []


def pot_exterior_area_mm2(m):
    """Äusserer Mantel, Rückseite, Mittelpol- und Wandstirnfläche; ohne Topfinneres."""
    rp, ri, ro = m.core_d / 2, m.pot_inner_d / 2, m.pot_outer_d / 2
    return 2*math.pi*ro*m.core_l + math.pi*(ro*ro + rp*rp + ro*ro-ri*ri)
