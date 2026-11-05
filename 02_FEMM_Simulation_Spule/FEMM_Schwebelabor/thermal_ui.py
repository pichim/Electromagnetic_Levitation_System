"""Temperaturansicht mit direkt erreichbarem Betrieb und flexiblem Diagramm."""
from dataclasses import asdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
import thermal

SIDES = {"Obere Spule": "upper", "Untere Spule": "lower"}
LABELS = {
    "ambient_c": "Umgebung [°C]", "duration_min": "Betriebsdauer [min]",
    "limit_c": "Temperaturgrenze [°C]", "initial_c": "Starttemperatur [°C]",
    "h_copper": "Wärmeabgabe Wicklung h [W/(m² K)]",
    "h_core": "Wärmeabgabe Kern h [W/(m² K)]",
    "coupling_w_k": "Wärmeübergang Wicklung–Kern [W/K]",
    "copper_exposed_percent": "Freie Wicklungsfläche [%]", "core_exposed_percent": "Freie Kernfläche [%]",
    "copper_density": "Kupferdichte [kg/m³]", "core_density": "Kerndichte [kg/m³]",
    "copper_cp": "Spezifische Wärmekapazität Kupfer [J/(kg K)]",
    "core_cp": "Spezifische Wärmekapazität Kern [J/(kg K)]",
    "copper_alpha": "Kupfer-Temperaturkoeffizient [1/K]",
}


