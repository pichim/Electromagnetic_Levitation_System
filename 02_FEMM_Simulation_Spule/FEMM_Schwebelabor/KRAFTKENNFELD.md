# Kraftkennfeld Fz(I, s)

Diese Ergänzung berechnet ausschliesslich statische Magnetkräfte. Sie enthält keine Regelung, keine Reglerauslegung, keine Linearisierung und keinen Kraft-Fit.

## Bedienung

1. Links den gewünschten Aufbau einstellen: Spule, Kernform, Windungszahl, Material, Objekt, beide Ausgangsluftspalte und Netz. Für einen Magneten oben die untere Spule im Reiter **Unten** deaktivieren.
2. Rechts den neuen Reiter **Kraftkennfeld** öffnen.
3. Für **Strom I [A]** und **Luftspalt s [mm]** jeweils Start, Ende und Schrittweite eingeben. Dezimalkommas sind erlaubt. Das Ende wird auch dann mitgerechnet, wenn die Schrittweite nicht genau aufgeht.
4. **Variierte Spule** wählen: **Oben** oder **Unten**. Der Abstand ist der freie Oberflächen-Luftspalt zwischen Kugel und dem Pol dieser Spule, nicht der Abstand zum Kugelmittelpunkt. Der andere Spulenstrom bleibt auf seinem eingestellten Wert.
5. **Kraftkennfeld berechnen** starten. Für jede Kombination aus Strom und Luftspalt wird eine eigene FEMM-Lösung gerechnet. Die Anzahl der Fälle steht neben der Spulenauswahl.
6. Darstellung wählen: **Kraft über Strom**, **Kraft über Luftspalt**, **Farbkarte** oder **3D-Kennfeld**. In **Kraft über Strom** heisst die Kurvenauswahl **Luftspalt je Kurve**: **Alle Luftspalte** zeigt die Kurvenschar, **s = 15 mm** eine einzelne Abstandskurve. In **Kraft über Luftspalt** heisst sie **Strom je Kurve**: **Alle Ströme** zeigt die Kurvenschar, **I = 2 A** eine einzelne Stromkurve. Bei Farbkarte und 3D ist diese Auswahl ausgeblendet. Bis zu 24 gezeichnete Kurven haben eine vollständige Legende neben dem Diagramm; bei grösseren Kurvenscharen erklärt eine beschriftete Farbskala die Werte. Beim Auswählen einer Einzelkurve bleibt ihre Farbe gleich.
7. **Kennfeld exportieren…** schreibt Daten und alle vier Diagramme in einen eigenen Unterordner des gewählten Zielordners. **PNG speichern** speichert die aktuell angezeigte Ansicht mit der gewählten Kurve und Perspektive.

**Mehr Platz fürs Diagramm:** **Bereiche einstellen** ausblenden. Die Werte bleiben erhalten und werden weiter für Berechnungen verwendet.

### Navigation

| Aktion | 2D-Diagramme und Farbkarte | 3D-Kennfeld |
|---|---|---|
| Linke Maustaste ziehen | Ansicht verschieben | Um die Hochachse drehen / Ansicht neigen, ohne seitliches Kippen |
| Rechte oder mittlere Maustaste ziehen | Standardfunktion der Matplotlib-Werkzeugleiste | Ansicht verschieben; alternativ Shift + links ziehen |
| Mausrad | Zum Mauszeiger zoomen | Ansicht vergrössern / verkleinern |
| Doppelklick links / Home-Symbol | Startansicht | Startansicht inklusive Zoom und Verschiebung |
| Blickrichtung | – | Perspektive, Kraft / Strom, Kraft / Luftspalt oder Draufsicht |
| + / − neben Blickrichtung | – | Zoom ohne Mausrad |

Die direkten Mausgesten funktionieren bei ausgeschalteten Pan-/Zoom-Werkzeugen der unteren Leiste. **Ansicht zurücksetzen** und die Blickrichtungs- und Zoomknöpfe beenden einen aktiven Werkzeugmodus automatisch. Während weitere Kennfeldpunkte eintreffen, bleiben 3D-Drehung, Zoom und Verschiebung erhalten. Ein neues Kennfeld oder ein Wechsel der Diagrammart startet mit der Grundansicht.

