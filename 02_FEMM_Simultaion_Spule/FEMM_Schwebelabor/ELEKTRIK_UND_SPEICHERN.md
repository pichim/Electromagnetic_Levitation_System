# Spannung, Induktivität, Zeitkonstante und Speichern

## 1. Ergebnisse ausdrücklich speichern

Es wird kein Ordner `ergebnisse` im Programmordner angelegt. FEMM benötigt
Arbeitsdateien zum Lösen und zum erneuten Öffnen eines Falls. Diese liegen in
einem temporären Windows-Ordner und werden nach dem Schliessen der eigenen
FEMM-Instanz beim Beenden des Programms entfernt. Ein Betriebssystem- oder
Prozessabbruch kann temporäre Dateien zurücklassen.

- **Ergebnisse → Ergebnisse speichern…**: Zielordner wählen. Darin entsteht
  ein eindeutig benannter Unterordner mit `job.json`, `ergebnisse.csv`,
  Geometrie und Diagrammen sowie den ursprünglichen `.fem`-/`.ans`-Dateien und
  Parametern aller abgeschlossenen Fälle. Elektrische Kurven werden ebenfalls
  gespeichert, sofern Werte vorhanden sind.
- **Kraftkennfeld → Kennfeld exportieren…** speichert denselben vollständigen
  Datensatz und zusätzlich Kennfeld-CSV, Matrizen, JSON und NPZ.
- **CSV speichern**, **PNG speichern** und **Feldbild speichern** speichern
  nur den gewünschten Einzel-Export am frei gewählten Ort.
- **Einstellungen → Speichern** speichert Eingaben, keine Ergebnisse.

Ein neuer Auftrag ersetzt die angezeigten Ergebnisse. Benötigte Ergebnisse
daher vorher speichern. Ein abgebrochener Auftrag lässt sich mit seinen
abgeschlossenen Fällen speichern. Wiederholtes Speichern überschreibt keinen
vorhandenen Datensatz. Die gespeicherten JSON-Dateipfade beziehen sich auf den
Ordner der `job.json`, damit sich der gesamte Ergebnisordner verschieben lässt.
Die internen Strom-Testmodelle werden nicht als Messfälle mitgespeichert.

## 2. Spannung im realen Aufbau berücksichtigen

In **Oben** beziehungsweise **Unten** je aktiver Spule eintragen:

1. **Draht-Ø Kupfer**, Wicklungsabmessungen und Windungen, oder optional
   **Gemessenes R20**. R20 meint den Widerstand der Spule ohne Zuleitungen bei
   20 °C. Ein Messwert ersetzt die Widerstandsschätzung aus der Drahtgeometrie,
   auch im Temperaturreiter. Für die thermische Kupfermasse bleibt der
   Drahtdurchmesser erforderlich; Zuleitungsverluste werden nicht als
   Erwärmung der Wicklung angesetzt.
2. **Wicklung [°C]**: angenommene Temperatur während des Betriebs. Eine Messung
   oder Abschätzung im Temperaturreiter kann dafür verwendet werden. Der
   Temperaturreiter überschreibt diesen Wert nicht automatisch.
3. **Leitungen [Ω]**: zusätzlicher Serienwiderstand beider Zuleitungen und
   Kontakte bei Betriebstemperatur; Standard 0 Ω.
4. **Verfügbare U [V]**: tatsächlich verfügbare Ausgangsspannung für diesen
   Spulenkreis, nach Verlusten im Stromverstärker. Leer bedeutet unbekannt.
   Eine positive Zahl wird als symmetrische Betragsgrenze angenommen; eine
   asymmetrische Versorgung muss separat berücksichtigt werden.

Berechnung mit Kupferkoeffizient α = 0,00393/K:

```text
R_Spule(T) = R20 · [1 + α · (T − 20 °C)]
R = R_Spule(T) + R_Leitungen
U_DC = R · I
Spannungsreserve = U_verfügbar − |U_DC|
P_Spule = I² · R_Spule(T)
```

