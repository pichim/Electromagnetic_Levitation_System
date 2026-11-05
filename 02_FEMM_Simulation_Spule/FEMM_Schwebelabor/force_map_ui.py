"""Eigener Reiter für die statischen Kraftkennfelder."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
import force_map
from plot_navigation import FieldNavigation
from force_map_navigation import ForceMapNavigation, PRESETS


class ForceMapTab(ttk.Frame):
    def __init__(self, parent, app, canvas_type, toolbar_type):
        super().__init__(parent)
        self.app, self.job = app, None
        self.vars = {k: tk.StringVar(value=str(v)) for k, v in force_map.DEFAULTS.items()}
        self.vars["current_side"].set("Oben")
        self.inputs = []
        header = ttk.Frame(self, padding=(10, 6))
        header.pack(fill="x")
        ttk.Label(header, text="Kraftkennfeld Fz(I, s)", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.settings_open = tk.BooleanVar(value=True)
        ttk.Checkbutton(header, text="Bereiche einstellen", variable=self.settings_open,
                        command=self.toggle_settings).pack(side="right")
        settings = self.settings_frame = ttk.Frame(self, padding=(8, 0))
        settings.pack(fill="x", pady=(0, 3))
        for col, title in enumerate(("Achse", "Start", "Ende", "Schritt")):
            ttk.Label(settings, text=title).grid(row=0, column=col, sticky="w", padx=4)
            if col: settings.columnconfigure(col, weight=1)
        for row, (prefix, label) in enumerate((("current", "Strom I [A]"), ("gap", "Luftspalt s [mm]")), 1):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky="w", padx=4)
            for col, key in enumerate(("start", "end", "step"), 1):
                entry = ttk.Entry(settings, textvariable=self.vars[prefix+"_"+key], width=9)
                entry.grid(row=row, column=col, sticky="ew", padx=4, pady=3)
                self.inputs.append(entry)
        ttk.Label(settings, text="Variierte Spule").grid(row=3, column=0, sticky="w", padx=4)
        self.side_box = ttk.Combobox(settings, textvariable=self.vars["current_side"], values=("Oben", "Unten"), state="readonly", width=10)
        self.side_box.grid(row=3, column=1, sticky="ew", padx=4, pady=3)
        self.count = ttk.Label(settings, style="Hint.TLabel")
        self.count.grid(row=3, column=2, columnspan=2, sticky="w", padx=4)
        self.context = ttk.Label(settings, style="Hint.TLabel", justify="left")
        self.context.grid(row=4, column=0, columnspan=4, sticky="ew", padx=4, pady=(3, 0))
        settings.bind("<Configure>", lambda e: self.context.configure(wraplength=max(200, e.width-24)))
        actions = self.actions_frame = ttk.Frame(self, padding=(8, 3))
        actions.pack(fill="x")
        self.run_button = ttk.Button(actions, text="Kraftkennfeld berechnen", command=lambda: app.start("force_map"))
        self.run_button.pack(side="left", padx=(0, 6))
        self.export_button = ttk.Button(actions, text="Kennfeld exportieren…", command=self.export, state="disabled")
        self.export_button.pack(side="left")
        ttk.Button(actions, text="PNG speichern", command=lambda: app.save_plot(self.figure)).pack(side="right")
        views = ttk.Frame(self, padding=(8, 3))
        views.pack(fill="x")
        self.view_var = tk.StringVar(value=force_map.VIEWS[0])
        ttk.Label(views, text="Diagramm").pack(side="left", padx=(0, 8))
        box = ttk.Combobox(views, textvariable=self.view_var, values=force_map.VIEWS, state="readonly", width=22)
        box.pack(side="left")
        box.bind("<<ComboboxSelected>>", self.view_changed)
        self.slice_frame = ttk.Frame(self, padding=(8, 3))
        self.slice_frame.pack(fill="x")
        self.slice_label = ttk.Label(self.slice_frame, text="Luftspalt je Kurve")
        self.slice_label.pack(side="left", padx=(0, 8))
        self.slice_values = {}
        self.slice_var = tk.StringVar(value="Alle Luftspalte")
        self.slice_box = ttk.Combobox(self.slice_frame, textvariable=self.slice_var,
                                     values=("Alle Luftspalte",), state="disabled", width=22)
        self.slice_box.pack(side="left")
        self.slice_box.bind("<<ComboboxSelected>>", lambda e: self.render())
        self.three_d_frame = ttk.Frame(self, padding=(8, 3))
        ttk.Label(self.three_d_frame, text="Blickrichtung").pack(side="left", padx=(0, 8))
        self.preset_var = tk.StringVar(value="Perspektive")
        self.preset_box = ttk.Combobox(self.three_d_frame, textvariable=self.preset_var,
                                     values=tuple(PRESETS), state="readonly", width=19)
        self.preset_box.pack(side="left")
        self.preset_box.bind("<<ComboboxSelected>>", lambda e: self.nav3d.preset(self.preset_var.get()))
        for text, command in (("−", lambda: self.nav3d.zoom(-1)), ("+", lambda: self.nav3d.zoom(1)),
                              ("Ansicht zurücksetzen", self.restore_view)):
            ttk.Button(self.three_d_frame, text=text, command=command,
                       width=3 if text in ("−", "+") else 20).pack(side="left", padx=(6, 0))
        self.view_hint = ttk.Label(self, style="Hint.TLabel", padding=(8, 2))
        self.view_hint.pack(fill="x")
        self.note = ttk.Label(self, text="Start = Ende erzeugt genau einen festen Strom oder Luftspalt.", style="Hint.TLabel", padding=(8, 3))
        self.note.pack(fill="x")
        self.bind("<Configure>", self.resize_hints)
        self.figure = Figure(figsize=(7, 5), dpi=100)
        self.canvas = canvas_type(self.figure, master=self)
        tab = self
        class KennfeldToolbar(toolbar_type):
            def home(toolbar, *args):
                if hasattr(tab, "nav3d") and tab.nav3d.active(): tab.restore_view()
                else: super().home(*args)
        self.toolbar = KennfeldToolbar(self.canvas, self, pack_toolbar=False)
        self.toolbar.pack(side="bottom", fill="x")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.nav2d = FieldNavigation(self.canvas, self.toolbar)
        self.nav3d = ForceMapNavigation(self.canvas, self.toolbar)
        self.view_changed()
        for var in self.vars.values(): var.trace_add("write", lambda *args: self.update_count())
        self.update_count()

    def toggle_settings(self):
        if self.settings_open.get():
            self.settings_frame.pack(fill="x", pady=(0, 3), before=self.actions_frame)
        else:
            self.settings_frame.pack_forget()

    def resize_hints(self, event):
        if event.widget is not self: return
        for label in (self.note, self.view_hint):
            label.configure(wraplength=max(180, event.width-20))

    def restore_view(self):
        if self.nav3d.active():
            self.preset_var.set("Perspektive")
            self.nav3d.restore_view()
        else: self.nav2d.restore_view()

    def settings_payload(self):
        values = {k: float(v.get().replace(",", ".")) for k, v in self.vars.items() if k != "current_side"}
        values["current_side"] = "upper" if self.vars["current_side"].get() == "Oben" else "lower"
        return force_map.parse_settings(values)

    def apply_settings(self, values=None):
        values = force_map.parse_settings(values or force_map.DEFAULTS)
        for key, value in values.items():
            self.vars[key].set(("Oben" if value == "upper" else "Unten") if key == "current_side" else str(value))

    def read_options(self, config):
        options = self.settings_payload()
        force_map.validate_options(config, options)
        return options

    def update_count(self):
        self.set_busy(self.app.busy, self.app.config, getattr(self.app, "valid", False))
        try:
            currents, gaps = force_map.axes(self.settings_payload())
            self.count.configure(text=f"{len(currents)} × {len(gaps)} = {len(currents)*len(gaps)} FEMM-Fälle")
        except (ValueError, KeyError, OverflowError):
            self.count.configure(text="Bereiche prüfen")

    def set_busy(self, busy, config, valid):
        side = "upper" if self.vars["current_side"].get() == "Oben" else "lower"
        allowed = valid and config.object.enabled and getattr(config, side).enabled
        self.run_button.configure(state="normal" if allowed and not busy else "disabled")
        self.export_button.configure(state="normal" if self.job and self.job.get("cases") and not busy else "disabled")
        for entry in self.inputs: entry.configure(state="disabled" if busy else "normal")
        self.side_box.configure(state="disabled" if busy else "readonly")
        if config.upper.enabled and config.lower.enabled:
            self.context.configure(text=f"Fester Aufbau: Luftspalt oben + unten = {config.upper_gap+config.lower_gap:g} mm. Das Objekt bewegt sich; der andere Spulenstrom bleibt konstant.")
        else:
            self.context.configure(text="Luftspalt zur gewählten Spule wird variiert. Aufbau, Objekt, Material und Netz stammen aus den linken Eingabereitern.")

    def clear(self):
        self.job = None
        self.note.configure(text="Start = Ende erzeugt genau einen festen Strom oder Luftspalt.")
        self.view_changed()

    def set_job(self, job):
        first = self.job is None or self.job.get("directory") != job.get("directory")
        self.job = job
        if first: self.view_changed()
        else: self.render()
        completed = len(job.get("cases", []))
        currents, gaps = force_map.axes(job["options"])
        self.note.configure(text=f"{job.get('status', '')} · {completed} / {len(currents)*len(gaps)} Punkte berechnet · zum Behalten exportieren oder Ergebnisse speichern")

    def view_changed(self, event=None):
        view = self.view_var.get()
        curves = view in force_map.VIEWS[:2]
        self.slice_frame.pack_forget()
        self.three_d_frame.pack_forget()
        self.slice_values = {}
        if curves:
            over_current = view == force_map.VIEWS[0]
            all_label = "Alle Luftspalte" if over_current else "Alle Ströme"
            self.slice_label.configure(text="Luftspalt je Kurve" if over_current else "Strom je Kurve")
            values = [all_label]
            if self.job:
                currents, gaps = force_map.axes(self.job["options"])
                symbol, unit = ("s", "mm") if over_current else ("I", "A")
                self.slice_values = {f"{symbol} = {value:g} {unit}": float(value)
                                     for value in (gaps if over_current else currents)}
                values += list(self.slice_values)
            self.slice_box.configure(values=values, state="readonly" if self.job else "disabled")
            self.slice_var.set(all_label)
            self.slice_frame.pack(fill="x", before=self.view_hint)
            self.view_hint.configure(text=("Jede Farbe = ein fester Luftspalt. Auswahl zeigt alle Luftspalte oder eine einzelne Kurve."
                                           if over_current else
                                           "Jede Farbe = ein fester Strom. Auswahl zeigt alle Ströme oder eine einzelne Kurve."))
        elif view == force_map.VIEWS[3]:
            self.three_d_frame.pack(fill="x", before=self.view_hint)
            self.preset_var.set("Perspektive")
            self.view_hint.configure(text="Links ziehen: drehen · Rechts ziehen: verschieben · Mausrad: zoomen · Doppelklick: zurücksetzen")
        else:
            self.view_hint.configure(text="Farbe = Magnetkraft Fz [N] · Links ziehen: verschieben · Mausrad: zoomen · Doppelklick: zurücksetzen")
        self.render(preserve_view=False)

    def render(self, preserve_view=True):
        state = self.nav3d.snapshot() if preserve_view and self.view_var.get() == force_map.VIEWS[3] else None
        selected = self.slice_values.get(self.slice_var.get())
        force_map.figure(self.job, self.view_var.get(), self.figure, fixed=selected)
        self.nav2d.reset()
        self.nav3d.reset()
        axes = self.figure.axes[0]
        if self.job and self.job.get("cases"):
            if self.view_var.get() == force_map.VIEWS[3]:
                self.nav3d.reset(axes, state)
            else:
                self.nav2d.reset(axes)
        self.canvas.draw_idle()

    def export(self):
        if not self.job or not self.job.get("cases"): return
        destination = filedialog.askdirectory(title="Ordner für Kraftkennfeld-Export wählen")
        if not destination: return
        try:
            from model import save_job
            from copy import deepcopy
            snapshot=deepcopy(self.job)
            snapshot["impedance_check"]=self.app.impedance_tab.payload_for_save()
            target = save_job(snapshot, destination)
            self.note.configure(text="Kennfeld exportiert: "+str(target))
        except (OSError, ValueError) as error:
            messagebox.showerror("Kraftkennfeld-Export", str(error))
