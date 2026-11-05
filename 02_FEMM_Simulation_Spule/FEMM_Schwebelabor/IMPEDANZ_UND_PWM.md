# Reiter R / XL

Der Reiter vergleicht den Spannungsbedarf eines idealen RL-Spulenkreises bei sinusförmigem Strom und bei PWM. Er funktioniert mit manuellen R-/L-Werten auch ohne FEMM. Die angehängte Programmversion mit Elektrik, Induktivität und manuellem Speichern bleibt die Grundlage.

## Standardwerte und Bedienung

| Eingabe | Standard | Bedeutung |
|---|---:|---|
| Strom ab / bis / Schritt | 0 / 10 / 1 A | Elf Tabellenzeilen; Bereich frei einstellbar |
| Frequenz | 20 000 Hz | In der Sinusansicht Sinusfrequenz; in PWM Schaltfrequenz |
| R20 | 4 Ω | Beispiel-Drahtwiderstand bei 20 °C |
| Wicklungstemperatur | 20 °C | Kupferkorrektur mit 0,00393/K |
| Leitungswiderstand | 0 Ω | Zusätzlicher Widerstand bei Betriebstemperatur |
| Induktivität | 100 mH | Beispiel, keine Messung des Aufbaus |
| Verfügbarer Spannungsbetrag | 48 V | Maximaler Betrag am Spulenkreis nach Treiberverlusten |
| Maximaler Spitzenstrom | 10 A | Einschliesslich PWM-Welligkeit bzw. Sinusspitze |
| Gewünschte Stromänderung / Zeit | 1 A / 10 ms | Lokale Steigung 100 A/s |
| PWM-Stufen | 0 / +U | Idealer synchroner Freilauf |

Unter **Vorgaben** Werte anpassen und **Berechnen** drücken. Dezimalkommas sind erlaubt. **Sinus / XL** und **PWM** zeigen getrennte Tabellen; **Kurven** bietet drei Diagramme. Änderungen leeren die bisherige Prüfung bis zur nächsten Berechnung. **Standardwerte** setzt nur diesen Reiter zurück.

Die Werte sind ein nachvollziehbares Beispiel. 20 kHz ist ein üblicher Ausgangspunkt für PWM; die geeignete Frequenz hängt vom Treiber, den Verlusten und der realen Spule ab. Mit den Beispielwerten gelten R = 4 Ω, L = 0,1 H und τ = 25 ms. Bei 10 A PWM-Mittelstrom beträgt die ideale Haltespannung 40 V; der Spitzenstrom liegt wegen der Welligkeit etwas über der eingestellten 10-A-Grenze.

## Sinus / XL: gewünschte Blindwiderstandsrechnung

Für eine ideale Reihenschaltung aus R und L bei einem sinusförmigen Strom:

- XL = 2πfL, in Ω, mit L in H und f in Hz.
- |Z| = √(R² + XL²). R und XL werden geometrisch addiert, weil ihre Spannungen um 90° versetzt sind.
- UR,eff = Ieff·R; UL,eff = Ieff·XL; Ueff = Ieff·|Z|.
- Uspitze = √2·Ueff und Ispitze = √2·Ieff.

Die Tabelle zeigt jeden Anteil und markiert überschrittene Spannungs- oder Stromgrenzen. Die Spannungsgrenze wird gegen **Uspitze** geprüft: Ein Treiber mit ±48 V kann ideal höchstens 48/√2 V Sinus-Effektivspannung erzeugen. Eine negative Halbwelle setzt einen geeigneten bidirektionalen Ausgang voraus. Das Sinusmodell enthält keine Treiberprüfung.

Bei 20 kHz und 100 mH ergibt sich XL ≈ 12 566 Ω. Ein Sinusstrom von 1 A effektiv benötigt im idealen Modell etwa 12 566 V effektiv. Das ist **keine Anforderung für einen mit 20-kHz-PWM geregelten Gleichstrom von 1 A**. Die PWM-Frequenz ist nicht die Frequenz einer sinusförmigen Änderung des gesamten Mittelstroms.

Bei konstantem R und L bleibt diese Sinus-Spannungskurve linear. Stromabhängiges L aus FEMM kann die Kurve verändern. Ein berechnetes XL ist eine Reaktanz und verursacht im idealen Modell keine Verlustwärme wie der Drahtwiderstand.

## PWM: Mittelstrom, Welligkeit und Stromänderung

Die PWM-Tabelle verwendet dieselben Stromzahlen als **Mittelwerte**. Für den periodisch eingeschwungenen idealen RL-Kreis gilt UHalten = R·Imittel. Die induktive Spannung mittelt sich über eine PWM-Periode zu null, wirkt aber während jeder Schaltphase.

