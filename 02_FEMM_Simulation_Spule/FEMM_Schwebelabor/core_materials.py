"""App-eigene Kernmaterialien; unabhängig von FEMMs matlib.dat.

3C91 ist ein ausdrücklich gekennzeichnetes Schätzmodell, keine gemessene
DC-Neukurve. Herleitung, Quelle und Grenzen: MATERIAL_3C91.md.
"""
import math

NAME_3C91 = "3C91 (25 C, Naeherung)"
MU0 = 4 * math.pi * 1e-7
SOURCE_3C91 = "https://megatron.ch/downloads/pdf/materialien/3c91.pdf"
MU_INITIAL_3C91 = 3000.0
H_REFERENCE_3C91 = 1200.0  # A/m; Datenblatt-Test bei 10 kHz
B_REFERENCE_3C91 = 0.470  # T bei 25 Grad C
# Magnetische Polarisation bei hohem H. Der Vakuumanteil wächst weiter.
J_LIMIT_3C91 = B_REFERENCE_3C91 - MU0 * H_REFERENCE_3C91


def flux_density_3c91(h):
    """H [A/m] -> B [T], isotrope hysteresefreie Sättigungsnäherung."""
    return MU0*h + J_LIMIT_3C91*math.tanh(
        MU0*(MU_INITIAL_3C91-1)*h/J_LIMIT_3C91)


# Dichte Punkte im Knie, grosser Bereich mit Vakuumsteigung nach Sättigung.
H_POINTS_3C91 = (0, 0.1, 0.5, 1, 2, 3, 4, *range(5, 1001, 5),
                1200, 1500, 2000, 5000, 10000, 100000, 1000000)
BH_3C91 = tuple((flux_density_3c91(h), float(h)) for h in H_POINTS_3C91)


def metadata():
    return {NAME_3C91: dict(mu=MU_INITIAL_3C91, hc=0, bh=len(BH_3C91))}


def note(name):
    if name != NAME_3C91:
        return ""
    return ("3C91-Ferrit: geschätzte nichtlineare B-H-Kurve bei 25 °C; "
            "µi ≈ 3000, B ≈ 0,47 T bei H = 1200 A/m. "
            "Keine gemessene DC-Kennlinie. Kerntemperatur wird nicht gekoppelt. "
            "Im Temperaturreiter Kerndichte ≈ 4800 kg/m³ und thermische "
            "Kennwerte separat einstellen.")


def add_to_femm(femm, name):
    """Eigene Definition laden; True verhindert mi_getmaterial für diesen Namen."""
    if name != NAME_3C91:
        return False
    # FEMM-Leitfähigkeit in MS/m: 1/(5 Ohm*m) / 1e6.
    femm.mi_addmaterial(name, MU_INITIAL_3C91, MU_INITIAL_3C91, 0, 0, 2e-7)
    for b, h in BH_3C91:
        femm.mi_addbhpoint(name, b, h)
    return True