**Nur ein Abstand, mehrere Ströme:** beim Luftspalt Start = Ende setzen. Beispiel: s = 30 mm, I = 0 bis 10 A mit Schritt 0,5 A.

**Nur ein Strom, mehrere Abstände:** beim Strom Start = Ende setzen. Beispiel: I = 5 A, s = 10 bis 50 mm mit Schritt 2 mm.

**Volles Kennfeld:** beide Bereiche variieren. Beispiel für einen einzelnen oberen Magneten: I = 0 bis 10 A mit Schritt 0,5 A, s = 10 bis 50 mm mit Schritt 2 mm. Das ergibt 21 × 21 = 441 FEMM-Fälle. Diese Beispiele sind Bereichsvorschläge, keine Aussage über die Kraft oder die Strombelastbarkeit eines realen Bauteils.

## Fester Aufbau bei zwei Magneten

Sind beide Magnete aktiv, bleibt ihr Polflächenabstand konstant:

`H = Kugeldurchmesser + Ausgangsluftspalt oben + Ausgangsluftspalt unten`.

Das Objekt bewegt sich zwischen den festen Polen. Wird bei Auswahl **Oben** der obere Luftspalt s grösser, verkleinert sich der untere entsprechend. Seine Grösse ist dann `Ausgangsluftspalt oben + Ausgangsluftspalt unten − s`. Bei Auswahl **Unten** gilt das umgekehrt. Unzulässige Abstände und Berührungen werden vor dem Start gemeldet. Der alte **Haltestrom-Sweep** verändert weiterhin beide Luftspalte gemeinsam; das ist eine andere Funktion.

Mit nur einem aktiven Magneten wird dessen Luftspalt variiert; der deaktivierte Magnet übt keine Kraft aus. Die internen z-Koordinaten folgen dabei der bestehenden Geometriereferenz. Für ein späteres Modell die exportierte Luftspaltachse benutzen.

## Kraft und Vorzeichen

Das Kennfeld enthält **magnetische Vertikalkraft Fz in Newton auf das gesamte Objekt**, positiv nach oben. Es wird weder der Betrag genommen noch die Gewichtskraft abgezogen. Eine untere Spule kann deshalb negative Kräfte liefern. Bei 0 A können die andere aktive Spule oder ein Permanentmagnet weiterhin eine Kraft erzeugen.