class ThermalTab(ttk.Frame):
    def __init__(self, parent, read_magnet, canvas_class, toolbar_class, save_plot, scroll_class):
        super().__init__(parent, padding=(8, 6))
        self.read_magnet, self.save_plot = read_magnet, save_plot
        self.result, self.result_side, self.muted = None, None, True
        self.compact = False
        self.parameters = {k: tk.StringVar(value="" if v is None else str(v))
                           for k, v in asdict(thermal.Settings()).items()}
        self.side = tk.StringVar(value="Obere Spule")
        self.cooling_preset = tk.StringVar(value="Ruhende Luft (Annahme)")
        self.entries = {}
        header = ttk.Frame(self);header.pack(fill="x");header.columnconfigure(1, weight=1)
        self.selector = ttk.Combobox(header, textvariable=self.side, values=list(SIDES), state="readonly", width=17)
        self.selector.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.calculate_button = ttk.Button(header, text="Temperatur berechnen", command=self.calculate)
        self.calculate_button.grid(row=0, column=2, sticky="e")
        header.bind("<Configure>", lambda e: self.calculate_button.grid(
            row=0 if e.width >= self.selector.winfo_reqwidth()+self.calculate_button.winfo_reqwidth()+10 else 1,
            column=2 if e.width >= self.selector.winfo_reqwidth()+self.calculate_button.winfo_reqwidth()+10 else 0,
            sticky="e"))
        self.source_note = self.hint(self, "Spulendaten aus den Reitern Oben/Unten.")
        operating = ttk.Frame(self);operating.pack(fill="x", pady=(1, 3))
        fields = []
        for key in ["ambient_c", "duration_min", "limit_c"]:
            field = ttk.Frame(operating)
            ttk.Label(field, text=LABELS[key]).pack(side="left", padx=(0, 5))
            entry = ttk.Entry(field, textvariable=self.parameters[key], width=8);entry.pack(side="left")
            self.entries[key] = entry;fields.append(field)
        operating.bind("<Configure>", lambda e: self.arrange(fields, e.width))
        cooling_row = ttk.Frame(self);cooling_row.pack(fill="x", pady=(3, 0))
        ttk.Label(cooling_row, text="Kühlung:").pack(side="left", padx=(0, 5))
        self.cooling_box = ttk.Combobox(cooling_row, textvariable=self.cooling_preset,
            values=list(thermal.COOLING_PRESETS)+["Benutzerdefiniert"], state="readonly", width=25)
        self.cooling_box.pack(side="left")
        self.cooling_box.bind("<<ComboboxSelected>>", self.choose_cooling)
        self.parameters_note = self.hint(self, "")
        self.parameters_valid = True

        # Nur die Annahmen scrollen. Der Verlauf nutzt die ganze restliche Höhe.
        self.pages = ttk.Notebook(self);self.pages.pack(fill="both", expand=True, pady=(2, 0))
        self.curve_page = ttk.Frame(self.pages, padding=(6, 4))
        self.settings_page = ttk.Frame(self.pages)
        self.details_page = ttk.Frame(self.pages, padding=(8, 6))
        for page, title in [(self.curve_page, "Temperaturverlauf"), (self.settings_page, "Kühlung und Stoffwerte"),
                            (self.details_page, "Rechendetails")]:self.pages.add(page, text=title)
        self.output_status = self.hint(self.curve_page, "Betrieb einstellen und Temperatur berechnen.")
        cards = ttk.Frame(self.curve_page);cards.pack(fill="x", pady=(0, 3))
        self.result_values, self.result_captions = {}, []
        for col, (key, title, colour) in enumerate([
                ("copper", "Wicklung", "#b25122"), ("core", "Kern", "#246b96"), ("power", "Kupferverluste", "#425564")]):
            cards.columnconfigure(col, weight=1, uniform="thermal")
            card = ttk.LabelFrame(cards, text=title, padding=(8, 5))
            card.grid(row=0, column=col, sticky="nsew", padx=(0, 6) if col < 2 else 0)
            value = ttk.Label(card, text="— °C" if key != "power" else "— W",
                              font=("Segoe UI", 15, "bold"), foreground=colour);value.pack(anchor="center")
            caption = ttk.Label(card, text="Mittelwert am Ende" if key != "power" else "Verlustleistung am Ende",
                                style="Hint.TLabel", font=("Segoe UI", 9), anchor="center");caption.pack(fill="x")
            card.bind("<Configure>", lambda e, label=caption: label.configure(wraplength=max(80, e.width-16)))
            self.result_values[key] = value
            self.result_captions.append(caption)
        self.limit_note = self.hint(self.curve_page, "Die Grenze wird für Wicklung und Kern ausgewertet.")
        tools = ttk.Frame(self.curve_page);tools.pack(side="bottom", fill="x", pady=(2, 0))
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.canvas = canvas_class(self.figure, master=self.curve_page)
        self.csv_button = ttk.Button(tools, text="CSV speichern", command=self.export_csv, state="disabled")
        self.csv_button.pack(side="right", padx=3)
        self.png_button = ttk.Button(tools, text="PNG speichern", command=lambda: self.save_plot(self.figure), state="disabled")
        self.png_button.pack(side="right", padx=3)
        self.toolbar = toolbar_class(self.canvas, tools, pack_toolbar=False);self.toolbar.pack(side="left")
        self.canvas.get_tk_widget().configure(height=1, width=1)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        ax = self.figure.add_subplot(111);ax.set_axis_off()
        ax.text(.5, .5, "Spule wählen, Betrieb einstellen und berechnen.\nHier erscheint der Verlauf von Wicklung und Kern.",
                transform=ax.transAxes, ha="center", va="center", color="#596773")
        self.canvas.draw_idle()

        self.scroll = scroll_class(self.settings_page, fit_width=True);self.scroll.pack(fill="both", expand=True)
        self.settings_body = self.scroll.body
        self.current_geometry_note = self.hint(self.settings_body, "")
        self.group("Starttemperatur", ["initial_c"],
                   "Leer lassen: Wicklung und Kern starten bei Umgebungstemperatur. Für eine warme Spule die gemeinsame Starttemperatur eingeben.")
        self.group("Kühlung an die Umgebung", ["h_copper", "h_core"],
                   "h beschreibt, wie gut eine Oberfläche Wärme an die Umgebung abgibt. Grösseres h bedeutet stärkere Kühlung. "
                   "Ruhende Luft: 8; Luftstrom: 30 W/(m² K). Diese Vorgaben sind Annahmen, keine Messwerte. Beide Werte sind einzeln anpassbar.")
        self.group("Wärmeaustausch zwischen Wicklung und Kern", ["coupling_w_k"],
                   "1 W/K bedeutet: Bei 1 °C Temperaturunterschied werden 1 W übertragen. 0 bedeutet keinen Wärmeaustausch. "
                   "Lack, Spulenkörper und Kontakt beeinflussen diesen Wert.")
        self.group("An die Umgebung abgegebene Wärmefläche", ["copper_exposed_percent", "core_exposed_percent"],
                   "100 % = alle Modellflächen frei; kleinere Werte berücksichtigen Abdeckungen. "
                   "Zylinderkern: Wicklungsmantel und beide Ringflächen; freier Kernmantel und Stirnflächen. "
                   "Topfkern: offene Wicklungs-Ringfläche sowie äusserer Kernmantel, Rückseite und Polflächen. "
                   "Innere Topfflächen zählen nicht zur direkten Umgebungskühlung.")
        self.group("Stoffwerte des Kupferdrahts", ["copper_density", "copper_cp", "copper_alpha"],
                   "Die Vorgaben gelten näherungsweise für Kupfer. Die Masse folgt aus Drahtdurchmesser und Drahtlänge.")
        self.group("Stoffwerte des Kerns", ["core_density", "core_cp"],
                   "Die Vorgaben gelten näherungsweise für Eisen/Stahl. Bei Ferrit oder anderem Material anpassen. "
                   "Die magnetische Materialauswahl setzt diese thermischen Werte nicht automatisch. "
                   "Die Kernmasse folgt aus der gewählten Zylinder- oder Topfkerngeometrie.")
        ttk.Button(self.settings_body, text="Thermische Annahmen zurücksetzen", command=self.reset_parameters).pack(anchor="w", pady=8)
        self.hint(self.settings_body, "Berechnet werden mittlere Temperaturen bei konstantem Strom. "
                  "Spulenkörpermasse, Eisenverluste, PWM-Rippel und gegenseitige Erwärmung zweier Spulen sind nicht enthalten. "
                  "Strahlung ist nicht separat enthalten. Die Kurve endet spätestens bei 300 °C.")
        self.details_note = self.hint(self.details_page, "Hier stehen die Werte der letzten Berechnung.")
        report_bar = ttk.Scrollbar(self.details_page);report_bar.pack(side="right", fill="y")
        self.report = tk.Text(self.details_page, wrap="word", font=("Segoe UI", 10), relief="flat", padx=8, pady=8,
                              yscrollcommand=report_bar.set, state="disabled")
        report_bar.configure(command=self.report.yview);self.report.pack(fill="both", expand=True)
        self.pages.bind("<<NotebookTabChanged>>", lambda e: self.after_idle(self.canvas.fit_to_widget))
        self.bind("<Configure>", self.resize_layout, add="+")
        self.side.trace_add("write", lambda *_: self.inputs_changed())
        for variable in self.parameters.values():variable.trace_add("write", lambda *_: self.inputs_changed())
        self.muted = False;self.inputs_changed()

    @staticmethod
    def arrange(fields, width):
        row = column = used = 0
        for field in fields:
            size = field.winfo_reqwidth()+14
            if column and used+size > width:row, column, used = row+1, 0, 0
            field.grid(row=row, column=column, sticky="w", padx=(0, 14), pady=2)
            used += size;column += 1

    def hint(self, parent, text):
        label = ttk.Label(parent, text=text, justify="left", style="Hint.TLabel", wraplength=450)
        label.pack(fill="x", pady=(2, 4))
        parent.bind("<Configure>", lambda e: label.configure(wraplength=max(100, e.width-16)), add="+")
        return label

    def group(self, title, fields, hint):
        group = ttk.LabelFrame(self.settings_body, text=title, padding=10);group.pack(fill="x", pady=(4, 8))
        for key in fields:
            row = ttk.Frame(group);row.pack(fill="x", pady=4);row.columnconfigure(0, weight=1)
            label = ttk.Label(row, text=LABELS[key], wraplength=350, justify="left")
            label.grid(row=0, column=0, sticky="w", padx=(0, 12))
            entry = ttk.Entry(row, textvariable=self.parameters[key], width=12)
            entry.grid(row=0, column=1, sticky="e");self.entries[key] = entry
            row.bind("<Configure>", lambda e, label=label, entry=entry:
                     label.configure(wraplength=max(100, e.width-entry.winfo_reqwidth()-16)))
        self.hint(group, hint);return group

    def resize_layout(self, event):
        compact = event.height < 500*float(self.tk.call("tk", "scaling"))/(96/72)
        if compact == self.compact:return
        self.compact = compact
        for caption in self.result_captions:
            if compact:caption.pack_forget()
            else:caption.pack(fill="x")
        self.note_visibility()

    def note_visibility(self):
        # Fehlermeldungen bleiben auch im kompakten Layout sichtbar.
        if self.compact and self.parameters_valid:self.parameters_note.pack_forget()
        elif not self.parameters_note.winfo_manager():
            self.parameters_note.pack(fill="x", pady=(2, 4), before=self.pages)

    def read_settings(self):
        values = {}
        for key, variable in self.parameters.items():
            text = variable.get().strip().replace(",", ".")
            try:values[key] = None if key == "initial_c" and not text else float(text)
            except ValueError:raise ValueError(LABELS[key]+": gültige Zahl eingeben.") from None
        settings = thermal.Settings(**values);thermal.validate_settings(settings);return settings

    def selected_side(self):
        if self.side.get() not in SIDES:raise ValueError("Obere oder untere Spule auswählen.")
        return SIDES[self.side.get()]

    def inputs_changed(self):
        if self.muted:return
        self.refresh_coil()
        try:
            settings = self.read_settings()
            coil = thermal.Coil.from_magnet(self.read_magnet(self.selected_side()))
            thermal.coil_data(coil, settings)
            self.parameters_valid = True
            self.cooling_preset.set(next((name for name, value in thermal.COOLING_PRESETS.items()
                                         if settings.h_copper == settings.h_core == value), "Benutzerdefiniert"))
            self.parameters_note.configure(text="Mittlere Temperaturen bei konstantem Strom. Weitere Annahmen unter „Kühlung und Stoffwerte“.", foreground="#596773")
            self.calculate_button.configure(state="normal")
            fresh = (self.result is not None and self.result_side == self.selected_side()
                     and self.result.coil == coil and self.result.settings == settings)
            if fresh:self.output_status.configure(text=self.result_context(), foreground="#596773")
            elif self.result is not None:
                self.output_status.configure(text="Eingaben geändert – erneut berechnen. Angezeigt bleibt: "+self.result_context(), foreground="#9a3e28")
            else:self.output_status.configure(text="Betrieb einstellen und Temperatur berechnen.", foreground="#596773")
        except ValueError as error:
            self.parameters_valid = False
            self.parameters_note.configure(text="Bitte korrigieren: "+str(error), foreground="#9a3e28")
            self.calculate_button.configure(state="disabled")
            self.output_status.configure(text="Berechnung blockiert. "+("Angezeigt bleibt das letzte Ergebnis." if self.result is not None else "Eingaben oben prüfen."), foreground="#9a3e28")
        self.note_visibility()

    def refresh_coil(self):
        try:
            magnet = self.read_magnet(self.selected_side())
            diameter = "unbekannt" if magnet.wire_d_mm is None else f"{magnet.wire_d_mm:g} mm"
            name = "Topfkern" if magnet.core_kind == "pot" else "Zylinderkern"
            self.source_note.configure(text=f"{name} · {magnet.current:g} A · {magnet.turns:g} Windungen · Kupfer-Ø {diameter}. Strom/Abmessungen: Oben/Unten.")
            core = (f"Topfkern: Mittelpol Ø {magnet.core_d:g}, Gesamthöhe {magnet.core_l:g}, innen/aussen Ø "
                    f"{magnet.pot_inner_d:g}/{magnet.pot_outer_d:g}, Rückwand {magnet.pot_back_h:g} mm" if magnet.core_kind == "pot" else
                    f"Zylinderkern: Ø {magnet.core_d:g} × {magnet.core_l:g} mm")
            self.current_geometry_note.configure(text=f"Übernommene Daten: {self.side.get()} · {core} · Material {magnet.material}.\n"
                f"Wicklung: innen/aussen Ø {magnet.coil_id:g}/{magnet.coil_od:g} mm, Höhe {magnet.coil_h:g} mm, Position {magnet.coil_offset:g} mm.")
        except ValueError as error:
            self.source_note.configure(text="Spulendaten unvollständig: "+str(error))
            self.current_geometry_note.configure(text="Gewählte Spule in Oben/Unten aktivieren und Eingaben vervollständigen.")

    def choose_cooling(self, event=None):
        value = thermal.COOLING_PRESETS.get(self.cooling_preset.get())
        if value is not None:
            self.muted = True
            for key in ["h_copper", "h_core"]:self.parameters[key].set(str(value))
            self.muted = False;self.inputs_changed()
        else:self.pages.select(self.settings_page)

    def reset_parameters(self):
        self.apply_settings({"side": self.selected_side(), "parameters": asdict(thermal.Settings())})

    def settings_payload(self):return {"side": self.selected_side(), "parameters": asdict(self.read_settings())}

    @staticmethod
    def parse_settings(data):
        if not isinstance(data, dict) or set(data) != {"side", "parameters"} or data["side"] not in {"upper", "lower"}:
            raise ValueError("Ungültige Temperatur-Einstellungen oder Spulenauswahl.")
        if not isinstance(data["parameters"], dict) or set(data["parameters"]) != set(asdict(thermal.Settings())):
            raise ValueError("Temperatur-Einstellungen enthalten fehlende oder unbekannte Felder.")
        thermal.validate_settings(thermal.Settings(**data["parameters"]));return data

    def apply_settings(self, data=None):
        data = self.parse_settings(data or {"side": "upper", "parameters": asdict(thermal.Settings())})
        self.muted = True
        try:
            self.side.set(next(name for name, value in SIDES.items() if value == data["side"]))
            for key, value in data["parameters"].items():self.parameters[key].set("" if value is None else str(value))
        finally:self.muted = False
        self.inputs_changed()

    def result_context(self):
        r = self.result;side = next(name for name, key in SIDES.items() if key == self.result_side)
        return f"{side} · {r.coil.current:g} A · nach {r.times_s[-1]/60:.4g} min"

    def calculate(self):
        try:
            side = self.selected_side();coil = thermal.Coil.from_magnet(self.read_magnet(side))
            result = thermal.calculate(coil, self.read_settings())
        except ValueError as error:
            self.parameters_note.configure(text="Bitte korrigieren: "+str(error), foreground="#9a3e28")
            self.output_status.configure(text="Berechnung blockiert: "+str(error), foreground="#9a3e28");return
        self.result, self.result_side = result, side
        thermal.draw_figure(result, self.figure);self.toolbar.update();self.toolbar.push_current();self.canvas.draw_idle()
        self.pages.select(self.curve_page);self.output_status.configure(text=self.result_context(), foreground="#596773")
        for key, value, unit in [("copper", result.copper_c[-1], "°C"), ("core", result.core_c[-1], "°C"), ("power", result.power_w[-1], "W")]:
            self.result_values[key].configure(text=f"{value:.1f} {unit}".replace(".", ","))
        reached = [(name, hit) for name, hit in zip(["Wicklung", "Kern"], result.limit_times_s) if hit is not None]
        note = (f"Grenze {result.settings.limit_c:g} °C: "+" · ".join(name+(" bereits zu Beginn erreicht" if hit == 0 else f" nach {hit/60:.3g} min erreicht") for name, hit in reached)
                if reached else f"Grenze {result.settings.limit_c:g} °C im berechneten Zeitraum bei Wicklung und Kern nicht erreicht.")
        if result.model_truncated:note += " Kurve bei 300 °C beendet; angeforderte Dauer nicht vollständig berechnet."
        self.limit_note.configure(text=note, foreground="#9a3e28" if reached or result.model_truncated else "#596773")
        self.details_note.configure(text="Letzte Berechnung: "+self.result_context()+". Diese Werte gehören zum angezeigten Diagramm.")
        self.report.configure(state="normal");self.report.delete("1.0", "end");self.report.insert("end", self.result_text(result));self.report.configure(state="disabled")
        self.csv_button.configure(state="normal");self.png_button.configure(state="normal");self.after_idle(self.canvas.fit_to_widget)

    @staticmethod
    def result_text(r):
        d = r.data
        text = [thermal.NOTICE, "", "ERGEBNIS IM BERECHNETEN ZEITRAUM",
                f"Nach {r.times_s[-1]/60:.5g} min: Wicklung {r.copper_c[-1]:.5g} °C · Kern {r.core_c[-1]:.5g} °C",
                f"Widerstand bei 20 °C: {d['resistance20_ohm']:.5g} Ω; beim Start: {r.resistance_ohm[0]:.5g} Ω; am Ende: {r.resistance_ohm[-1]:.5g} Ω",
                f"Kupferverluste I²R(T): zu Beginn {r.power_w[0]:.5g} W; am Ende {r.power_w[-1]:.5g} W"]
        for name, hit in zip(["Wicklung", "Kern"], r.limit_times_s):
            when = "bereits zu Beginn erreicht" if hit == 0 else f"nach {hit/60:.5g} min erreicht" if hit is not None else "im berechneten Zeitraum nicht erreicht"
            text.append(f"Grenze {r.settings.limit_c:g} °C – {name}: {when}.")
        text += ["", "RECHNERISCHER LANGZEITWERT"]
        if r.stable:
            if max(r.steady_c) > thermal.MODEL_MAX_C:
                text += [f"Formale Extrapolation: Wicklung {r.steady_c[0]:.5g} °C · Kern {r.steady_c[1]:.5g} °C.",
                         "Ausserhalb des Modellbereichs von 300 °C; kein belastbarer Wert für den Dauerbetrieb."]
            else:text.append(f"Gleichgewicht unter den eingegebenen Annahmen: Wicklung {r.steady_c[0]:.5g} °C · Kern {r.steady_c[1]:.5g} °C.")
        else:text.append("Unter diesen Annahmen ergibt sich kein stabiles Dauergleichgewicht.")
        if r.model_truncated:text.append("Die Kurve wurde bei 300 °C beendet; die angeforderte Betriebsdauer wurde nicht vollständig berechnet.")
        text += ["", "VERWENDETE SPULENDATEN UND ANNAHMEN",
                 f"Umgebung {r.settings.ambient_c:g} °C · Start {r.copper_c[0]:g} °C · angeforderte Dauer {r.settings.duration_min:g} min",
                 f"Strom {r.coil.current:g} A · Windungen {r.coil.turns:g} · Kupferdraht-Ø {r.coil.wire_d_mm:g} mm",
                 f"Massen: Kupfer {d['copper_mass_kg']*1000:.5g} g · Kern {d['core_mass_kg']*1000:.5g} g",
                 f"Wärmekapazitäten: Wicklung {d['copper_capacity_j_k']:.5g} J/K · Kern {d['core_capacity_j_k']:.5g} J/K",
                 f"Freie Flächen: Wicklung {d['copper_area_m2']*1e4:.5g} cm² · Kern {d['core_area_m2']*1e4:.5g} cm²",
                 f"Wärmeabgabe h: Wicklung/Kern {r.settings.h_copper:g}/{r.settings.h_core:g} W/(m² K)",
                 f"Wärmeübergang Wicklung–Kern: {r.settings.coupling_w_k:g} W/K",
                 "Berechnung mit konstantem Strom in Python; keine FEMM-Temperaturrechnung."]
        return "\n".join(text)

    def export_csv(self):
        if self.result is None:return
        path = filedialog.asksaveasfilename(title="Temperaturverlauf der letzten Berechnung speichern",
                initialfile="temperatur.csv", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            try:thermal.export_csv(self.result, Path(path), self.result_side)
            except OSError as error:messagebox.showerror("CSV nicht gespeichert", str(error))
