"""Deutsche Tkinter-Oberfläche. Start: python app.py"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import ctypes
import json
import math
import os
import queue
import sys
import time
from types import SimpleNamespace
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk, filedialog, messagebox

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    import model
    from plot_navigation import FieldNavigation
    from field_measurements import FieldMeasurements
    from thermal_ui import ThermalTab
    from force_map_ui import ForceMapTab
    from electrical_ui import ElectricalTab
    from impedance_ui import ImpedanceTab
    import electrical
    import impedance
    import force_map
except ImportError as e:
    messagebox.showerror("Abhängigkeiten fehlen", f"{e}\n\nIm Projektordner ausführen:\npython -m pip install -r requirements.txt")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent
CHOICES = {
    "kind": {"Massive Stahlkugel": "solid", "Stahl-Hohlkugel": "hollow", "Leichte Kugel mit PM": "pm"},
    "core_kind": model.CORE_TYPES,
    "pm_direction": {"+z / nach oben": 1, "−z / nach unten": -1},
}

class PlotToolbar(NavigationToolbar2Tk):
    toolitems = tuple(item for item in NavigationToolbar2Tk.toolitems
                     if item[3] not in {"configure_subplots", "save_figure"})

    def pan(self, *args):
        measurements=getattr(self,"field_measurements",None)
        if measurements is not None and measurements.enabled:measurements.set_enabled(False)
        super().pan(*args)

    def zoom(self, *args):
        measurements=getattr(self,"field_measurements",None)
        if measurements is not None and measurements.enabled:measurements.set_enabled(False)
        super().zoom(*args)


class PlotCanvas(FigureCanvasTkAgg):
    """Auch zuvor verborgene Reiter nach einer DPI-Änderung passend zeichnen."""
    def _update_device_pixel_ratio(self, event=None):
        super()._update_device_pixel_ratio(event)
        self.get_tk_widget().after_idle(self.fit_to_widget)

    def fit_to_widget(self):
        widget=self.get_tk_widget()
        if not widget.winfo_exists() or not widget.winfo_ismapped():
            return
        width,height=widget.winfo_width(),widget.winfo_height()
        if width>1 and height>1:
            # resize() ist auch in älteren TkAgg-Versionen vorhanden. Pack/Grid
            # senden nach der DPI-Umstellung nicht immer ein Configure-Ereignis.
            self.resize(SimpleNamespace(width=width,height=height))


class ScrollPane(ttk.Frame):
    def __init__(self, parent, fit_width=False):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=bar.set, xscrollcommand=horizontal.set)
        horizontal.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.body = ttk.Frame(self.canvas, padding=10)
        self.window = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window, width=e.width if fit_width else max(e.width, self.body.winfo_reqwidth())))

    def wheel(self, event):
        self.canvas.yview_scroll(-int(event.delta/120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1), "units")


class App:
    def __init__(self, root):
        self.root, self.config = root, model.Config()
        self.root.title("FEMM Schwebelabor · Zylinder- und Topfkerne")
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        self.ui_scale = max(1.0, float(root.tk.call("tk", "scaling"))/(96/72))
        root.geometry(f"{min(int(1450*self.ui_scale), int(w*.92))}x{min(int(960*self.ui_scale), int(h*.88))}")
        root.minsize(min(int(900*self.ui_scale), int(w*.8)), min(int(540*self.ui_scale), int(h*.75)))
        self.vars, self.widgets, self.labels, self.maps, self.rows = {}, {}, {}, {}, {}
        self.muted, self.preview_timer, self.busy, self.closing = False, None, False, False
        self.job, self.last_result, self.started = None, None, None
        self.preview_section,self.preview_parameter="setup",""
        self.events, self.results = queue.Queue(), {}
        self.worker = model.Worker(self.events)
        self.materials = model.material_names()
        self.soft_materials, self.pm_materials = model.material_names("soft"), model.material_names("pm")
        self.build()
        self.populate(self.config)
        self.refresh()
        root.bind_all("<MouseWheel>", self.wheel, add="+")
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.after(100, self.poll)

    def build(self):
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("TButton", padding=(10, 6))
        style.configure("TNotebook.Tab", padding=(12, 6))
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Hint.TLabel", foreground="#596773")
        style.configure("Force.TLabel",font=("Segoe UI",16,"bold"))
        self.table_font=tkfont.Font(self.root,family="Segoe UI",size=10)
        style.configure("Results.Treeview",font=self.table_font,
                        rowheight=self.table_font.metrics("linespace")+int(10*self.ui_scale))
        style.configure("Results.Treeview.Heading",font=("Segoe UI",10,"bold"))
        top = ttk.Frame(self.root, padding=(16, 12))
        top.pack(fill="x")
        ttk.Label(top, text="FEMM Schwebelabor", font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(top, text="Zwei koaxiale Elektromagnete · Längen in mm · Ströme in A", style="Hint.TLabel").pack(anchor="w", pady=(3,0))

        # Feste Bedienleiste bleibt auch auf kleineren Bildschirmen erreichbar.
        bottom = ttk.Frame(self.root, padding=(16, 8))
        bottom.pack(side="bottom", fill="x")
        self.status = ttk.Label(bottom, text="Vorschau bereit", wraplength=1000)
        self.status.pack(fill="x")
        bottom.bind("<Configure>", lambda e: self.status.configure(wraplength=max(200,e.width-32)))
        self.progress = ttk.Progressbar(bottom, mode="indeterminate")
        self.progress.pack(fill="x", pady=(5, 3))
        ttk.Label(bottom, text="Kräftegleichgewicht allein ist kein Stabilitäts- oder thermischer Nachweis.", style="Hint.TLabel").pack(anchor="w")
        actions = ttk.Frame(self.root, padding=(13, 5))
        actions.pack(side="bottom", fill="x")
        self.run_buttons = []
        for col, (text, kind) in enumerate([("Einzelfall berechnen", "single"), ("Stromsweep", "current"), ("Haltestrom-Sweep", "gap")]):
            b = ttk.Button(actions, text=text, command=lambda k=kind: self.start(k))
            b.grid(row=0, column=col, padx=3, sticky="ew")
            actions.columnconfigure(col, weight=1)
            self.run_buttons.append(b)
        self.cancel_button = ttk.Button(actions, text="Nach diesem Fall abbrechen", command=self.cancel, state="disabled")
        self.cancel_button.grid(row=0, column=3, padx=3, sticky="ew")
        actions.columnconfigure(3, weight=1)

        pane = ttk.Panedwindow(self.root, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=16, pady=(0, 5))
        left = ttk.Frame(pane, width=min(int(410*self.ui_scale),int(self.root.winfo_screenwidth()*.35)))
        right = ttk.Frame(pane)
        pane.add(left, weight=0)
        pane.add(right, weight=1)
        settings=ttk.LabelFrame(left,text="Einstellungen",padding=(8,6))
        settings.pack(fill="x",pady=(0,6))
        self.settings_buttons=[]
        for col,(label,command) in enumerate([("Speichern",self.save_settings),("Laden",self.load_settings),("Zurücksetzen",self.reset_settings)]):
            button=ttk.Button(settings,text=label,command=command)
            button.grid(row=0,column=col,sticky="ew",padx=2)
            settings.columnconfigure(col,weight=1)
            self.settings_buttons.append(button)
        self.settings_note=ttk.Label(settings,text="Standardwerte",style="Hint.TLabel")
        self.settings_note.grid(row=1,column=0,columnspan=3,sticky="w",pady=(4,0))
        settings.bind("<Configure>",lambda e:self.settings_note.configure(wraplength=max(150,e.width-20)))
        self.input_tabs = ttk.Notebook(left)
        self.input_tabs.pack(fill="both", expand=True)
        self.scrolls = []
        for title, maker in [("Aufbau", self.build_setup), ("Oben", lambda b: self.build_magnet(b, "upper")),
                             ("Unten", lambda b: self.build_magnet(b, "lower")), ("Objekt", self.build_object),
                             ("Sweeps", self.build_sweeps), ("Netz", self.build_mesh)]:
            scroll = ScrollPane(self.input_tabs,fit_width=title in {"Netz","Oben","Unten"})
            self.scrolls.append(scroll)
            self.input_tabs.add(scroll, text=title)
            maker(scroll.body)
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill="both", expand=True)
        self.geo_tab, self.field_tab, self.chart_tab, self.result_tab = (ttk.Frame(self.tabs) for _ in range(4))
        for tab, name in [(self.geo_tab, "Geometrie"), (self.field_tab,"Magnetfeld"), (self.chart_tab, "Diagramm"), (self.result_tab, "Ergebnisse")]:
            self.tabs.add(tab, text=name)
        # TkAgg übernimmt die Display-Skalierung selbst. Zusätzlicher DPI-Faktor
        # würde die Schrift unter Windows zweimal vergrössern.
        self.geo_figure, self.chart_figure = Figure(figsize=(6,6),dpi=100), Figure(figsize=(7,5),dpi=100)
        self.validation_note = ttk.Label(self.geo_tab, text="", padding=(8, 4), foreground="#9a3e28")
        self.validation_note.pack(fill="x")
        self.dimension_note=ttk.Label(self.geo_tab,text="",padding=(8,4),style="Hint.TLabel",justify="left")
        self.dimension_note.pack(fill="x")
        self.geo_tab.bind("<Configure>", lambda e: [label.configure(wraplength=max(180,e.width-20))
                                                   for label in [self.validation_note,self.dimension_note]])
        self.geo_canvas = self.figure_ui(self.geo_tab, self.geo_figure, "PNG speichern")
        self.chart_canvas = self.figure_ui(self.chart_tab, self.chart_figure, "PNG speichern")
        self.clear_chart()
        self.field_figure = Figure(figsize=(7,6),dpi=100)
        self.field_note = ttk.Label(self.field_tab,text="",style="Hint.TLabel",padding=(8,4))
        self.field_note.pack(fill="x")
        self.field_tab.bind("<Configure>",lambda e:self.field_note.configure(wraplength=max(180,e.width-20)))
        self.field_canvas = self.figure_ui(self.field_tab,self.field_figure,"PNG speichern")
        self.clear_field()

        self.result_tab.columnconfigure(0,weight=1)
        self.result_tab.rowconfigure(2,weight=2)
        self.result_tab.rowconfigure(3,weight=1)
        header=ttk.Frame(self.result_tab,padding=(8,8))
        header.grid(row=0,column=0,sticky="ew")
        self.force_values={}
        for col,(key,title) in enumerate([("magnetic","Magnetkraft Fz"),("weight","Gewichtskraft ↓"),("net","Nettokraft Fz − Gewicht")]):
            card=ttk.LabelFrame(header,text=title,padding=(10,8))
            card.grid(row=0,column=col,sticky="ew",padx=(0,6) if col<2 else 0)
            header.columnconfigure(col,weight=1,uniform="force")
            value=ttk.Label(card,text="— N",style="Force.TLabel",anchor="center")
            value.pack(fill="x")
            self.force_values[key]=value
        self.result_context=ttk.Label(header,text="Noch keine Berechnung.",style="Hint.TLabel",justify="left")
        self.result_context.grid(row=1,column=0,columnspan=3,sticky="ew",pady=(6,0))
        self.balance_note=ttk.Label(header,text="",justify="left")
        self.balance_note.grid(row=2,column=0,columnspan=3,sticky="ew",pady=(3,0))
        header.bind("<Configure>",lambda e:[v.configure(wraplength=max(180,e.width-20)) for v in [self.result_context,self.balance_note]])
        exports = ttk.Frame(self.result_tab, padding=(8,4))
        exports.grid(row=1,column=0,sticky="ew")
        self.field_button = ttk.Button(exports, text="FEMM öffnen", command=self.show_field)
        self.field_button.pack(side="left", padx=(0,5))
        self.field_export = ttk.Button(exports, text="Feldbild speichern", command=self.export_field)
        self.field_export.pack(side="left", padx=5)
        self.csv_button = ttk.Button(exports, text="CSV speichern", command=self.export_csv)
        self.csv_button.pack(side="left", padx=5)
        self.save_results_button = ttk.Button(exports, text="Ergebnisse speichern…", command=self.save_results, state="disabled")
        self.save_results_button.pack(side="left", padx=5)
        cols = ["nr", "phase", "iu", "il", "gu", "gl", "force", "net", "uu", "ul"]
        box = ttk.Frame(self.result_tab)
        box.grid(row=2,column=0,sticky="nsew",padx=8,pady=4)
        self.table = ttk.Treeview(box,columns=cols,show="headings",height=6,selectmode="browse",style="Results.Treeview")
        for key,text,width in zip(cols,["Nr.","Berechnung","I oben [A]","I unten [A]","g oben [mm]","g unten [mm]","Fz [N]","F netto [N]","|U oben| [V]","|U unten| [V]"],
                                  [40,125,85,85,95,95,105,105,100,100]):
            self.table.heading(key, text=text)
            self.table.column(key,width=int(width*self.ui_scale),minwidth=int(width*self.ui_scale),stretch=key=="phase",
                              anchor="w" if key=="phase" else "center" if key=="nr" else "e")
        self.table.tag_configure("alternate",background="#f1f5f8")
        self.table.tag_configure("voltage_limit",foreground="#a45523")
        sb = ttk.Scrollbar(box, command=self.table.yview)
        sx = ttk.Scrollbar(box, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=sb.set,xscrollcommand=sx.set)
        sx.pack(side="bottom",fill="x")
        self.table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.table.bind("<<TreeviewSelect>>", self.select_result)
        report_box = ttk.LabelFrame(self.result_tab,text="Details zum ausgewählten Fall",padding=(8,6))
        report_box.grid(row=3,column=0,sticky="nsew",padx=8,pady=(4,8))
        self.report = tk.Text(report_box,height=6,wrap="word",font=("Segoe UI",10),relief="flat",padx=6,pady=6)
        sb2 = ttk.Scrollbar(report_box, command=self.report.yview)
        self.report.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.report.pack(fill="both", expand=True)
        self.input_tabs.bind("<<NotebookTabChanged>>",self.input_section_changed)
        self.tabs.bind("<<NotebookTabChanged>>",self.plot_tab_changed)
        self.thermal_tab=ThermalTab(self.tabs,self.read_thermal_magnet,PlotCanvas,PlotToolbar,self.save_plot,ScrollPane)
        self.tabs.insert(self.result_tab,self.thermal_tab,text="Temperatur")
        self.force_map_tab=ForceMapTab(self.tabs,self,PlotCanvas,PlotToolbar)
        self.tabs.insert(self.chart_tab,self.force_map_tab,text="Kraftkennfeld")
        self.electrical_tab=ElectricalTab(self.tabs,self,PlotCanvas,PlotToolbar)
        self.tabs.insert(self.thermal_tab,self.electrical_tab,text="Elektrik")
        self.impedance_tab=ImpedanceTab(self.tabs,self,PlotCanvas,PlotToolbar,ScrollPane)
        self.tabs.insert(self.thermal_tab,self.impedance_tab,text="R / XL")
        # Eight tabs can exceed the pane width at large Windows display scales.
        self.tab_names={self.tabs.tab(tab,"text"):tab for tab in self.tabs.tabs()}
        self.tab_select_frame=ttk.Frame(right,padding=(4,2))
        ttk.Label(self.tab_select_frame,text="Reiter:").pack(side="left",padx=(0,6))
        self.tab_select_var=tk.StringVar(value="Geometrie")
        chooser=ttk.Combobox(self.tab_select_frame,textvariable=self.tab_select_var,
                             values=tuple(self.tab_names),state="readonly",width=18)
        chooser.pack(side="left",fill="x",expand=True)
        chooser.bind("<<ComboboxSelected>>",lambda e:self.tabs.select(self.tab_names[self.tab_select_var.get()]))
        self.tabs.bind("<Configure>",self.arrange_tab_selector,add="+")

    def arrange_tab_selector(self,event=None):
        font=tkfont.nametofont("TkDefaultFont")
        required=sum(font.measure(name)+int(32*self.ui_scale) for name in self.tab_names)
        if self.tabs.winfo_width()<required:
            if not self.tab_select_frame.winfo_manager():self.tab_select_frame.pack(fill="x",before=self.tabs)
        elif self.tab_select_frame.winfo_manager():self.tab_select_frame.pack_forget()

    def figure_ui(self, parent, fig, text):
        tools = ttk.Frame(parent)
        if parent is self.field_tab:
            # Die Bedienung erhält auch bei wenig Höhe vor dem Hinweistext Platz.
            tools.pack(side="bottom",fill="x",before=self.field_note)
        else:
            tools.pack(side="bottom",fill="x")
        canvas = PlotCanvas(fig, master=parent)
        navigation_tools=tools
        if parent is self.field_tab:
            # Eigene Zeile hält die Ansichts-Tasten auch bei schmalem Fenster sichtbar.
            view_tools=ttk.Frame(tools)
            view_tools.pack(fill="x",pady=(2,0))
            colour_tools=ttk.Frame(tools)
            colour_tools.pack(fill="x",pady=(3,3))
            ttk.Label(colour_tools,text="Farbskala:").pack(side="left",padx=(4,5))
            self.field_scale_var=tk.StringVar(value="Logarithmisch")
            scale_box=ttk.Combobox(colour_tools,textvariable=self.field_scale_var,
                                   values=["Logarithmisch","Linear"],state="readonly",width=15)
            scale_box.pack(side="left")
            scale_box.bind("<<ComboboxSelected>>",self.field_style_changed)
            self.field_whole_var=tk.BooleanVar(value=True)
            ttk.Checkbutton(colour_tools,text="Feld auch in Bauteilen",variable=self.field_whole_var,
                            command=self.field_style_changed).pack(side="left",padx=(10,4))
            navigation_tools=ttk.Frame(tools)
            navigation_tools.pack(fill="x")
        ttk.Button(navigation_tools, text=text, command=lambda: self.save_plot(fig)).pack(side="right", padx=4)
        toolbar=PlotToolbar(canvas, navigation_tools, pack_toolbar=False)
        toolbar.pack(side="left", fill="x")
        if parent is self.field_tab:
            self.field_navigation=FieldNavigation(canvas,toolbar)
            self.field_measure_var=tk.BooleanVar(value=False)
            self.field_measurements=FieldMeasurements(canvas,toolbar,self.field_measure_changed)
            toolbar.field_measurements=self.field_measurements
            self.field_navigation.pointer_tool=self.field_measurements
            view_buttons=[]
            for label,command in [("Mehr Breite",self.field_navigation.more_width),
                                  ("Weniger Breite",self.field_navigation.less_width),
                                  ("Grundansicht",self.field_navigation.restore_view)]:
                button=ttk.Button(view_tools,text=label,command=command)
                button.grid(row=0,column=len(view_buttons),sticky="w",padx=4)
                view_buttons.append(button)
            self.field_measure_button=ttk.Checkbutton(view_tools,text="Tesla messen",
                variable=self.field_measure_var,command=self.toggle_field_measure,state="disabled")
            self.field_measure_button.grid(row=0,column=len(view_buttons),sticky="w",padx=4)
            view_buttons.append(self.field_measure_button)
            self.field_clear_points=ttk.Button(view_tools,text="Messpunkte löschen",
                command=self.field_measurements.clear,state="disabled")
            self.field_clear_points.grid(row=0,column=len(view_buttons),sticky="w",padx=4)
            view_buttons.append(self.field_clear_points)
            def arrange_view_buttons(event):
                row,column,used=0,0,0
                for button in view_buttons:
                    width=button.winfo_reqwidth()+8
                    if column and used+width>event.width:
                        row,column,used=row+1,0,0
                    button.grid_configure(row=row,column=column)
                    used+=width
                    column+=1
            view_tools.bind("<Configure>",arrange_view_buttons)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return canvas

    def info(self, parent, text):
        label = ttk.Label(parent, text=text, wraplength=360, justify="left", style="Hint.TLabel")
        label.pack(fill="x", pady=(4, 8))
        parent.bind("<Configure>", lambda e: label.configure(wraplength=max(150,e.width-24)), add="+")
        return label

    def group(self, parent, title):
        group = ttk.LabelFrame(parent, text=title, padding=(10, 8))
        group.pack(fill="x", pady=(4,10))
        return group

    def field(self, parent, path, label, choices=None, optional=False, check=False,label_width=21,entry_width=18):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        self.rows[path] = row
        row.columnconfigure(1, weight=1)
        self.labels[path] = label
        if check:
            v = tk.BooleanVar()
            widget = ttk.Checkbutton(row, text=label, variable=v)
            widget.grid(row=0, column=0, columnspan=2, sticky="w")
        else:
            ttk.Label(row, text=label, width=label_width, anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 8))
            v = tk.StringVar()
            if isinstance(choices, dict):
                self.maps[path] = choices
                widget = ttk.Combobox(row, textvariable=v, values=list(choices), state="readonly", width=entry_width)
            elif choices:
                widget = ttk.Combobox(row, textvariable=v, values=choices, width=entry_width)
            else:
                widget = ttk.Entry(row, textvariable=v, width=entry_width)
            widget.grid(row=0, column=1, sticky="ew")
        self.vars[path], self.widgets[path] = v, widget
        v.trace_add("write", lambda *_: self.changed(path))
        widget.bind("<FocusIn>",lambda e,p=path:self.focus_parameter(p),add="+")
        return widget

    def build_setup(self, b):
        g = self.group(b, "Oberflächen-Luftspalte")
        self.field(g, "upper_gap", "Oben [mm]")
        self.field(g, "lower_gap", "Unten [mm]")
        self.info(g, "Abstand zwischen Kugeloberfläche und Polfläche.")
        g = self.group(b, "Berechnete Lage")
        self.distance_label = ttk.Label(g, text="", justify="left")
        self.distance_label.pack(anchor="w", pady=3)
        self.info(g, "Polabstand = Kugeldurchmesser + beide Luftspalte. Gleiche Luftspalte zentrieren die Kugel.")
        self.info(b, "z zeigt nach oben. z=0 liegt zwischen den Polflächen.")

    def build_magnet(self, b, side):
        self.field(b,side+".enabled","Spule und Kern aktiv",check=True)
        self.info(b,"Häkchen aus: gesamter Elektromagnet entfällt in Geometrie, FEMM und Temperaturrechnung.")
        g = self.group(b, "Kernform und Abmessungen")
        self.field(g,side+".core_kind","Kernform",CHOICES["core_kind"])
        for key,label in [("core_d","Kern-Ø [mm]"),("core_l","Kernlänge [mm]"),("material","Material")]:
            self.field(g, side+"."+key, label, self.soft_materials if key=="material" else None,entry_width=24 if key=="material" else 10)
        for key,label in [("pot_inner_d","Topf innen Ø [mm]"),("pot_outer_d","Topf aussen Ø [mm]"),("pot_back_h","Rückwand [mm]")]:
            self.field(g,side+"."+key,label,entry_width=10)
        if not hasattr(self,"core_notes"):self.core_notes={}
        self.core_notes[side]=self.info(g,"")
        g = self.group(b, "Wicklung")
        for key,label in [("coil_id","Innendurchmesser [mm]"),("coil_od","Aussendurchmesser [mm]"),
                          ("coil_h","Höhe [mm]"),("coil_offset","Axiale Position [mm]"),("turns","Windungszahl")]:
            self.field(g,side+"."+key,label,entry_width=10)
        self.info(g, "Position ab objektseitigem Pol; positiv vom Objekt weg.")
        self.field(g,side+".wire_d_mm","Draht-Ø Kupfer [mm]",optional=True,entry_width=10)
        self.field(g,side+".wire_od_mm","Draht-Ø mit Lack [mm]",optional=True,entry_width=10)
        self.info(g,"Kupfer-Ø ohne Lack eingeben. 1 mm ist ein Beispielwert. Mit Lack optional; leer = unbekannt.")
        g = self.group(b, "Ansteuerung")
        self.field(g,side+".current","Strom [A]",entry_width=10)
        self.field(g,side+".voltage_limit_v","Verfügbare U [V]",optional=True,entry_width=10)
        self.info(g,"Vorzeichen kehrt die Stromrichtung um. Beide Magnete sind unabhängig.")
        self.info(g,"U ist die tatsächlich verfügbare Spannung am Spulenkreis, nach Verstärkerverlusten. Leer = Grenze unbekannt. Überschreitungen werden angezeigt; der FEMM-Strom bleibt für den Vergleich unverändert.")
        g = self.group(b,"Elektrische Betriebswerte")
        self.field(g,side+".temperature_c","Wicklung [°C]",entry_width=10)
        self.field(g,side+".resistance20_ohm","Gemessenes R20 [Ω]",optional=True,entry_width=10)
        self.field(g,side+".lead_resistance_ohm","Leitungen [Ω]",entry_width=10)
        self.info(g,"R20 optional: gemessener Spulenwiderstand bei 20 °C ersetzt die Drahtschätzung. Leitungen als zusätzlicher Widerstand bei Betriebstemperatur. Temperatur hier als Annahme eintragen; der Temperaturreiter überschreibt sie nicht.")
        g = self.group(b,"Elektrische Schätzung")
        if not hasattr(self,"wire_notes"):self.wire_notes={}
        self.wire_notes[side]=self.info(g,"")
        self.info(g,"R und P aus mittlerer Drahtlänge geschätzt, ohne Anschlussdrähte. U gilt für stationären Gleichstrom. Erwärmung im Reiter Temperatur abschätzen.")
        self.info(g,"Magnetfeld: Windungszahl × Strom. Draht-Ø ändert weder Windungszahl noch Strom automatisch.")

    def build_object(self, b):
        self.field(b,"object.enabled","Objekt aktiv",check=True)
        self.info(b,"Häkchen aus: Kugel und Innenmagnet entfallen. Einzelfälle zeigen dann das Magnetfeld ohne Objekt. Der Referenz-Ø hält den Polabstand unverändert.")
        self.field(b, "object.kind", "Objekt", CHOICES["kind"])
        self.object_groups = {}
        g = self.group(b,"Kugel")
        self.field(g,"object.diameter","Durchmesser [mm]")
        self.field(g,"object.wall","Wandstärke [mm]")
        g = self.group(b,"Stahlmaterial")
        self.object_groups["steel"] = g
        self.field(g,"object.material","Material",self.soft_materials)
        self.field(g,"object.density","Dichte [kg/m³]")
        g = self.group(b,"Gesamtmasse")
        self.field(g,"object.measured_mass_g","Gemessene Masse [g]")
        self.info(g,"Bei Stahl optional: leer = Masse aus Geometrie und Dichte. PM-Kugel: Masse inklusive Magnet eingeben.")
        g = self.group(b,"Scheiben-Permanentmagnet")
        self.object_groups["pm"] = g
        for key,label in [("pm_d","Durchmesser [mm]"),("pm_h","Dicke [mm]"),("pm_z","Axiale Lage [mm]"),
                          ("pm_material","Material"),("pm_direction","Magnetisierung")]:
            self.field(g,"object."+key,label, CHOICES["pm_direction"] if key=="pm_direction" else self.pm_materials if key=="pm_material" else None)
        self.info(g,"Axiale Lage relativ zum Kugelmittelpunkt.")

    def build_sweeps(self, b):
        self.sweep_vars = {}
        for title, fields in [
            ("Stromsweep",[("current_start","Start [A]","0"),("current_end","Ende [A]","4"),("current_step","Schritt [A]","0.5")]),
            ("Haltestrom: Luftspalt",[("gap_start","Start [mm]","10"),("gap_end","Ende [mm]","20"),("gap_step","Schritt [mm]","5")]),
            ("Haltestrom: Suchbereich",[("search_start","Startstrom [A]","0"),("search_end","Endstrom [A]","6"),("scan_points","Grobscan-Punkte","9")])]:
            g = self.group(b,title)
            for key,label,default in fields:
                row=ttk.Frame(g);row.pack(fill="x",pady=4)
                row.columnconfigure(1,weight=1)
                ttk.Label(row,text=label,width=21).grid(row=0,column=0,sticky="w",padx=(0,8))
                v=tk.StringVar(value=default)
                ttk.Entry(row,textvariable=v,width=18).grid(row=0,column=1,sticky="ew")
                self.sweep_vars[key]=v
        self.info(b,"Unterer Strom bleibt wie im Reiter Unten. Haltestrom-Sweep: beide Luftspalte gleich, Kugel mittig. Dichterer Grobscan findet kleinere Lösungsbereiche.")

    def build_mesh(self,b):
        g=self.group(b,"FEMM-Netz einstellen")
        row=ttk.Frame(g);row.pack(fill="x",pady=4);row.columnconfigure(1,weight=1)
        ttk.Label(row,text="Netzprofil",width=17).grid(row=0,column=0,sticky="w",padx=(0,8))
        self.mesh_profile_var=tk.StringVar(value="Standard")
        self.mesh_profile_box=ttk.Combobox(row,textvariable=self.mesh_profile_var,
                                         values=list(model.MESH_PRESETS),state="readonly",width=14)
        self.mesh_profile_box.grid(row=0,column=1,sticky="ew")
        self.mesh_profile_box.bind("<<ComboboxSelected>>",self.choose_mesh)
        self.mesh_recommendation=self.info(g,"")
        for key,label in [("mesh_mm","Lokal [mm]"),("air_mesh_mm","Äussere Luft [mm]"),
                          ("arc_deg","Kreisbogen [°]"),("domain_factor","Luftbereich-Faktor")]:
            self.field(g,"numerics."+key,label,label_width=17,entry_width=14)
        self.info(g,"Kleinere mm- und Gradwerte = feineres Netz, längere Rechenzeit. Gilt für Einzelfälle und beide Sweeps. Eigene Werte sind möglich.")
        g=self.group(b,"Empfehlungen")
        for name,(local,air,angle,recommendation) in model.MESH_PRESETS.items():
            ttk.Label(g,text=f"{name} · lokal {local:g} mm",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(3,0))
            self.info(g,recommendation)
        self.info(g,"Ausgangswerte für den Standardaufbau. Kleine Luftspalte, dünne Schalen oder dünne Magnete brauchen gegebenenfalls ein noch feineres lokales Netz.")
        g=self.group(b,"Kraft und Kurvenknick prüfen")
        self.info(g,"Denselben Fall mit Standard und Fein vergleichen; bei Bedarf Sehr fein. Erst kleine Änderungen zwischen den Netzen sprechen für ein ausreichend feines Netz.")
        self.info(g,"Luftbereich separat prüfen: Faktor 4 auf 6 erhöhen, Netzwerte gleich lassen. Grösserer Faktor = weiter entfernter Rand, kein feineres Netz. Profile ändern diesen Faktor nicht.")
        self.info(g,"Lokal gilt an Kernen, Polflächen, Objekt und naher Luft. Hohlkugelschalen werden zusätzlich auf höchstens Wandstärke/3 verfeinert. Die homogenisierte Wicklung bleibt im Inneren mindestens bei 1 mm.")

        g=self.group(b,"Induktivität am Arbeitspunkt")
        self.field(g,"numerics.inductance_enabled","Induktivität berechnen",check=True)
        self.field(g,"numerics.inductance_step_percent","Stromänderung [%]",entry_width=10)
        self.field(g,"numerics.inductance_min_step_a","Mindestens [A]",entry_width=10)
        self.info(g,"L = ΔFlussverkettung / ΔStrom, mit zwei Testströmen je aktiver Spule und unveränderter Kugelposition. Andere Ströme bleiben fest. Bis zu vier zusätzliche FEMM-Lösungen je Fall. Für schnelle Kraftsuchen abschaltbar.")
        self.info(g,"Standard: ±max(1 % des Strombetrags, 0,01 A). Netz und Testschritt verkleinern und Werte vergleichen, bevor L für einen Regler verwendet wird.")

    def choose_mesh(self,event=None):
        if self.busy:return
        values=model.MESH_PRESETS.get(self.mesh_profile_var.get())
        if values:
            self.muted=True
            try:
                for key,value in zip(model.MESH_FIELDS,values):
                    self.vars["numerics."+key].set(str(value))
            finally:self.muted=False
        self.refresh(update_report=False)

    def wheel(self, event):
        try:
            widget = self.root.winfo_containing(event.x_root, event.y_root)
            while widget:
                if isinstance(widget, ScrollPane):
                    widget.wheel(event)
                    return
                widget = widget.master
        except tk.TclError:
            pass

    def changed(self, path):
        if self.muted:
            return
        if path.endswith(("enabled","core_kind")):
            c=deepcopy(self.config)
            for side in ["upper","lower","object"]:
                getattr(c,side).enabled=bool(self.vars[side+".enabled"].get())
            for side in ["upper","lower"]:
                getattr(c,side).core_kind=self.maps[side+".core_kind"].get(self.vars[side+".core_kind"].get(),"rod")
            self.update_states(c)
        if path.startswith(("upper.","lower.")) and hasattr(self,"thermal_tab"):
            self.thermal_tab.inputs_changed()
        if self.preview_timer:
            self.root.after_cancel(self.preview_timer)
        self.preview_timer = self.root.after(300, lambda: self.refresh(path))

    def input_section_changed(self, event=None):
        section=["setup","upper","lower","object","setup","setup"][self.input_tabs.index("current")]
        if section!=self.preview_section:
            self.preview_section,self.preview_parameter=section,""
            self.refresh(update_report=False)

    def focus_parameter(self, path):
        self.preview_parameter=path
        self.refresh(update_report=False)

    def plot_tab_changed(self, event=None):
        selected=self.tabs.select()
        if hasattr(self,"tab_select_var"):
            self.tab_select_var.set(self.tabs.tab(selected,"text"))
        for tab,canvas in [(self.geo_tab,self.geo_canvas),(self.field_tab,self.field_canvas),(self.chart_tab,self.chart_canvas),
                           (self.force_map_tab,self.force_map_tab.canvas),
                           (self.electrical_tab,self.electrical_tab.canvas),
                           (self.impedance_tab,self.impedance_tab.canvas),
                           (self.thermal_tab,self.thermal_tab.canvas)]:
            if selected==str(tab):
                self.root.after_idle(canvas.fit_to_widget)
                break

    def populate(self, c):
        self.muted = True
        try:
            for path, var in self.vars.items():
                obj = c
                for part in path.split("."):
                    obj = getattr(obj, part)
                if path in self.maps:
                    var.set(next(k for k, v in self.maps[path].items() if v == obj))
                elif isinstance(var, tk.BooleanVar):
                    var.set(obj)
                else:
                    var.set("" if obj is None else str(obj))
        finally:
            self.muted = False
        self.update_states(c)
        if hasattr(self,"thermal_tab"):
            self.thermal_tab.inputs_changed()

    def apply_settings(self,c,sweeps,note,temperature=None,force_map_settings=None,impedance_settings=None):
        self.config=deepcopy(c)
        self.populate(c)
        self.thermal_tab.apply_settings(temperature)
        self.force_map_tab.apply_settings(force_map_settings)
        self.impedance_tab.apply_settings(impedance_settings)
        for key,var in self.sweep_vars.items():var.set(str(sweeps[key]))
        self.preview_parameter=""
        self.refresh(update_report=False)
        self.settings_note.configure(text=note)
        self.tabs.select(self.geo_tab)

    def save_settings(self):
        if self.busy:return
        try:
            c=self.read()
            sweeps={k:float(v.get().replace(",",".")) for k,v in self.sweep_vars.items()}
            data=model.settings_payload(c,sweeps)
            data["temperature"]=self.thermal_tab.settings_payload()
            data["force_map"]=self.force_map_tab.settings_payload()
            data["impedance"]=self.impedance_tab.settings_payload()
            path=filedialog.asksaveasfilename(title="Aufbau-Einstellungen speichern",initialfile="aufbau.json",
                                            defaultextension=".json",filetypes=[("Schwebelabor-Einstellungen","*.json")])
            if path:
                model.save_json(path,data)
                self.settings_note.configure(text="Gespeichert: "+Path(path).name)
        except (OSError,ValueError,TypeError) as e:
            messagebox.showerror("Einstellungen nicht gespeichert",str(e))

    def load_settings(self):
        if self.busy:return
        path=filedialog.askopenfilename(title="Aufbau-Einstellungen laden",filetypes=[("Schwebelabor-Einstellungen","*.json")])
        if not path:return
        try:
            data=json.loads(Path(path).read_text(encoding="utf-8-sig"))
            if not isinstance(data,dict):raise ValueError("Ungültige Einstellungsdatei.")
            temperature=self.thermal_tab.parse_settings(data.pop("temperature")) if "temperature" in data else None
            force_map_settings=force_map.parse_settings(data.pop("force_map")) if "force_map" in data else None
            impedance_settings=impedance.parse_settings(data.pop("impedance")) if "impedance" in data else None
            c,sweeps=model.parse_settings(data)
            self.apply_settings(c,sweeps,"Geladen: "+Path(path).name,temperature,force_map_settings,impedance_settings)
        except (OSError,ValueError,TypeError) as e:
            messagebox.showerror("Einstellungen nicht geladen",str(e))

    def reset_settings(self):
        if self.busy:return
        self.apply_settings(model.Config(),model.DEFAULT_SWEEPS,"Standardwerte wiederhergestellt")

    def read(self):
        c = deepcopy(self.config)
        for side in ["upper","lower","object"]:
            getattr(c,side).enabled=bool(self.vars[side+".enabled"].get())
        for side in ["upper","lower"]:
            getattr(c,side).core_kind=self.maps[side+".core_kind"][self.vars[side+".core_kind"].get()]
        for path, var in self.vars.items():
            parts = path.split(".")
            target = getattr(c, parts[0]) if len(parts) == 2 else c
            key, value, default = parts[-1], var.get(), getattr(target, parts[-1])
            if len(parts)==2 and parts[0] in {"upper","lower","object"}:
                if not target.enabled and key not in {"enabled","diameter"}:continue
                if parts[0] in {"upper","lower"} and key in model.POT_KEYS and target.core_kind!="pot":continue
            if path in self.maps:
                parsed = self.maps[path][value]
            elif isinstance(var, tk.BooleanVar):
                parsed = bool(value)
            elif isinstance(default, str):
                parsed = str(value).strip()
            else:
                try:
                    parsed = None if str(value).strip() == "" and key in {"measured_mass_g","wire_d_mm","wire_od_mm","resistance20_ohm","voltage_limit_v"} else float(str(value).replace(",", "."))
                    if parsed is not None and not math.isfinite(parsed):
                        raise ValueError()
                except ValueError:
                    raise ValueError(f"{self.labels[path]}: gültige endliche Zahl eingeben.") from None
            setattr(target, key, parsed)
        return c

    def read_thermal_magnet(self,side):
        """Nur die gewählte Spule lesen; Temperaturrechnung braucht keinen gültigen FEMM-Fall."""
        if side not in {"upper","lower"}:raise ValueError("Ungültige Spulenauswahl.")
        magnet=deepcopy(getattr(self.config,side))
        if not bool(self.vars[side+".enabled"].get()):
            raise ValueError("Gewählte Spule ist deaktiviert. Im Reiter Oben/Unten zuerst aktivieren.")
        magnet.core_kind=self.maps[side+".core_kind"][self.vars[side+".core_kind"].get()]
        for key in magnet.__dataclass_fields__:
            path=side+"."+key
            variable=self.vars[path]
            if key in model.POT_KEYS and magnet.core_kind!="pot":continue
            if isinstance(variable,tk.BooleanVar):
                parsed=bool(variable.get())
            elif path in self.maps:
                parsed=self.maps[path][variable.get()]
            elif isinstance(getattr(magnet,key),str):
                parsed=variable.get().strip()
            else:
                value=variable.get().strip()
                try:
                    parsed=None if not value and key in {"wire_d_mm","wire_od_mm","resistance20_ohm","voltage_limit_v"} else float(value.replace(",","."))
                    if parsed is not None and not math.isfinite(parsed):raise ValueError()
                except ValueError:
                    raise ValueError(self.labels[path]+": gültige endliche Zahl eingeben.") from None
            setattr(magnet,key,parsed)
        return magnet

    def update_states(self, c):
        for path, widget in self.widgets.items():
            parts=path.split(".")
            inactive=(len(parts)==2 and parts[0] in {"upper","lower","object"} and
                      not getattr(c,parts[0]).enabled and parts[1] not in {"enabled","diameter"})
            disabled = inactive or self.busy or ((path.startswith("numerics.") or path.endswith(("wire_d_mm","wire_od_mm"))) and self.busy or
                        path.startswith("object.pm_") and c.object.kind != "pm" or
                        path == "object.wall" and c.object.kind != "hollow" or
                        path in {"object.material", "object.density"} and c.object.kind == "pm")
            widget.configure(state="disabled" if disabled else "readonly" if path in self.maps or path.endswith("material") else "normal")

        for side in ["upper","lower"]:
            m=getattr(c,side);pot=m.core_kind=="pot"
            for key in model.POT_KEYS:
                self.rows[side+"."+key].pack_forget()
                if pot:self.rows[side+"."+key].pack(fill="x",pady=4,before=self.core_notes[side])
            for key,label in [("core_d","Mittelpol-Ø [mm]" if pot else "Kern-Ø [mm]"),
                              ("core_l","Gesamthöhe [mm]" if pot else "Kernlänge [mm]")]:
                path=side+"."+key;self.labels[path]=label
                self.rows[path].grid_slaves(row=0,column=0)[0].configure(text=label)
            self.core_notes[side].configure(text=
                ("Öffnung zum Objekt. Gesamthöhe inklusive Rückwand. Wandstärke = (Topf aussen Ø − Topf innen Ø) / 2. Wicklung muss zwischen Mittelpol, Aussenwand und Rückwand Platz haben." if pot else
                 "Runder zylindrischer Kern ohne magnetischen Rückschluss.") +
                ("\n\n" + model.core_materials.note(m.material) if model.core_materials.note(m.material) else ""))
        profile=model.mesh_profile(c.numerics)
        self.mesh_profile_var.set(profile)
        self.mesh_recommendation.configure(text=model.MESH_PRESETS[profile][3] if profile in model.MESH_PRESETS else
                                           "Eigene Netzwerte: Genauigkeit durch Vergleich mit einem feineren Netz prüfen.")
        self.mesh_profile_box.configure(state="disabled" if self.busy else "readonly")

        self.rows["object.wall"].pack_forget()
        if c.object.kind == "hollow":
            self.rows["object.wall"].pack(fill="x",pady=4)
        for name,group in self.object_groups.items():
            group.pack_forget()
        # Repack existing groups in their existing input order.
        steel,pm=self.object_groups["steel"],self.object_groups["pm"]
        if c.object.kind != "pm":
            steel.pack(fill="x",pady=(4,10),before=self.rows["object.measured_mass_g"].master)
        else:
            pm.pack(fill="x",pady=(4,10))

    def update_wire_notes(self,c):
        for side,m in [("upper",c.upper),("lower",c.lower)]:
            try:
                text=model.wire_summary(m)
                errors,warnings=model.wire_issues(m)
                text+="".join("\n"+line for line in errors+warnings)
                self.wire_notes[side].configure(text=text,foreground="#9a3e28" if errors else "#596773")
            except (ValueError,TypeError):
                self.wire_notes[side].configure(text="Für Drahtwerte gültigen Kupfer-Ø und Wickelraum eingeben.",foreground="#9a3e28")

    def refresh(self, changed="",update_report=True):
        if self.preview_timer:
            self.root.after_cancel(self.preview_timer)
        self.preview_timer = None
        try:
            c, changes = model.normalize(self.read(), changed)
            self.config = c
            self.update_states(c)
            p = model.coordinates(c)
            self.distance_label.configure(text=f"Polflächenabstand H: {p['h']:.6g} mm\nKugelmittelpunkt z: {p['center']:.6g} mm")
            self.dimension_note.configure(text=model.geometry_info(c,self.preview_section))
            errors, warnings = model.validate(c)
            self.update_wire_notes(c)
            # Ungültige Geometrie zeigt den letzten gültigen Schnitt; Fehler sind sichtbar.
            try:
                if c.object.diameter > 0 and all(not m.enabled or (m.core_d > 0 and m.core_l > 0 and m.coil_od > m.coil_id > 0) for m in [c.upper,c.lower]):
                    model.geometry_figure(c,self.geo_figure,self.preview_section,self.preview_parameter)
                    if errors:
                        self.geo_figure.axes[0].set_title("Eingaben ungültig – Solver blockiert\n"+errors[0], fontsize=10)
                    self.geo_canvas.draw_idle()
            except (ValueError, StopIteration, ZeroDivisionError):
                pass
            self.valid = not errors
            self.force_map_tab.set_busy(self.busy,c,self.valid)
            note = "\n".join(["FEHLER: "+e for e in errors[:2]])
            self.validation_note.configure(text=note)
            if not self.busy:
                p = model.coordinates(c)
                self.status.configure(text=("Berechnung blockiert: "+errors[0]) if errors else "Reine Feldsimulation · Objekt deaktiviert" if not c.object.enabled else f"Vorschau bereit · Masse {model.mass(c)*1000:.5g} g · Gewicht {model.mass(c)*9.81:.6g} N · g oben {p['upper_gap']:.4g} mm")
                for index,b in enumerate(self.run_buttons):
                    allowed=self.valid and (index==0 or c.upper.enabled and c.object.enabled)
                    b.configure(state="normal" if allowed else "disabled")
            if not self.busy and update_report and self.last_result is None:
                self.text_report("\n".join(["Eingabeprüfung"]+["FEHLER: "+e for e in errors]+warnings))
            return c if not errors else None
        except (ValueError, KeyError, TypeError) as e:
            self.valid = False
            self.force_map_tab.set_busy(self.busy,self.config,False)
            for label in self.wire_notes.values():
                label.configure(text="Eingabe unvollständig oder ungültig – Schätzung nach Korrektur.",foreground="#9a3e28")
            self.validation_note.configure(text="FEHLER: "+str(e))
            if self.geo_figure.axes:
                self.geo_figure.axes[0].set_title("Eingabe ungültig – letzte darstellbare Geometrie", fontsize=10)
                self.geo_canvas.draw_idle()
            if not self.busy:
                self.status.configure(text=str(e))
                for b in self.run_buttons:
                    b.configure(state="disabled")
            return None

    def text_report(self, text):
        self.report.configure(state="normal")
        self.report.delete("1.0", "end")
        self.report.insert("end", text)
        self.report.configure(state="disabled")

    def start(self, kind):
        if self.busy:
            return
        c = self.refresh()
        if c is None:
            self.tabs.select(self.result_tab)
            return
        try:
            options = {}
            if kind == "force_map":
                options = self.force_map_tab.read_options(c)
            if kind in {"current", "gap"}:
                prefix = "current" if kind == "current" else "gap"
                for key in ["start", "end", "step"]:
                    options[key] = float(self.sweep_vars[prefix+"_"+key].get().replace(",", "."))
                options["fixed_lower"] = c.lower.current
                if kind == "gap":
                    for key in ["search_start", "search_end", "scan_points"]:
                        options[key] = float(self.sweep_vars[key].get().replace(",", "."))
                model.validate_options(kind, c, options)
            self.job = None
            self.last_result = None
            self.results.clear()
            self.electrical_tab.clear()
            self.clear_field()
            self.clear_result_summary()
            self.table.delete(*self.table.get_children())
            if kind == "force_map":
                self.force_map_tab.clear()
                self.tabs.select(self.force_map_tab)
            self.started = time.monotonic()
            self.set_busy(True)
            self.worker.submit(kind, c, options)
        except Exception as e:
            messagebox.showerror("Auftrag nicht gestartet", str(e))

    def set_busy(self, value):
        self.busy = value
        self.force_map_tab.set_busy(value,self.config,getattr(self,"valid",False))
        self.update_states(self.config)
        for index,b in enumerate(self.run_buttons):
            allowed=getattr(self,"valid",False) and (index==0 or self.config.upper.enabled and self.config.object.enabled)
            b.configure(state="normal" if allowed and not value else "disabled")
        for b in [self.field_button, self.field_export]:
            b.configure(state="disabled" if value else "normal")
        for b in self.settings_buttons:b.configure(state="disabled" if value else "normal")
        self.save_results_button.configure(state="normal" if not value and self.job and self.job.get("cases") else "disabled")
        self.cancel_button.configure(state="normal" if value else "disabled")
        if value:
            self.progress.start(12)
        else:
            self.progress.stop()

    def cancel(self):
        self.worker.cancel.set()
        self.status.configure(text="Abbruch angefordert; aktuelle FEMM-Einzelberechnung wird beendet, Ergebnisse bleiben erhalten.")

    def selected_result(self):
        selection = self.table.selection()
        return self.results.get(selection[0]) if selection else self.last_result

    def clear_field(self):
        self.field_measurements.set_field()
        self.field_figure.clear()
        ax=self.field_figure.add_subplot(111)
        ax.set_axis_off()
        ax.text(.5,.5,"Einzelfall berechnen, um Feldlinien\nim Aufbau zu sehen.",transform=ax.transAxes,
                ha="center",va="center",fontsize=11,color="#596773")
        self.field_note.configure(text="")
        self.field_navigation.reset()
        self.field_canvas.draw_idle()

    def clear_chart(self):
        self.chart_figure.clear()
        ax=self.chart_figure.add_subplot(111)
        ax.set_axis_off()
        ax.text(.5,.5,"Stromsweep oder Haltestrom-Sweep starten.\nDanach erscheinen hier die berechneten Kurven.",
                transform=ax.transAxes,ha="center",va="center",fontsize=11,color="#596773")
        self.chart_canvas.draw_idle()

    def clear_result_summary(self):
        for label in self.force_values.values():label.configure(text="— N",foreground="#596773")
        self.result_context.configure(text="Noch keine Berechnung.")
        self.balance_note.configure(text="")

    @staticmethod
    def number(value,signed=False):
        if value is None:return "—"
        return (f"{value:+.6g}" if signed else f"{value:.6g}").replace(".",",")

    def update_result_summary(self,r):
        n=self.number
        self.force_values["magnetic"].configure(text=n(r["magnetic_force_z_n"],True)+" N",foreground="#176b98")
        self.force_values["weight"].configure(text=n(r["weight_n"])+" N",foreground="#596773")
        net=r["net_force_n"];tolerance=r["config"]["numerics"]["equilibrium_tolerance_n"]
        colour="#176b98" if abs(net)<=tolerance else "#a45523"
        self.force_values["net"].configure(text=n(net,True)+" N",foreground=colour)
        c=model.Config.from_dict(r["config"]);p=model.coordinates(c)
        self.result_context.configure(text=f"Berechneter FEMM-Fall · I oben {n(r['upper_current_a'],True)} A · I unten {n(r['lower_current_a'],True)} A\n"
                                      f"Luftspalte {n(p['upper_gap'])} / {n(p['lower_gap'])} mm · Masse {n(r['mass_kg']*1000)} g · aktuelle Eingaben können abweichen")
        status=("Numerisches Kräftegleichgewicht innerhalb der Krafttoleranz." if abs(net)<=tolerance else
                "Kraftüberschuss nach oben." if net>0 else "Aufwärtskraft reicht nicht zum Ausgleich des Gewichts.")
        if not c.object.enabled:status="Objekt deaktiviert: reine Feldsimulation; Objektkräfte werden nicht ausgewertet."
        exceeded=[name for side,name in [("upper","oben"),("lower","unten")]
                  if model.result_electrical(r,side) and model.result_electrical(r,side)["within_voltage_limit"] is False]
        if exceeded:
            status+=" DC-Spannungsgrenze "+" / ".join(exceeded)+" überschritten: Strom am realen Aufbau nicht erreichbar."
            colour="#a45523"
        self.balance_note.configure(text=status,foreground=colour)

    def select_result(self, event=None):
        r = self.selected_result()
        if not r:
            return
        self.impedance_tab.reference_changed()
        self.update_result_summary(r)
        selection=self.table.selection()
        if selection:self.electrical_tab.select_case(selection[0])
        p = model.coordinates(model.Config.from_dict(r["config"]))
        if r.get("field_data"):
            try:
                self.render_field(r)
            except (OSError,ValueError) as e:
                self.clear_field()
                self.field_note.configure(text="Feldansicht nicht verfügbar: "+str(e))
        else:
            self.clear_field()
        text=["Vorzeichen: Fz und Nettokraft positiv nach oben; Gewichtskraft wirkt nach unten.",
              model.mesh_summary(model.Config.from_dict(r["config"]).numerics),
              f"Objektvolumen-Abweichung des Netzes: {self.number(r['volume_relative_error']*100)} %",
              "Kräftegleichgewicht allein belegt keine geregelte oder seitliche Stabilität und keine thermische Dauerbetriebsfähigkeit."]
        saved=model.Config.from_dict(r["config"])
        text += ["", "Elektrische Werte des berechneten Falls:"]
        for name,m in [("Oben",saved.upper),("Unten",saved.lower)]:
            text += [name+":",electrical.summary(model.result_electrical(r,"upper" if name=="Oben" else "lower"))]
        if self.job and self.job.get("summary"):
            text += ["", "Sweep-Auswertung:"]+[model.summary_text(row) for row in self.job["summary"]]
        text += ["", "Ergebnisse bleiben bis zum Schliessen temporär verfügbar. Mit Ergebnisse speichern… dauerhaft sichern."]+["Hinweis: "+w for w in r["warnings"] if w!=model.NOTICE]
        self.text_report("\n".join(text))

    def field_style(self):
        return dict(scale="log" if self.field_scale_var.get()=="Logarithmisch" else "linear",
                    whole_field=bool(self.field_whole_var.get()))

    @staticmethod
    def field_case_key(r):
        data=r.get("field_data",{})
        return (str(r.get("directory","")),str(data.get("nodes","")),str(data.get("elements","")))

    def toggle_field_measure(self):
        self.field_measurements.set_enabled(self.field_measure_var.get())

    def field_measure_changed(self,measurements):
        self.field_measure_var.set(measurements.enabled)
        # Der Callback wird erst nach dem Aufbau der Bedienelemente aufgerufen.
        if hasattr(self,"field_measure_button"):
            self.field_measure_button.configure(state="normal" if measurements.axes is not None else "disabled")
            self.field_clear_points.configure(state="normal" if measurements.points else "disabled")
        if measurements.enabled:self.field_navigation.drag=None

    def render_field(self,r,keep_view=False):
        nav=self.field_navigation
        limits=(nav.axes.get_xlim(),nav.axes.get_ylim()) if keep_view and nav.active() else None
        model.field_figure(r,self.field_figure,**self.field_style())
        ax=self.field_figure.axes[0]
        nav.reset(ax,ax.field_domain)
        if limits:
            nav.set_limits(*limits)
            nav.toolbar.push_current()
        self.field_measurements.set_field(ax,ax.field_sampler,self.field_case_key(r))
        p=model.coordinates(model.Config.from_dict(r["config"]))
        self.field_note.configure(text=f"Berechneter Fall: oben {r['upper_current_a']:+.5g} A · unten {r['lower_current_a']:+.5g} A · Luftspalte {p['upper_gap']:.4g} / {p['lower_gap']:.4g} mm\n"
                                  "Blau = schwach · Grün/Gelb = mittel · Rot = stark. "+ax.field_colour_note+".\n"
                                  "Mausrad: Zoom · Shift + Mausrad: Breite · Ziehen: Ansicht verschieben\n"
                                  "Tesla messen: Klick setzt/entfernt Punkte · Punkt ziehen: verschieben · ≈ Wert des FEMM-Netzelements")
        self.field_canvas.draw_idle()

    def field_style_changed(self,event=None):
        r=self.selected_result()
        if not r or not r.get("field_data"):return
        try:
            self.render_field(r,keep_view=True)
        except (OSError,ValueError) as e:
            self.field_note.configure(text="Feldansicht nicht verfügbar: "+str(e))

    def show_field(self):
        r = self.selected_result()
        if not r:
            messagebox.showinfo("Feldbild", "Zuerst einen FEMM-Fall berechnen.")
            return
        self.set_busy(True)
        self.started = time.monotonic()
        self.worker.submit("field", None, {"result": r})

    def export_field(self):
        r = self.selected_result()
        if not r:
            messagebox.showinfo("Feldbild", "Zuerst einen FEMM-Fall berechnen.")
            return
        files=[("Feld mit Geometrie PNG","*.png"),("Native FEMM-Ansicht BMP","*.bmp")] if r.get("field_data") else [("Native FEMM-Ansicht BMP","*.bmp")]
        path = filedialog.asksaveasfilename(defaultextension=".png" if r.get("field_data") else ".bmp", filetypes=files)
        if path:
            if Path(path).suffix.lower()==".png":
                try:
                    key=self.field_case_key(r)
                    if self.field_measurements.case_key==key:
                        self.field_measurements.hide_hover()
                        figure=self.field_figure
                    else:
                        figure=model.field_figure(r,**self.field_style())
                        self.field_measurements.draw_saved(figure.axes[0],key)
                    figure.savefig(path,dpi=180)
                except Exception as e:
                    messagebox.showerror("Feldbild speichern",str(e))
                return
            self.set_busy(True)
            self.started = time.monotonic()
            self.worker.submit("field", None, {"result": r, "destination": path})

    def save_plot(self, figure):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            try:
                if figure is self.field_figure:self.field_measurements.hide_hover()
                figure.savefig(path, dpi=180)
            except Exception as e:
                messagebox.showerror("PNG-Export", str(e))

    def export_csv(self):
        if not self.job:
            messagebox.showinfo("CSV-Export", "Zuerst eine Berechnung durchführen.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            try:
                model.export_job(self.job, path)
            except Exception as e:
                messagebox.showerror("CSV-Export", str(e))

    def save_results(self):
        if self.busy or not self.job or not self.job.get("cases"):
            return
        destination = filedialog.askdirectory(title="Ordner für Ergebnisse wählen")
        if not destination:
            return
        try:
            snapshot=deepcopy(self.job)
            snapshot["impedance_check"]=self.impedance_tab.payload_for_save()
            target = model.save_job(snapshot, destination)
            self.status.configure(text="Ergebnisse gespeichert: "+str(target))
        except (OSError, ValueError, TypeError) as error:
            messagebox.showerror("Ergebnisse nicht gespeichert", str(error))

    def select_electrical_result(self, index):
        if index in self.results and self.table.selection() != (index,):
            self.table.selection_set(index)
            self.table.see(index)

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "job":
                    self.job = data
                    self.electrical_tab.set_job(data)
                    self.impedance_tab.set_job(data)
                    if data["kind"] == "force_map": self.force_map_tab.set_job(data)
                elif kind == "progress":
                    self.phase = data
                elif kind == "case":
                    self.last_result = data
                    if self.job:
                        self.job["cases"].append(data)
                    index = str(len(self.results)+1)
                    self.results[index] = data
                    self.electrical_tab.add_case(index,data)
                    p = model.coordinates(model.Config.from_dict(data["config"]))
                    eu,el=model.result_electrical(data,"upper"),model.result_electrical(data,"lower")
                    exceeded=any(e and e['within_voltage_limit'] is False for e in [eu,el])
                    self.table.insert("", "end", iid=index, values=(index, data.get("phase", "FEMM"),
                        self.number(data['upper_current_a']),self.number(data['lower_current_a']),
                        self.number(p['upper_gap']),self.number(p['lower_gap']),
                        self.number(data['magnetic_force_z_n'],True),self.number(data['net_force_n'],True),
                        self.number(eu['voltage_dc_v']) if eu else "—",self.number(el['voltage_dc_v']) if el else "—"),
                        tags=(("alternate",) if int(index)%2==0 else ())+(("voltage_limit",) if exceeded else ()))
                    self.table.see(index)
                    if not self.table.selection():self.update_result_summary(data)
                elif kind == "summary":
                    if self.job:
                        self.job["summary"].append(data)
                        if self.job["kind"] == "force_map":
                            self.force_map_tab.set_job(self.job)
                        else:
                            model.sweep_figure(self.job, self.chart_figure)
                            self.chart_canvas.draw_idle()
                            self.tabs.select(self.chart_tab)
                elif kind == "done":
                    self.job = data
                    self.electrical_tab.set_job(data)
                    self.impedance_tab.set_job(data)
                    if data["kind"] == "force_map": self.force_map_tab.set_job(data)
                    self.set_busy(False)
                    self.status.configure(text=f"{data['status']} · {len(data['cases'])} FEMM-Fälle · {data['seconds']:.1f} s · zum Behalten Ergebnisse speichern…")
                    if data["kind"] in {"current", "gap"}:
                        model.sweep_figure(data, self.chart_figure)
                        self.chart_canvas.draw_idle()
                    self.select_result()
                    if data["kind"] == "single":
                        self.tabs.select(self.field_tab if self.last_result and self.last_result.get("field_data") else self.result_tab)
                    if data["status"].startswith("Fehler:"):
                        self.text_report(data["status"]+"\n\nAbgeschlossene Ergebnisse bleiben erhalten.\n"+self.report.get("1.0", "end"))
                elif kind == "field_done":
                    self.set_busy(False)
                    self.status.configure(text="Echte FEMM-Lösung geöffnet"+(f" · Bild gespeichert: {data}" if data else ""))
                elif kind == "error":
                    self.set_busy(False)
                    self.status.configure(text="Fehler: "+data)
                    self.text_report(data+"\n\nAbgeschlossene Ergebnisse sind bis zum Schliessen temporär verfügbar und können gespeichert werden.")
                    if not self.closing:
                        messagebox.showerror("FEMM-Auftrag", data)
        except queue.Empty:
            pass
        if self.busy and self.started:
            suffix = " · Abbruch nach diesem Fall" if self.worker.cancel.is_set() else ""
            self.status.configure(text=f"{getattr(self, 'phase', 'FEMM startet')} · vergangen {time.monotonic()-self.started:.1f} s"+suffix)
        if self.closing and not self.worker.thread.is_alive():
            self.root.destroy()
            return
        self.root.after(150, self.poll)

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.worker.shutdown()
        self.status.configure(text="Fenster wird nach der aktuellen Einzelberechnung geschlossen; temporäre Arbeitsdateien werden gelöscht.")


def main():
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