Die Kraftberechnung bleibt die bestehende FEMM-Auswertung: Objektgruppe 30, `mo_blockintegral(19)`, achsensymmetrisch. FEMM beschreibt Integral 19 als z-Komponente der Kraft über den gewichteten Spannungstensor: [offizielles Kugel-Beispiel](https://www.femm.info/doku/doku.php?id=coilgun). Das bestehende Modell unterstützt runde Stab- und offene Topfkerne; ein realer E-Kern wird dadurch nicht nachgebildet.

Gewicht und Nettokraft stehen in separaten CSV-Spalten. Für spätere Modellierung lassen sich damit Magnetkraft und Gravitation getrennt verwenden. Die magnetostatischen Werte zeigen keine Stromdynamik, Hysteresehistorie oder Bewegungseffekte. Vor einer Nutzung am realen Aufbau sollten ausgewählte Punkte mit feinerem Netz und Messungen verglichen werden.

## Exportdateien

Während der Berechnung bleiben die Daten im Arbeitsspeicher; benötigte FEMM-Arbeitsdateien liegen temporär. Dauerhaftes Speichern erfolgt erst mit **Kennfeld exportieren…** oder **Ergebnisse speichern…** nach freier Ordnerwahl. Dabei werden ursprüngliche FEMM-Fälle, elektrische Ergebnisse und alle Kennfeld-Exporte gemeinsam gespeichert. Eine spätere Änderung der Eingaben verändert das berechnete Kennfeld nicht. Die normalen Aufbau-Einstellungen **Speichern/Laden/Zurücksetzen** übernehmen auch die Kennfeldbereiche; alte Einstellungsdateien bleiben ladbar und erhalten die neuen Standardbereiche.

| Datei | Inhalt |
|---|---|
| `kraftkennfeld.csv` | Eine Zeile je angeforderter Kombination; Strom in A, Abstand in m und mm, Magnetkraft in N, beide tatsächlichen Ströme und Luftspalte, Gewicht, Nettokraft, Status und Verweis auf den Einzelresultatordner |
| `kraftmatrix_abstand_strom.csv` | Erste Spalte: Luftspalt in m. Kopfzeile: Ströme in A. Matrix: Fz in N. Zeilen = Abstände; Spalten = Ströme |
| `kraftmatrix_strom_abstand.csv` | Transponierte Matrix: erste Spalte Strom in A; Kopfzeile Luftspalte in m |
| `kraftkennfeld.json` | Beide SI-Achsen, Kraftmatrix, vollständige Geometrie, Materialien, Netz, Randbedingungen, Vorzeichen, Status und Solverinformationen |
| `kraftkennfeld.npz` | Für NumPy: `current_a`, `gap_m`, `magnetic_force_z_n`, `valid`, `metadata_json`. Matrix ebenfalls Abstand × Strom |
| `kraft_ueber_strom.png` | Kurvenschar für feste Luftspalte |
| `kraft_ueber_luftspalt.png` | Kurvenschar für feste Ströme |
| `kraftkennfeld_farbkarte.png` / `kraftkennfeld_3d.png` | Übersicht des Kennfeldes |
| `job.json`, `ergebnisse.csv`, `faelle/` | Vorhandenes vollständiges Jobformat und ursprüngliche FEMM-Einzelmodelle samt Parametern |

CSV: UTF-8 mit BOM, Semikolon als Trennzeichen und Dezimalpunkt. Kraftwerte werden mit voller Python-Zahlengenauigkeit geschrieben. Beim Import gegebenenfalls Semikolon und Dezimalpunkt auswählen. Für die spätere maschinelle Verarbeitung sind JSON oder NPZ eindeutig.

**Fehlende Punkte:** Bei Abbruch bleiben berechnete Punkte erhalten. Ein FEMM-Fehler stoppt den Auftrag und wird mit seiner Position dokumentiert. Nicht berechnete Kräfte sind in CSV leer, in JSON `null` und in NPZ `NaN`; die NPZ-Maske `valid` kennzeichnet die vorhandenen Kräfte. Fehlende Punkte werden nie als 0 N ausgegeben. Kurvenlinien und 3D-Flächen dienen nur der Ansicht; sie ergänzen keine Datenpunkte. Die 3D-Fläche wird nur für ein vollständiges zweidimensionales Raster gezeichnet.

Maximal 5000 Kombinationen pro Auftrag. Rechenzeit und Speicherbedarf steigen mit der Anzahl und der Netzfeinheit. Der Abbruchknopf beendet den Auftrag nach der laufenden FEMM-Einzelberechnung.

## Prüfung dieser Ergänzung

Die automatischen Prüfungen decken feste Magnetpositionen, beide Stromspulen, Einzelmagnete, SI-Einheiten, Matrixrichtung, Kraftvorzeichen, Einzelpunkte, ungleichmässigen letzten Schritt, Abbruch, Fehler und alle Darstellungen ab. Zusätzlich wurde die echte FEMM-Rechnung für einen oberen Einzelmagneten, zwei feste Magnete und einen unteren Einzelmagneten ausgeführt. Ein Kennfeldpunkt wurde unabhängig als Einzelfall nachgerechnet und ergab denselben Kraftwert. Diese Funktionsprüfung bestätigt keine bestimmte Genauigkeit für einen realen Aufbau.

## Elektrische Zusatzwerte

Das Kennfeld enthält zusätzlich U_DC, Spannungsreserve, differenzielle Induktivität und elektrische Zeitkonstante beider Spulen. Die bisherigen Kraftschlüssel bleiben erhalten. Die Metadaten verwenden Version 2; zusätzliche NPZ-Matrizen haben dieselbe Reihenfolge wie die Kraftmatrix. Einzelheiten und Annahmen stehen in [ELEKTRIK_UND_SPEICHERN.md](ELEKTRIK_UND_SPEICHERN.md).
