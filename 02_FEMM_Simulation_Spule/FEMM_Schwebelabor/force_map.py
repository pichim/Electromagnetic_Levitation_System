"""Statisches FEMM-Kraftkennfeld Fz(I, s); keine Regelung und kein Kraft-Fit."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import csv
import json
import math
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure

DEFAULTS = dict(current_side="upper", current_start=0.0, current_end=4.0,
                current_step=0.5, gap_start=10.0, gap_end=20.0, gap_step=5.0)
VIEWS = ("Kraft über Strom", "Kraft über Luftspalt", "Farbkarte", "3D-Kennfeld")
MAX_POINTS = 5000


def axes(options):
    from model import sweep_values
    currents = sweep_values(*(options["current_"+k] for k in ("start", "end", "step")))
    gaps = sweep_values(*(options["gap_"+k] for k in ("start", "end", "step")))
    if len(currents)*len(gaps) > MAX_POINTS:
        raise ValueError(f"Maximal {MAX_POINTS} FEMM-Fälle pro Kennfeld; Schrittweiten vergrössern.")
    return currents, gaps


def parse_settings(data):
    if not isinstance(data, dict) or set(data) != set(DEFAULTS):
        raise ValueError("Ungültige Kraftkennfeld-Einstellungen.")
    if data["current_side"] not in {"upper", "lower"}:
        raise ValueError("Kraftkennfeld: obere oder untere Stromspule wählen.")
    for key in DEFAULTS:
        if key != "current_side" and (type(data[key]) not in (int, float) or not math.isfinite(data[key])):
            raise ValueError("Kraftkennfeld: endliche Zahlen erforderlich.")
    axes(data)
    if data["gap_start"] <= 0:
        raise ValueError("Kraftkennfeld: Luftspalte müssen grösser als 0 mm sein.")
    return deepcopy(data)


def case_at(base, options, current, gap):
    """Zwei aktive Pole bleiben ortsfest; bei einem Pol ist nur dessen Abstand relevant."""
    case = deepcopy(base)
    side = options["current_side"]
    other = "lower" if side == "upper" else "upper"
    getattr(case, side).current = current
    setattr(case, side+"_gap", gap)
    if base.upper.enabled and base.lower.enabled:
        setattr(case, other+"_gap", base.upper_gap+base.lower_gap-gap)
    return case


def validate_options(base, options):
    from model import validate
    options = parse_settings(options)
    side = options["current_side"]
    if not base.object.enabled or not getattr(base, side).enabled:
        raise ValueError("Kraftkennfeld benötigt ein aktives Objekt und die ausgewählte Spule.")
    currents, gaps = axes(options)
    if base.upper.enabled and base.lower.enabled and gaps[-1] >= base.upper_gap+base.lower_gap:
        raise ValueError("Bei zwei festen Magneten muss jeder Luftspalt kleiner als die Summe der beiden Ausgangsluftspalte sein. Sonst berührt das Objekt den anderen Pol.")
    for gap in gaps:
        for current in {currents[0], currents[-1]}:
            errors, _ = validate(case_at(base, options, current, gap))
            if errors:
                raise ValueError(f"Kraftkennfeld bei I={current:g} A, s={gap:g} mm:\n"+"\n".join(errors))
    return currents, gaps


def grid(job):
    """Zeilen = Luftspalte, Spalten = Ströme. Fehlende Punkte bleiben NaN."""
    currents, gaps = axes(job["options"])
    forces = np.full((len(gaps), len(currents)), np.nan)
    side = job["options"]["current_side"]
    ci = {round(x, 12): i for i, x in enumerate(currents)}
    gi = {round(x, 12): i for i, x in enumerate(gaps)}
    for result in job.get("cases", []):
        i = ci.get(round(result[side+"_current_a"], 12))
        g = gi.get(round(result["config"][side+"_gap"], 12))
        if i is not None and g is not None:
            forces[g, i] = result["magnetic_force_z_n"]
    return np.array(currents), np.array(gaps), forces


def export(job, directory):
    """SI-Langform, zwei Matrizen, NPZ und vollständige Parameter als JSON."""
    from model import Config, coordinates, mass, save_json, result_electrical
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    currents, gaps, forces = grid(job)
    base = Config.from_dict(job["config"])
    side = job["options"]["current_side"]
    results = {(round(r[side+"_current_a"], 12), round(r["config"][side+"_gap"], 12)): r
               for r in job.get("cases", [])}
    errors = {(round(r["current_a"], 12), round(r["gap_mm"], 12)): r["error"]
              for r in job.get("map_errors", [])}
    rows = []
    electrical_keys = ("voltage_dc_v", "voltage_dc_signed_v", "voltage_limit_v", "voltage_headroom_v",
                       "within_voltage_limit", "resistance_ohm", "temperature_c", "flux_linkage_wb",
                       "inductance_h", "mutual_inductance_h", "time_constant_s", "perturbation_a")
    matrices = {s+"_"+k: np.full(forces.shape, np.nan) for s in ("upper","lower") for k in electrical_keys}
    for j, gap in enumerate(gaps):
        for i, current in enumerate(currents):
            case = case_at(base, job["options"], float(current), float(gap))
            p = coordinates(case)
            key = (round(current, 12), round(gap, 12))
            result = results.get(key)
            force = float(forces[j, i]) if result else None
            rows.append(dict(current_a=float(current), gap_m=float(gap)/1000, gap_mm=float(gap),
                magnetic_force_z_n=force, upper_current_a=case.upper.current if case.upper.enabled else 0,
                lower_current_a=case.lower.current if case.lower.enabled else 0,
                upper_gap_m=case.upper_gap/1000, lower_gap_m=case.lower_gap/1000,
                pole_spacing_m=p["h"]/1000, object_z_m=p["center"]/1000,
                mass_kg=mass(case), weight_n=mass(case)*9.81,
                net_force_z_n=force-mass(case)*9.81 if force is not None else None,
                status="berechnet" if result else "Fehler" if key in errors else "nicht berechnet",
                error=errors.get(key, ""), result_directory=result["directory"] if result else ""))
            for s in ("upper", "lower"):
                data = result_electrical(result, s) if result else None
                for k in electrical_keys:
                    value = data.get(k) if data else None
                    rows[-1][s+"_"+k] = value
                    if value is not None:
                        matrices[s+"_"+k][j, i] = value
    def write_csv(name, header, values):
        path = directory/name
        tmp = path.with_suffix(path.suffix+".tmp")
        with tmp.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(header)
            writer.writerows(values)
        tmp.replace(path)
    write_csv("kraftkennfeld.csv", list(rows[0]), ([row[k] for k in rows[0]] for row in rows))
    write_csv("kraftmatrix_abstand_strom.csv", ["gap_m / current_a", *currents],
              ([gap/1000, *(float(v) if np.isfinite(v) else "" for v in forces[j])] for j, gap in enumerate(gaps)))
    write_csv("kraftmatrix_strom_abstand.csv", ["current_a / gap_m", *(gaps/1000)],
              ([current, *(float(v) if np.isfinite(v) else "" for v in forces[:, i])] for i, current in enumerate(currents)))
    metadata = dict(format="femm-force-map", version=2, model_version=job["model_version"],
        status=job["status"], config=job["config"], options=job["options"],
        current_axis="Strom der oberen Spule" if side == "upper" else "Strom der unteren Spule",
        gap_axis="Oberflächen-Luftspalt zwischen Kugel und Pol der Stromspule",
        force="Magnetkraft Fz auf das ganze Objekt, positiv nach oben, in N; ohne Gewichtskraftabzug",
        geometry="Feste Polpositionen, Objekt bewegt sich" if base.upper.enabled and base.lower.enabled else "Ein aktiver Magnet; dessen Luftspalt wird variiert",
        current_a=currents.tolist(), gap_m=(gaps/1000).tolist(),
        magnetic_force_z_n=[[float(v) if np.isfinite(v) else None for v in row] for row in forces],
        matrix_order="Zeilen: gap_m; Spalten: current_a",
        electrical_matrices={key:[[float(v) if np.isfinite(v) else None for v in row] for row in matrix]
                             for key,matrix in matrices.items()},
        voltage_limit_encoding="within_voltage_limit: 1 = eingehalten, 0 = überschritten, null/NaN = unbekannt",
        completed_points=len(results), total_points=forces.size,
        solver=job["cases"][0].get("solver") if job.get("cases") else None,
        cases=[dict(current_a=r[side+"_current_a"], gap_m=r["config"][side+"_gap"]/1000,
                    magnetic_force_z_n=r["magnetic_force_z_n"], directory=r["directory"],
                    electrical={s:result_electrical(r,s) for s in ("upper","lower")},
                    volume_relative_error=r.get("volume_relative_error"), warnings=r.get("warnings", [])) for r in job.get("cases", [])],
        errors=job.get("map_errors", []),
        note="Statische FEMM-Kraftwerte; L ist die lokale zentrale Fluss-Strom-Ableitung, τ=L/R. Keine geschlossene Regelung oder Bewegungsinduktion. Kurvenlinien verbinden nur berechnete Punkte. Fehlende Werte bleiben leer/null/NaN. Netz und Testschritt vor späterer Nutzung prüfen.")
    save_json(directory/"kraftkennfeld.json", metadata)
    tmp = directory/"kraftkennfeld.npz.tmp"
    with tmp.open("wb") as stream:
        np.savez(stream, current_a=currents, gap_m=gaps/1000, magnetic_force_z_n=forces,
                 valid=np.isfinite(forces), metadata_json=json.dumps(metadata, ensure_ascii=False, allow_nan=False), **matrices)
    tmp.replace(directory/"kraftkennfeld.npz")


def figure(job, view=VIEWS[0], fig=None, fixed=None):
    from model import Config
    fig = fig or Figure(figsize=(9, 5.5), dpi=100)
    fig.clear()
    fig.set_facecolor("#ffffff")
    if job is None:
        ax = fig.add_subplot(111)
        ax.set_axis_off()
        ax.text(.5, .5, "Ströme und Luftspalte oben einstellen.\nDann Kraftkennfeld berechnen.", ha="center", va="center", transform=ax.transAxes, color="#596773")
        return fig
    currents, gaps, forces = grid(job)
    side = job["options"]["current_side"]
    label = "Obere" if side == "upper" else "Untere"
    valid = np.isfinite(forces)
    ax = fig.add_subplot(111, projection="3d" if view == VIEWS[3] else None)
    if not valid.any():
        ax.text2D(.5, .5, "Noch keine berechneten Punkte", transform=ax.transAxes) if view == VIEWS[3] else ax.text(.5, .5, "Noch keine berechneten Punkte", transform=ax.transAxes, ha="center")
    elif view in VIEWS[:2]:
        over_current = view == VIEWS[0]
        values, rows = (gaps, forces) if over_current else (currents, forces.T)
        x = currents if over_current else gaps
        symbol, unit = ("s", "mm") if over_current else ("I", "A")
        selected = None if fixed is None else int(np.argmin(abs(values-fixed)))
        # Assign colours using the complete axis, so a selected curve retains its colour.
        cmap = colormaps["tab10" if len(values) <= 10 else "tab20" if len(values) <= 20 else "viridis"]
        norm = Normalize(values[0], values[-1] if len(values) > 1 else values[0]+1)
        for index, (value, row) in enumerate(zip(values, rows)):
            if selected is not None and index != selected: continue
            if np.isfinite(row).any():
                color = cmap(index) if len(values) <= 20 else cmap(norm(value))
                ax.plot(x, row, "o-", color=color, linewidth=1.8, markersize=3.5,
                        label=f"{symbol} = {value:g} {unit}")
        ax.set_xlabel(f"Strom I [A] · {label.lower()} Spule" if over_current else
                      f"Oberflächen-Luftspalt s [mm] · {label.lower()} Spule", labelpad=8)
        ax.set_ylabel("Magnetkraft Fz [N] · positiv nach oben", labelpad=8)
        ax.set_title("Kraft über Strom · je Kurve ein fester Luftspalt" if over_current else
                     "Kraft über Luftspalt · je Kurve ein fester Strom", fontsize=12, pad=14)
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            title = "Luftspalt je Kurve" if over_current else "Strom je Kurve"
            if len(handles) <= 24:
                # Always show all entries, including the 17-current example.
                # Two columns fit a low or small application window.
                fig.subplots_adjust(right=.70 if len(handles)>12 else .77)
                ax.legend(handles, labels, title=title, fontsize=8, title_fontsize=9,
                          loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0,
                          frameon=False, ncol=2 if len(handles)>12 else 1,
                          columnspacing=1.0, handlelength=1.7, labelspacing=.5)
            else:
                fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), ax=ax,
                             label=f"{title}: {symbol} [{unit}]", pad=.025, fraction=.05)
        ax.set_facecolor("#fafbfd")
        ax.grid(color="#dce2e8", alpha=.8, linewidth=.6)
        ax.spines[["top", "right"]].set_visible(False)
        for spine in ax.spines.values(): spine.set_color("#a9b3bd")
        ax.tick_params(labelsize=9, colors="#374151")
    elif view == VIEWS[2]:
        def edges(values):
            # Farbflächen enden am berechneten Bereich; keine Extrapolation.
            return np.r_[values[0], (values[:-1]+values[1:])/2, values[-1]]
        cmap = colormaps["viridis"].copy()
        cmap.set_bad("#eeeeee")
        xx, yy = np.meshgrid(currents, gaps)
        if len(currents)>1 and len(gaps)>1:
            plot = ax.pcolormesh(edges(currents), edges(gaps), np.ma.masked_invalid(forces), cmap=cmap)
            ax.scatter(xx[valid], yy[valid], color="#ffffff", edgecolors="#334155",
                       linewidths=.4, s=8, clip_on=False)
            ax.set_xlim(currents[0],currents[-1])
            ax.set_ylim(gaps[0],gaps[-1])
        else:
            plot = ax.scatter(xx[valid], yy[valid], c=forces[valid], cmap=cmap, marker="s", s=100)
        ax.set_xlabel(f"{label} Spule: Strom I [A]")
        ax.set_ylabel(f"{label} Spule: Luftspalt s [mm]")
        ax.set_title("Kraftkennfeld Fz(I, s)")
        fig.colorbar(plot, ax=ax, label="Magnetkraft Fz [N] · + nach oben")
    else:
        xx, yy = np.meshgrid(currents, gaps)
        norm = Normalize(float(forces[valid].min()), float(forces[valid].max()))
        if len(currents)>1 and len(gaps)>1 and valid.all():
            ax.plot_surface(xx, yy, forces, cmap="viridis", norm=norm, alpha=.88,
                            linewidth=.3, edgecolor=(.3, .4, .5, .2))
        points = ax.scatter(xx[valid], yy[valid], forces[valid], c=forces[valid],
                            cmap="viridis", norm=norm, s=12, depthshade=False)
        ax.set_xlabel("Strom I [A]", labelpad=9)
        ax.set_ylabel("Luftspalt s [mm]", labelpad=9)
        ax.set_zlabel("Magnetkraft Fz [N]", labelpad=9)
        ax.set_title(f"Kraftkennfeld · {label.lower()} Spule", fontsize=12, pad=8)
        ax.view_init(elev=28, azim=-135, roll=0)
        ax.set_proj_type("ortho")
        ax.set_box_aspect((1.2, 1.05, .85), zoom=1.08)
        ax.tick_params(labelsize=8, pad=1)
        fig.colorbar(points, ax=ax, label="Magnetkraft Fz [N] · positiv nach oben",
                     shrink=.7, pad=.06, fraction=.035)
    base = Config.from_dict(job["config"])
    other = "lower" if side == "upper" else "upper"
    fixed = getattr(base, other)
    context = (f"Andere Spule konstant: {fixed.current:g} A" if fixed.enabled else "Andere Spule deaktiviert")
    context += " · feste Polpositionen" if base.upper.enabled and base.lower.enabled else " · ein aktiver Magnet"
    fig.text(.5, .025, f"{valid.sum()}/{forces.size} FEMM-Punkte · {context}\nLinien und Flächen verbinden berechnete Punkte.", ha="center", fontsize=8, color="#596773")
    # Leave more room for the plot and keep the footer clear of axis labels.
    if view == VIEWS[3]:
        fig.subplots_adjust(left=.015, bottom=.12, top=.92)
    elif view in VIEWS[:2]:
        fig.subplots_adjust(left=.10, bottom=.18, top=.89)
    else:
        fig.subplots_adjust(left=.10, bottom=.18, top=.89, right=.95)
    return fig


def save_figures(job, directory):
    for view, name in zip(VIEWS, ("kraft_ueber_strom.png", "kraft_ueber_luftspalt.png", "kraftkennfeld_farbkarte.png", "kraftkennfeld_3d.png")):
        figure(job, view).savefig(Path(directory)/name, dpi=160)
