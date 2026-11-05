"""Explicit frequency comparison; sinusoidal RMS and PWM averages stay separate."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
import electrical
import impedance
import model

SOURCES = {"Manuelle R-/L-Werte": "manual", "FEMM-Stromkurve": "femm"}
SIDES = {"Oben": "upper", "Unten": "lower"}
MODES = {"0 / +U (synchroner Freilauf)": "slow", "−U / +U (bipolare Brücke)": "bipolar"}
CHOICES = {"source": SOURCES, "side": SIDES, "pwm_mode": MODES}
LABELS = {
    "current_start_a": "Strom ab [A]", "current_end_a": "Strom bis [A]",
    "current_step_a": "Stromschritt [A]", "frequency_hz": "Frequenz [Hz]",
    "resistance20_ohm": "Drahtwiderstand R20 [Ω]", "temperature_c": "Wicklungstemperatur [°C]",
    "lead_resistance_ohm": "Leitungswiderstand [Ω]", "inductance_mh": "Induktivität L [mH]",
    "voltage_limit_v": "Verfügbarer Spannungsbetrag [V]", "current_limit_a": "Maximaler Spitzenstrom [A]",
    "delta_current_a": "Gewünschte Stromänderung [A]", "transition_ms": "Zeit dafür [ms]",
}


class ImpedanceTab(ttk.Frame):
    def __init__(self, parent, app, canvas_type, toolbar_type, scroll_type):
        super().__init__(parent)
        self.app, self.job, self.assessment, self.muted = app, None, None, True
        self.vars, self.entries = {}, {}
        actions = ttk.Frame(self, padding=(8, 4));actions.pack(fill="x")
        buttons = [ttk.Button(actions, text=label, command=command) for label,command in (
            ("Berechnen", self.compute), ("Standardwerte", self.reset), ("Prüfung speichern…", self.save))]
        def arrange(event=None):
            self.arrange_controls(actions,buttons)
        actions.bind("<Configure>",arrange)
        self.note=self.hint(self,"")
        self.pages=ttk.Notebook(self);self.pages.pack(fill="both",expand=True)
        self.settings_page, self.sine_page, self.pwm_page, self.chart_page=(ttk.Frame(self.pages) for _ in range(4))
        for page,label in ((self.settings_page,"Vorgaben"),(self.sine_page,"Sinus / XL"),
                           (self.pwm_page,"PWM"),(self.chart_page,"Kurven")):
            self.pages.add(page,text=label)
        self.scroll=scroll_type(self.settings_page,fit_width=True);self.scroll.pack(fill="both",expand=True)
        self.scroll.canvas.configure(width=1,height=1)
        body=self.scroll.body
        self.hint(body,"Die Standardwerte sind Beispiele: 0–10 A in 1-A-Schritten, 20 kHz, 4 Ω, 100 mH, 48 V. "
                  "Für die reale Spule R und L übernehmen oder messen.")
        group=ttk.LabelFrame(body,text="Quelle und Spule",padding=8);group.pack(fill="x",pady=4)
        for key,label in (("source","R-/L-Quelle"),("side","Gewählte Spule")):
            self.choice(group,key,label)
        for label,command in (("Drahtwiderstand aus Aufbau",self.import_design),
                              ("R/L aus gewähltem FEMM-Fall",self.import_case)):
            ttk.Button(group,text=label,command=command).pack(anchor="w",pady=3)
        self.hint(group,"FEMM-Stromkurve: gleiche Geometrie, Luftspalte, anderer Spulenstrom und Netzeinstellungen "
                  "wie im gewählten Ergebnis. Zwischen Punkte wird linear interpoliert; ausserhalb fehlen Werte.")
        self.group(body,"Strombereich und Frequenz",("current_start_a","current_end_a","current_step_a","frequency_hz"),
                   "Sinusansicht: Frequenz des Sinusstroms, Strom als Effektivwert. PWM-Ansicht: "
                   "Schaltfrequenz und Strom als Mittelwert. Beide Ansichten verwenden dieselben Zahlen getrennt.")
        self.group(body,"Manuelle Spulenwerte",("resistance20_ohm","temperature_c","lead_resistance_ohm","inductance_mh"),
                   "R(T) = R20·[1 + 0,00393·(T−20 °C)] + RLeitung. L bleibt bei manueller Eingabe konstant. "
                   "Bei FEMM-Stromkurve gelten die R-/L-Werte und Temperaturen der berechneten Fälle.")
        self.group(body,"Ansteuerung und Grenzen",("voltage_limit_v","current_limit_a","delta_current_a","transition_ms"),
                   "Spannungsbetrag am Spulenkreis nach Treiberverlusten. Sinus: Spitzenspannung prüfen. "
                   "PWM: mittlere Haltespannung, lokale Spannung für ±ΔI/Δt und tatsächlichen Spitzenstrom prüfen.")
        self.choice(body,"pwm_mode","Ideale PWM-Stufen")
        self.hint(body,"0/+U setzt synchronen Freilauf voraus; eine Diode hat einen zusätzlichen Spannungsabfall. "
                  "−U/+U benötigt eine bipolare Brücke. Bewegung, Kopplung und Kern-/Schaltverluste fehlen. "
                  "FEMM liefert magnetostatisches Ldiff; für hohe Frequenzen ist die reale Impedanz zu messen.")
        self.sine_table=self.table(self.sine_page, (
            ("i","Ieff [A]",90),("r","R [Ω]",90),("l","L [mH]",100),("xl","XL [Ω]",105),
            ("z","|Z| [Ω]",105),("ur","UR,eff [V]",120),("ul","UL,eff [V]",120),
            ("u","Ueff [V]",120),("peak","Uspitze [V]",125),("status","Grenzen",240)))
        self.hint(self.sine_page,"Sinusmodell: XL = 2πfL; |Z| = √(R² + XL²); Ueff = Ieff·|Z|. "
                  "Uspitze = √2·Ueff. Diese Spannung gilt für einen Sinusstrom, nicht für den PWM-Mittelstrom.")
        self.pwm_table=self.table(self.pwm_page, (
            ("i","Imittel [A]",110),("hold","UHalten [V]",120),("rise","U+ [V]",105),
            ("fall","U− [V]",105),("duty","Tastgrad [%]",130),("ripple","ΔI Spitze–Spitze [A]",185),
            ("peak","Ispitze [A]",120),("tau","τ = L/R [ms]",135),("power","P Kupfer [W]",135),
            ("status","Grenzen",300)))
        self.hint(self.pwm_page,"PWM: UHalten = R·Imittel; U± = R·Imittel ± L·ΔI/Δt (lokal am Strompunkt). "
                  "Die Frequenz beeinflusst die Welligkeit. τ gilt für das lokale RL-Modell. "
                  "Die Stromgrenze gilt für den Spitzenstrom inklusive Welligkeit.")
        tools=ttk.Frame(self.chart_page,padding=(8,4));tools.pack(fill="x")
        self.view=tk.StringVar(value="Sinus / XL")
        control=ttk.Combobox(tools,textvariable=self.view,values=("Sinus / XL","PWM","Blindwiderstand"),state="readonly",width=18)
        control.bind("<<ComboboxSelected>>",lambda e:self.render())
        png=ttk.Button(tools,text="PNG speichern",command=self.save_png)
        tools.bind("<Configure>",lambda e:self.arrange_controls(tools,[control,png]))
        self.figure=Figure(figsize=(8,5),dpi=100);self.canvas=canvas_type(self.figure,master=self.chart_page)
        self.toolbar_frame=ttk.Frame(self.chart_page);self.toolbar_frame.pack(side="bottom",fill="x")
        toolbar_type(self.canvas,self.toolbar_frame,pack_toolbar=True)
        self.canvas.get_tk_widget().configure(height=1,width=1)
        self.canvas.get_tk_widget().pack(fill="both",expand=True)
        self.canvas.mpl_connect("resize_event",lambda e:self.render())
        self.chart_page.bind("<Configure>",self.arrange_toolbar)
        self.pages.bind("<<NotebookTabChanged>>",lambda e:self.after_idle(self.canvas.fit_to_widget))
        for var in self.vars.values():var.trace_add("write",lambda *_:self.changed())
        self.apply_settings()
        self.pages.select(self.sine_page)

    @staticmethod
    def arrange_controls(frame,controls):
        width=frame.winfo_width();x=y=row_height=0
        for control in controls:
            w,h=control.winfo_reqwidth(),control.winfo_reqheight()
            if x and x+w>width:x=0;y+=row_height+4;row_height=0
            control.place(x=x,y=y,width=min(w,width),height=h)
            x+=w+6;row_height=max(row_height,h)
        frame.configure(height=y+row_height)

    def arrange_toolbar(self,event=None):
        small=self.chart_page.winfo_width()<650*self.app.ui_scale
        if small:self.toolbar_frame.pack_forget()
        elif not self.toolbar_frame.winfo_manager():
            self.toolbar_frame.pack(side="bottom",fill="x",before=self.canvas.get_tk_widget())

    @staticmethod
    def hint(parent,text):
        label=ttk.Label(parent,text=text,style="Hint.TLabel",wraplength=600,justify="left",padding=(8,4))
        label.pack(fill="x")
        parent.bind("<Configure>",lambda e:label.configure(wraplength=max(100,e.width-24)),add="+")
        return label

    def choice(self,parent,key,label):
        row=ttk.Frame(parent);row.pack(fill="x",pady=3)
        ttk.Label(row,text=label).pack(anchor="w")
        self.vars[key]=tk.StringVar()
        widget=ttk.Combobox(row,textvariable=self.vars[key],values=tuple(CHOICES[key]),state="readonly",width=28)
        widget.pack(fill="x");self.entries[key]=widget

    def group(self,parent,title,keys,hint):
        frame=ttk.LabelFrame(parent,text=title,padding=8);frame.pack(fill="x",pady=4)
        for key in keys:
            row=ttk.Frame(frame);row.pack(fill="x",pady=3)
            row.columnconfigure(0,weight=1)
            label=ttk.Label(row,text=LABELS[key],wraplength=300)
            label.grid(row=0,column=0,sticky="w",padx=(0,8))
            row.bind("<Configure>",lambda e,l=label:l.configure(wraplength=max(90,e.width-130*self.app.ui_scale)))
            self.vars[key]=tk.StringVar();self.entries[key]=ttk.Entry(row,textvariable=self.vars[key],width=12)
            self.entries[key].grid(row=0,column=1,sticky="e")
        self.hint(frame,hint)

    def table(self,page,columns):
        box=ttk.Frame(page,padding=6);box.pack(fill="both",expand=True)
        table=ttk.Treeview(box,columns=[k for k,_,_ in columns],show="headings",height=11,style="Results.Treeview")
        for key,title,width in columns:
            table.heading(key,text=title)
            table.column(key,width=int(width*self.app.ui_scale),minwidth=int(50*self.app.ui_scale),stretch=False,
                         anchor="w" if key=="status" else "e")
        sy=ttk.Scrollbar(box,command=table.yview);sx=ttk.Scrollbar(box,orient="horizontal",command=table.xview)
        table.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        sx.pack(side="bottom",fill="x");sy.pack(side="right",fill="y");table.pack(fill="both",expand=True)
        table.tag_configure("limit",foreground="#a45523")
        table.tag_configure("unknown",foreground="#596773")
        table.tag_configure("alternate",background="#f1f5f8")
        return table

    def settings_payload(self):
        data={}
        for key,var in self.vars.items():
            value=var.get()
            try:data[key]=CHOICES[key][value] if key in CHOICES else float(value.strip().replace(",","."))
            except (ValueError,KeyError):raise ValueError(f"R / XL: {LABELS.get(key,key)} ist ungültig.") from None
        return impedance.parse_settings(data)

    def apply_settings(self,data=None):
        data=impedance.parse_settings(data) if data is not None else asdict(impedance.Settings())
        self.muted=True
        try:
            for key,value in data.items():
                self.vars[key].set(next(label for label,code in CHOICES[key].items() if code==value) if key in CHOICES else f"{value:g}")
        finally:self.muted=False
        self.changed();self.compute()

    def reset(self):
        self.apply_settings()

    def changed(self):
        if self.muted:return
        self.assessment=None
        for table in (self.sine_table,self.pwm_table):table.delete(*table.get_children())
        self.note.configure(text="Vorgaben geändert · Berechnen drücken.")
        manual=self.vars["source"].get()==next(iter(SOURCES))
        for key in ("resistance20_ohm","temperature_c","lead_resistance_ohm","inductance_mh"):
            self.entries[key].configure(state="normal" if manual else "disabled")
        self.render()

    def set_job(self,job):
        self.job=job
        if self.vars["source"].get()=="FEMM-Stromkurve":self.changed()

    def evaluate(self):
        s=impedance.Settings(**self.settings_payload())
        anchor=self.app.selected_result() if s.source=="femm" else None
        return impedance.calculate(s,self.job or self.app.job,anchor)

    def compute(self):
        try:
            self.assessment=self.evaluate();self.fill_tables();self.render()
            s=self.assessment["settings"];unknown=sum(r["impedance_ohm"] is None for r in self.assessment["rows"])
            self.note.configure(text=f"{len(self.assessment['rows'])} Ströme · {s['frequency_hz']:g} Hz · "
                +(f"FEMM-Stromkurve · {unknown} Punkte ohne vollständige R-/L-Werte" if s["source"]=="femm" else "manuelle R-/L-Annahme"))
        except (ValueError,TypeError,KeyError) as error:
            self.assessment=None;messagebox.showerror("R / XL nicht berechnet",str(error))

    @staticmethod
    def number(value):return "—" if value is None else f"{value:.6g}"

    def fill_tables(self):
        for table in (self.sine_table,self.pwm_table):table.delete(*table.get_children())
        for index,row in enumerate(self.assessment["rows"]):
            def scaled(key,scale):return None if row[key] is None else row[key]*scale
            sine="R/L unbekannt" if row["sine_voltage_ok"] is None else "OK" if row["sine_voltage_ok"] else "Spannungsgrenze überschritten"
            if row["sine_current_ok"] is False:
                sine="Stromgrenze überschritten" if sine=="OK" else sine+" · Stromgrenze überschritten"
            values=(row["current_a"],row["resistance_ohm"],scaled("inductance_h",1000),row["reactance_ohm"],
                    row["impedance_ohm"],row["voltage_resistive_v"],row["voltage_inductive_sine_rms_v"],
                    row["voltage_sine_rms_v"],row["voltage_sine_peak_v"])
            tags=("alternate",) if index%2 else ()
            stag="unknown" if row["sine_voltage_ok"] is None else "limit" if row["sine_voltage_ok"] is False or row["sine_current_ok"] is False else ""
            self.sine_table.insert("","end",iid=str(index),values=tuple(self.number(v) for v in values)+(sine,),tags=tags+((stag,) if stag else ()))
            issues=[]
            for key,label in (("hold_ok","Halten"),("rise_ok","Erhöhen"),("fall_ok","Senken"),("pwm_current_ok","Spitzenstrom")):
                if row[key] is False:issues.append(label)
            status="Grenze: "+", ".join(issues) if issues else "R/L oder PWM unbekannt" if row["pwm_duty"] is None else "OK"
            pvalues=(row["current_a"],row["voltage_pwm_hold_v"],row["voltage_rise_v"],row["voltage_fall_v"],
                     scaled("pwm_duty",100),row["pwm_ripple_pp_a"],row["pwm_current_peak_a"],
                     scaled("time_constant_s",1000),row["pwm_power_coil_w"])
            self.pwm_table.insert("","end",iid=str(index),values=tuple(self.number(v) for v in pvalues)+(status,),
                                  tags=tags+(("limit",) if issues else ("unknown",) if row["pwm_duty"] is None else ()))

    def render(self):
        impedance.figure(self.assessment,self.view.get(),self.figure)
        # Keep the preview readable on a small, scaled display; exports retain 8×5 inches.
        width,height=self.figure.get_size_inches();factor=min(1,width/6.5,height/4)
        size=max(4.25,9*factor);ax=self.figure.axes[0]
        ax.tick_params(labelsize=size,length=2,pad=1)
        ax.xaxis.label.set_fontsize(size);ax.yaxis.label.set_fontsize(size)
        ax.title.set_fontsize(max(5,size*1.1))
        ax.xaxis.labelpad=3;ax.yaxis.labelpad=3;ax.title.set_position((.5,1.01))
        if ax.get_legend():
            for text in ax.get_legend().get_texts():text.set_fontsize(size*.9)
        for text in self.figure.texts:
            text.set_text("Sinus: Effektivwerte · PWM: Mittelwerte");text.set_fontsize(max(4.25,size*.8))
        if factor<=.65:
            ax.set_xlabel("Imittel [A]" if self.view.get()=="PWM" else "Ieff [A]")
            ax.set_ylabel({"PWM":"UPWM [V]","Sinus / XL":"Ueff [V]","Blindwiderstand":"R, XL, |Z| [Ω]"}[self.view.get()])
            handles,labels=ax.get_legend_handles_labels()
            if ax.get_legend():ax.get_legend().remove()
            labels=[{"UR,eff":"UR","UL,eff":"UL","Ugesamt,eff":"Ugesamt"}.get(label,label) for label in labels]
            if handles:self.figure.legend(handles,labels,ncol=2,loc="upper center",fontsize=max(4.25,size*.9))
            ax.set_title("")
        self.figure.subplots_adjust(left=.22 if factor>.65 else .28,right=.96,top=.84 if factor>.65 else .75,
                                    bottom=.23 if factor>.65 else .3)
        self.canvas.draw_idle()

    def reference_changed(self):
        if self.vars["source"].get()=="FEMM-Stromkurve":self.changed()

    def import_data(self,data,include_l):
        if not data or data.get("resistance20_ohm") is None:raise ValueError("Kein Drahtwiderstand vorhanden: Drahtdurchmesser oder gemessenes R20 eintragen.")
        if include_l and data.get("inductance_h") is None:raise ValueError("Keine berechnete Induktivität im gewählten Fall. L im Reiter Netz aktivieren und FEMM berechnen.")
        values={key:data[key] for key in ("resistance20_ohm","temperature_c","lead_resistance_ohm")}
        if include_l:values["inductance_mh"]=data["inductance_h"]*1000
        if data.get("voltage_limit_v") is not None:values["voltage_limit_v"]=data["voltage_limit_v"]
        self.muted=True
        try:
            self.vars["source"].set("Manuelle R-/L-Werte")
            for key,value in values.items():self.vars[key].set(f"{value:.12g}")
        finally:self.muted=False
        self.changed();self.compute()
        self.note.configure(text="R/L aus FEMM-Fall übernommen · für alle Ströme konstant angesetzt" if include_l else
                            "R aus Aufbau übernommen · L bleibt eine manuelle Annahme")

    def import_design(self):
        try:
            m=self.app.read_thermal_magnet(SIDES[self.vars["side"].get()])
            self.import_data(electrical.stationary(m,model.wire_data(m)),False)
        except (ValueError,TypeError,KeyError) as error:messagebox.showerror("R nicht übernommen",str(error))

    def import_case(self):
        try:
            row=self.app.selected_result()
            if not row:raise ValueError("Zuerst einen FEMM-Fall berechnen und im Reiter Ergebnisse oder Elektrik wählen.")
            self.import_data(model.result_electrical(row,SIDES[self.vars["side"].get()]),True)
        except (ValueError,TypeError,KeyError) as error:messagebox.showerror("R/L nicht übernommen",str(error))

    def payload_for_save(self):
        # A saved assessment always uses the currently visible settings and source.
        return deepcopy(self.evaluate())

    def save(self):
        try:
            assessment=self.payload_for_save()
            destination=filedialog.askdirectory(title="Ordner für R-/XL-/PWM-Prüfung wählen")
            if not destination:return
            parent=Path(destination)
            stage=Path(mkdtemp(prefix=".impedanz-",dir=parent))
            try:
                impedance.export(assessment,stage)
                stem="impedanz_"+datetime.now().strftime("%Y%m%d_%H%M%S");target=parent/stem;index=1
                while target.exists():target=parent/f"{stem}_{index}";index+=1
                stage.rename(target)
            except Exception:
                shutil.rmtree(stage,ignore_errors=True);raise
            self.note.configure(text="Prüfung gespeichert: "+str(target))
        except (OSError,ValueError,TypeError) as error:messagebox.showerror("Prüfung nicht gespeichert",str(error))

    def save_png(self):
        try:self.app.save_plot(impedance.figure(self.payload_for_save(),self.view.get()))
        except (ValueError,TypeError) as error:messagebox.showerror("PNG nicht gespeichert",str(error))