Die Ergebnistabelle zeigt die Spannungsbeträge für beide Spulen. Eine
Überschreitung färbt die Zeile und erscheint in den Details. Auch ein
mathematisch gefundenes Kräftegleichgewicht wird bei ungenügender Spannung
als stationär nicht erreichbar gekennzeichnet. **FEMM begrenzt den Strom
nicht automatisch**: Die theoretische Kraft bleibt sichtbar und wird von
der elektrischen Erreichbarkeit unterschieden. Die Stromgrenze des konkreten
Verstärkers ist weiterhin separat zu beachten.

## 3. Induktivität aus FEMM berechnen

Unter **Netz → Induktivität am Arbeitspunkt** ist die Berechnung standardmässig
aktiv. Jede aktive Spule erhält zwei zusätzliche magnetostatische Lösungen:

```text
ΔI = max(|I| · Stromänderung[%] / 100, Mindestens[A])
L_diff(I,z) ≈ [λ(I + ΔI,z) − λ(I − ΔI,z)] / (2 · ΔI)
```

Standard: 1 % und mindestens 0,01 A. Geometrie, Kugelposition und die anderen
Spulenströme bleiben gleich. λ ist die Flussverkettung des FEMM-Schaltkreises
aus `mo_getcircuitproperties`; sie enthält bereits die Windungszahl.
Ein weiterer Faktor N oder 2π wird nicht angebracht. Bei zwei aktiven Spulen
wird ausserdem die Gegeninduktivität aus der Flussänderung der anderen Spule
bestimmt und die lokale 2×2-Induktivitätsmatrix in `job.json` gespeichert.

Diese differenzielle Induktivität beschreibt kleine Stromänderungen am
gewählten Arbeitspunkt. Sie berücksichtigt die modellierte B-H-Kurve und
Sättigung. Auch bei I = 0, Permanentmagneten und einer bestromten zweiten Spule
funktioniert die Differenzbildung; das einfache Verhältnis λ/I wäre dort
mehrdeutig oder undefiniert.

Nach den Testlösungen werden das ursprüngliche FEMM-Modell und seine
ursprüngliche Lösung wieder geladen. Kraft, Feldansicht und exportierte
FEMM-Dateien gehören damit zum eingestellten Strom. Die Testlösungen erhöhen
die Fallzahl im Sweep nicht. Bei zwei aktiven Spulen entstehen bis zu vier
zusätzliche Lösungen pro Fall. Für umfangreiche schnelle Kraftsuchen lässt
sich die Induktivitätsberechnung abschalten; L und τ bleiben dann unbekannt.

Vor Nutzung im Regler: denselben Arbeitspunkt mit feinerem Netz und z. B.
halbiertem Testschritt vergleichen. Eine nichtpositive oder nicht endliche
Fluss-Strom-Ableitung wird als nicht auswertbar angezeigt, nicht durch einen
Absolutbetrag verdeckt. Fehler der Zusatzberechnung lassen die bereits
berechneten Kraft- und Spannungswerte bestehen und werden als Hinweis erfasst.

## 4. Zeitkonstante und Reglergrundlage

```text
τ = L_diff / [R_Spule(T) + R_Leitungen]
τ_nur_Spule = L_diff / R_Spule(T)
G_I/U(s) ≈ 1 / (L_diff · s + R)
```

Beispiel: L_diff = 100 mH und R = 2 Ω ergeben τ = 50 ms. Das ist eine lokale
elektrische RL-Zeitkonstante bei festem Objekt und konstantem anderen Strom.
Sie beschreibt weder die geschlossene Stromregelung im Kepco/ESCON noch die
gesamte Höhenregelung. Für eine Spannungsansteuerung muss zusätzlich zum
stationären Spannungsabfall Spannung für Stromänderungen verfügbar sein:

```text
u = R·i + dλ/dt
  ≈ R·i + L_diff·di/dt + M·dI_andere/dt + (∂λ/∂z)·dz/dt
```

Der letzte Term beschreibt die Bewegungsinduktion. Er wird hier nicht
berechnet. Angezeigt wird eine lokale Stromanstiegsreserve
`(U_verfügbar − |R·I|) / L_diff` für einen Anstieg des Strombetrags, wenn
das Objekt feststeht und der andere Strom konstant bleibt. Bei fehlender
Spannungsgrenze oder deren Überschreitung wird keine solche Reserve behauptet.

Die Induktivität stammt aus einem magnetostatischen Materialmodell.
Frequenzabhängige Wirbelströme im massiven Kern, Hysterese, PWM und die
Verstärkerdynamik sind nicht enthalten. Das Modell liefert einen Ausgangswert
für die Reglerplanung; eine Strom-Sprungmessung am realen Aufbau ergänzt ihn.

## 5. Anzeige und Export

**Elektrik → Messwerte** zeigt für jeden Fall beide Ströme, beide Luftspalte,
Spannungen, Induktivitäten, Zeitkonstanten und den Status der Spannungsgrenze.
Zeile wählen und **Elektrik → Details** öffnen für Widerstand, Temperatur,
Verluste, Testschritt und Reserve. Bei wenig Breite stehen die beiden
Spulendetails untereinander; die Details besitzen eigene Scrollbalken.
Die Auswahl ist mit dem Reiter Ergebnisse gekoppelt.

**Elektrik → Kurven** enthält U(I), L_diff(I) und τ(I) für die obere oder untere
Spule. Linien gruppieren einen festen Luftspalt und einen festen anderen
Spulenstrom. Die Spannungskurve zeigt zusätzlich die eingetragene U-Grenze.

CSV enthält die vollständigen elektrischen Werte pro Fall. Das Kennfeld-NPZ
enthält die bisherigen Kraftmatrizen und zusätzliche Matrizen, beispielsweise
`upper_voltage_dc_v`, `upper_inductance_h`, `upper_time_constant_s` und ihre
Pendants für die untere Spule. Reihenfolge: Luftspaltzeilen, Stromspalten.
Unbekannte Werte bleiben leer/null/NaN. Für `within_voltage_limit` gilt:
1 = eingehalten, 0 = überschritten, NaN = unbekannt. Kennfeld-Metadaten verwenden
Version 2; die bisherigen Kraftschlüssel behalten ihre Bedeutung.

Aufbau-Einstellungen verwenden Version 6. Versionen 1, 3 und 5 bleiben ladbar;
neue elektrische Annahmen erhalten die Standardwerte. Alte Ergebnisse werden
nicht nachträglich mit einer erfundenen Induktivität ergänzt.

## Quellen und Prüfung dieser Ausgabe

- FEMM: [Inductance Example](https://www.femm.info/wiki/InductanceExample)
- FEMM: [pyFEMM manual](https://www.femm.info/doku/lib/exe/fetch.php?media=upload%3Apyfemm%3Apyfemm-manual.pdf),
  `mo_getcircuitproperties` und `mi_modifycircprop`.
- FEMM: [ReadMe 4.2, incremental permeability](https://www.femm.info/wiki/ReadMe42),
  Flussverkettung, lokale Induktivitätsmatrix und Feld-Schaltungs-Modell.

Automatische Tests verwenden unabhängig bekannte Widerstands- und
Fluss-Strom-Funktionen für Einheiten, Temperatur, Vorzeichen, magnetische
Vorspannung, Kopplung, Nullstrom, Fehlersituationen, ursprüngliche
Arbeitspunktdateien, alte Einstellungen, manuelles Speichern und Export.
Diese Ausgabe wurde in einer Linux-Umgebung geprüft; ein echter Durchlauf
der neuen FEMM-COM-Zusatzlösungen unter Windows steht noch aus.