Bei 0/+U ist der Tastgrad D = R·Imittel/U. Bei −U/+U ist D = (R·Imittel/U + 1)/2. Die Stromwelligkeit, der Spitzenstrom und der Effektivstrom werden aus der exakten periodischen RL-Lösung berechnet, nicht nur aus einer Dreiecksnäherung. Die Kupferleistung ist Ieff²·RSpule, ohne Leitungsverluste. Höhere PWM-Frequenz reduziert in diesem Modell die Welligkeit, erhöht aber nicht die mittlere Haltespannung.

U+ und U− zeigen den **lokalen** Spannungsbedarf für die eingestellte positive bzw. negative Stromsteigung: u = R·i ± L·ΔI/Δt. Sie beschreiben den jeweiligen Tabellenpunkt, keine vollständig simulierte Rampe. Bei 0/+U ist ein negativer Spannungsbedarf nicht erreichbar; bei −U/+U ist er bis −U erreichbar. Eine negative Rampe ab 0 A ist im synchronen unipolaren Modell entsprechend nicht möglich. Nicht erreichbare mittlere Ströme erhalten keine erfundene PWM-Welligkeit.

Bei L = 0 kann die Sinus-/Widerstandsrechnung erfolgen; die PWM-Welligkeit ist ohne Induktivität hier nicht auswertbar. Diese Prüfung ersetzt keine thermische Bewertung im Temperaturreiter.

## R und L aus dem Aufbau oder aus FEMM

- **Drahtwiderstand aus Aufbau** übernimmt R20, Temperatur, Leitungswiderstand und gegebenenfalls Spannung aus der gewählten Spule der aktuellen Eingaben. R20 folgt aus Drahtgeometrie oder einem eingetragenen Messwert. L bleibt eine manuelle Annahme.
- **R/L aus gewähltem FEMM-Fall** übernimmt zusätzlich die berechnete differenzielle Induktivität des im Reiter Ergebnisse oder Elektrik gewählten Falls. Diese Werte gelten anschliessend als konstant für alle Tabellenströme.
- **FEMM-Stromkurve** nutzt die bereits berechneten Fälle des aktuellen Auftrags. Der gewählte Ergebnisfall legt die Geometrie, die Luftspalte, den anderen Spulenstrom, die elektrischen Annahmen und die Netzeinstellungen fest. Nur der Strom der gewählten Spule darf zwischen Punkten abweichen. R und L werden zwischen passenden Punkten linear interpoliert. Ausserhalb des berechneten Strombereichs gibt es keine Extrapolation.

Für eine vollständige 0–10-A-FEMM-Tabelle zuerst den entsprechenden Stromsweep mit aktivierter Induktivitätsberechnung im Reiter Netz ausführen. Fehlende L-Werte bleiben unbekannt. Die Quellenangabe pro Punkt und die Referenzkonfiguration stehen im JSON-/CSV-Export.

FEMM liefert in dieser Ausgabe magnetostatisches Ldiff am Arbeitspunkt. Bei realem PWM können L und der wirksame Wechselstromwiderstand durch Frequenz, Sättigung, Wirbelströme und Skin-/Proximity-Effekte abweichen. Eine grosse Sinusschwingung wird mit lokalem Ldiff nur näherungsweise beschrieben. Zur abschliessenden Spulenauswahl die reale Impedanz bei Betriebsfrequenz, Strom und Temperatur messen sowie Treiberverluste, Kernverluste, Bewegung und Kopplung berücksichtigen.

## Speichern

Es entsteht kein automatischer Ergebnisse-Ordner. **Prüfung speichern…** fragt nach einem Zielordner und schreibt dort einen neuen, eindeutig benannten Unterordner mit `impedanz.json`, `impedanz.csv` und drei PNG-Diagrammen. CSV enthält SI-Einheiten im Spaltennamen; die Tabelle stellt L in mH und τ in ms dar. Die Prüfung lässt sich auch ohne einen FEMM-Auftrag speichern.

**Ergebnisse speichern…** und **Kennfeld exportieren…** nehmen zusätzlich die aktuelle Prüfung in den ausdrücklich gewählten Ergebnisexport auf. **PNG speichern** exportiert das gewählte Diagramm. Das Speichern der Aufbau-Einstellungen nimmt die Vorgaben des neuen Reiters mit auf; alte Einstellungsdateien ohne diesen Abschnitt verwenden die Standardwerte. Berechnung und Export verändern den gespeicherten FEMM-Fall nicht.

## Prüfung und Quellen

Die Softwaretests verwenden einen analytischen 3–4–5-Impedanzfall, unabhängige zeitliche RK4-Integration des PWM-RL-Kreises, Temperaturkorrektur und Fälle zur Interpolation ohne Extrapolation. Synthetische Testfälle sind keine echte FEMM-Validierung.

- Analog Devices, Impedanz aus R und X: <https://wiki.analog.com/resources/eval/user-guides/admx/eval-admx2001ebz>
- Texas Instruments, PWM-Stromsteuerung und Freilauf: <https://www.ti.com/document-viewer/lit/html/SSZT383/GUID-4216DB6F-57F6-4D58-BAA8-1567DCA72ADD>
