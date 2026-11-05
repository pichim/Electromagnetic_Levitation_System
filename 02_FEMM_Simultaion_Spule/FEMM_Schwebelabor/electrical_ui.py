"""Electrical results belonging to immutable computed cases, not live inputs."""
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
import electrical
import model


class ElectricalTab(ttk.Frame):
    def __init__(self, parent, app, canvas_type, toolbar_type):
        super().__init__(parent)
        self.app, self.job, self.cases = app, None, {}
        self.note = ttk.Label(self, text="Einzelfall oder Sweep berechnen. Jeder Fall erhält eigene Spannungs-, L- und τ-Werte.",
                              style="Hint.TLabel", padding=(10, 6))
        self.note.pack(fill="x")
        self.bind("<Configure>", lambda e: self.note.configure(wraplength=max(200,e.width-24)))
        self.pages = ttk.Notebook(self)
        self.pages.pack(fill="both", expand=True)
        values, details_page, curves = (ttk.Frame(self.pages) for _ in range(3))
        self.pages.add(values, text="Messwerte")
        self.pages.add(details_page, text="Details")
        self.pages.add(curves, text="Kurven")
        values.rowconfigure(0, weight=1)
        values.columnconfigure(0, weight=1)
        box = ttk.Frame(values, padding=8)
        box.grid(row=0, column=0, sticky="nsew")
        columns = ("nr", "iu", "il", "gu", "gl", "uu", "ul", "lu", "ll", "tu", "tl", "status")
        self.table = ttk.Treeview(box, columns=columns, show="headings", height=7,
                                  selectmode="browse", style="Results.Treeview")
        headings = ("Nr.", "I oben [A]", "I unten [A]", "s oben [mm]", "s unten [mm]", "|U oben| [V]", "|U unten| [V]",
                    "L oben [mH]", "L unten [mH]", "τ oben [ms]", "τ unten [ms]", "DC-Spannung")
        for k, title in zip(columns, headings):
            self.table.heading(k, text=title)
            width=150 if k=="status" else 45 if k=="nr" else 110
            self.table.column(k, width=int(width*app.ui_scale),
                              minwidth=int(40*app.ui_scale), stretch=False, anchor="w" if k=="status" else "e")
        self.table.tag_configure("limit", foreground="#a45523")
        self.table.tag_configure("alternate", background="#f1f5f8")
        sy = ttk.Scrollbar(box, command=self.table.yview)
        sx = ttk.Scrollbar(box, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sx.pack(side="bottom", fill="x")
        sy.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)
        self.table.bind("<<TreeviewSelect>>", self.selected)
        details = ttk.Frame(details_page, padding=8)
        details.pack(fill="both",expand=True)
        self.details = {}
        detail_frames=[]
        for col, (side, name) in enumerate((("upper", "Obere Spule"), ("lower", "Untere Spule"))):
            frame = ttk.LabelFrame(details, text=name, padding=8)
            detail_frames.append(frame)
            frame.grid(row=0, column=col, sticky="nsew", padx=(0, 4) if col==0 else (4, 0))
            details.columnconfigure(col, weight=1, uniform="electrical")
            text = tk.Text(frame, wrap="word", width=1, height=10, relief="flat", font=("Segoe UI", 10), padx=4, pady=4)
            scroll = ttk.Scrollbar(frame, command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            text.pack(fill="both", expand=True)
            self.details[side] = text
        details.rowconfigure(0, weight=1)
        self.details_stacked=None
        def arrange_details(event):
            stacked=event.width < int(660*app.ui_scale)
            if stacked==self.details_stacked:return
            self.details_stacked=stacked
            for i,frame in enumerate(detail_frames):
                frame.grid_forget()
                frame.grid(row=i if stacked else 0,column=0 if stacked else i,sticky="nsew",padx=0 if stacked else 4,pady=4)
            details.rowconfigure(0,weight=1)
            details.rowconfigure(1,weight=1 if stacked else 0)
            details.columnconfigure(0,weight=1)
            details.columnconfigure(1,weight=0 if stacked else 1)
        details.bind("<Configure>",arrange_details)
        formula=ttk.Label(details_page, text="u = R·i + dλ/dt · bei fester Position und konstantem anderen Strom: u ≈ R·i + Ldiff·di/dt\n"
                  "τ = Ldiff / R gilt lokal für den Spulenkreis. Stromverstärker und mechanische Regelstrecke separat berücksichtigen.",
                  style="Hint.TLabel", justify="left", padding=(10, 6), wraplength=700)
        formula.pack(side="bottom",fill="x",before=details)
        details_page.bind("<Configure>",lambda e:formula.configure(wraplength=max(100,e.width-24)))
        hint=ttk.Label(values,text="Zeile wählen. Unter Details stehen Widerstand, Temperatur, Spannungsreserve und L/R-Zeitkonstante des Falls.",
                       style="Hint.TLabel",padding=(10,6),wraplength=700)
        hint.grid(row=1,column=0,sticky="ew")
        values.bind("<Configure>",lambda e:hint.configure(wraplength=max(100,e.width-24)))
        tools = ttk.Frame(curves, padding=8)
        tools.pack(fill="x")
        tools.columnconfigure(1, weight=1)
        self.side = tk.StringVar(value="Oben")
        self.view = tk.StringVar(value=next(iter(electrical.VIEWS)))
        for col,(var, choices, width) in enumerate(((self.side, ("Oben", "Unten"), 8), (self.view, tuple(electrical.VIEWS), 24))):
            control = ttk.Combobox(tools, textvariable=var, values=choices, state="readonly", width=width)
            control.grid(row=0,column=col,sticky="ew",padx=(0,8))
            control.bind("<<ComboboxSelected>>", lambda e: self.render())
        ttk.Button(tools, text="Ergebnisse speichern…", command=app.save_results).grid(row=0,column=2,sticky="e")
        self.figure = Figure(figsize=(8,5), dpi=100)
        self.canvas = canvas_type(self.figure, master=curves)
        toolbar = ttk.Frame(curves)
        toolbar.pack(side="bottom",fill="x")
        toolbar_type(self.canvas, toolbar, pack_toolbar=True)
        ttk.Button(toolbar,text="PNG speichern",command=lambda:app.save_plot(self.figure)).pack(side="right")
        self.canvas.get_tk_widget().pack(fill="both",expand=True)
        self.pages.bind("<<NotebookTabChanged>>", lambda e: self.canvas.fit_to_widget())
        self.clear()

    def clear(self):
        self.job, self.cases = None, {}
        self.table.delete(*self.table.get_children())
        self.table.configure(displaycolumns=self.table["columns"])
        for text in self.details.values():
            self.set_text(text, "Noch kein berechneter Fall ausgewählt.")
        self.render()

    @staticmethod
    def set_text(widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    def add_case(self, index, row):
        self.cases[index] = row
        if self.table.exists(index):
            return
        upper, lower = (model.result_electrical(row, s) for s in ("upper", "lower"))
        def value(data, key, scale=1):
            return "—" if data is None or data.get(key) is None else f"{data[key]*scale:.5g}"
        enabled = [e for e in (upper,lower) if e is not None]
        exceeded = any(e["within_voltage_limit"] is False for e in enabled)
        status = "Grenze überschritten" if exceeded else "Grenze unbekannt" if any(e["within_voltage_limit"] is None for e in enabled) else "innerhalb Grenze" if enabled else "deaktiviert"
        cfg = row["config"]
        self.table.insert("", "end", iid=index, values=(index, f"{row['upper_current_a']:.5g}",f"{row['lower_current_a']:.5g}",
            f"{cfg['upper_gap']:.5g}",f"{cfg['lower_gap']:.5g}",value(upper,"voltage_dc_v"),value(lower,"voltage_dc_v"),
            value(upper,"inductance_h",1000),value(lower,"inductance_h",1000),
            value(upper,"time_constant_s",1000),value(lower,"time_constant_s",1000),status),
            tags=(("alternate",) if int(index)%2==0 else ())+(("limit",) if exceeded else ()))
        if not self.table.selection():
            self.table.selection_set(index)

    def set_job(self, job):
        self.job = job
        cfg=job["config"]
        columns=["nr"]
        if cfg["upper"].get("enabled",True):columns += ["iu","gu","uu","lu","tu"]
        if cfg["lower"].get("enabled",True):columns += ["il","gl","ul","ll","tl"]
        columns.append("status")
        self.table.configure(displaycolumns=columns)
        for i,row in enumerate(job.get("cases", []),1):
            self.add_case(str(i),row)
        self.note.configure(text=f"{job.get('status','')} · {len(job.get('cases',[]))} berechnete Fälle · elektrische Werte gehören zum jeweiligen berechneten Aufbau")
        self.render()

    def select_case(self, index):
        if self.table.exists(index) and self.table.selection() != (index,):
            self.table.selection_set(index)
            self.table.see(index)

    def selected(self, event=None):
        selected = self.table.selection()
        if not selected:
            return
        index = selected[0]
        row = self.cases[index]
        for side, text in self.details.items():
            self.set_text(text, electrical.summary(model.result_electrical(row,side)))
        self.app.select_electrical_result(index)

    def render(self):
        electrical.figure(self.job,"upper" if self.side.get()=="Oben" else "lower",self.view.get(),self.figure)
        self.canvas.draw_idle()
