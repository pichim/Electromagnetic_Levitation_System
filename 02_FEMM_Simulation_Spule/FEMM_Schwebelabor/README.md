# FEMM Schwebelabor - einfache Windows-Anwendung

## Neu: Reiter R / XL

Die Spannungstabelle startet mit **0 bis 10 A in 1-A-Schritten** und editierbaren Beispielwerten **20 kHz, 4 Ω, 100 mH und 48 V**. Die Ansicht **Sinus / XL** berechnet Blindwiderstand, Gesamtimpedanz, Effektiv- und Spitzenspannung. Die Ansicht **PWM** berechnet mittlere Haltespannung, Tastgrad, Stromwelligkeit und lokale Spannungen für Stromänderungen. Beide Ansichten kennzeichnen ihre Stromdefinition und prüfen die eingestellten Grenzen. R/L können manuell oder aus FEMM übernommen werden. Eine berechnete FEMM-Stromkurve berücksichtigt stromabhängiges L ohne Extrapolation.

**Prüfung speichern…** fragt nach einem Zielordner für CSV, JSON und Diagramme. Anleitung und Grenzen des Modells: [IMPEDANZ_UND_PWM.md](IMPEDANZ_UND_PWM.md).

## Aktuelle Ergänzung: Elektrik und manuelles Speichern

- Ergebnisse werden nur über **Ergebnisse speichern…** beziehungsweise einen ausdrücklich gewählten Export dauerhaft geschrieben. Der Zielordner ist frei wählbar; im Programmordner entsteht kein `ergebnisse`-Ordner.
- Pro Fall: Spannungsbedarf bei eingetragener Temperatur, verfügbare Spannung und Reserve; optional gemessenes R20 und Leitungswiderstand.
- Neuer Reiter **Elektrik** mit Messwerten und Kurven für U(I), differenzielle Induktivität L(I) und elektrische Zeitkonstante τ(I).
- FEMM berechnet L mit kleinen positiven und negativen Stromänderungen am jeweiligen Arbeitspunkt. Die ursprünglichen Kraft- und Feldlösungen bleiben erhalten.
- Vollständige Anleitung, Formeln, Annahmen und Exportfelder: [ELEKTRIK_UND_SPEICHERN.md](ELEKTRIK_UND_SPEICHERN.md).
- Die neuen Berechnungs- und Speichertests nutzen analytische Referenzen. Die weiter unten dokumentierten echten FEMM-Messwerte stammen aus früheren Ausgaben; sie validieren die neue Induktivitätsberechnung nicht.


## Verbesserte Kennfeldansicht

- Beschriftete Kurvenauswahl: **Alle Luftspalte** oder **Alle Ströme**, abhängig vom Diagramm; einzelne Kurven mit Abstand oder Stromwert.
- Vollständige Legenden auch für 17 Stromkurven. Bei mehr als 24 Kurven ordnet eine Farbskala die Werte zu. Einzelkurven behalten ihre Farbe.
- 3D: links ziehen zum Drehen, rechts ziehen zum Verschieben, Mausrad zum Zoomen. Blickrichtungen, +/− und **Ansicht zurücksetzen** erleichtern die Orientierung.
- **Bereiche einstellen** ausblenden, um mehr Platz fürs Diagramm zu erhalten.

## Neu: Kraftkennfeld

Im neuen Reiter **Kraftkennfeld** lassen sich Strom und Luftspalt unabhängig variieren. Jeder Punkt ist eine FEMM-Einzelberechnung. Ansichten: **Kraft über Strom** bei festem Abstand, **Kraft über Luftspalt** bei festem Strom, Farbkarte und 3D-Kennfeld. Export: CSV, zwei Kraftmatrizen, JSON, NPZ und PNG. Bei zwei aktiven Magneten bleiben die Pole fest und das Objekt bewegt sich. Es wurden keine Regelungsfunktionen ergänzt.

Bedienung, Definition des Abstands, SI-Einheiten und Dateiformate: **[KRAFTKENNFELD.md](KRAFTKENNFELD.md)**.

## Start

1. Alle Dateien aus dem ZIP in einen beschreibbaren Ordner entpacken.
2. Python mit Tkinter installieren (Python 3.11 oder neuer).
3. [FEMM 4.2](https://www.femm.info/doku/doku.php?id=Download) separat installieren und einmal starten. pyFEMM installiert nur die Python-Schnittstelle.
4. Im entpackten Ordner eine PowerShell öffnen:

```powershell
python -m pip install -r requirements.txt
```

Danach **Schwebelabor.pyw doppelklicken**. Das Programm startet über `pythonw.exe` ohne CMD-Fenster. Alle ZIP-Dateien zuerst gemeinsam entpacken; nicht direkt im ZIP starten. `start.bat` ist als Kompatibilitätsstart weiterhin enthalten und übergibt sofort an `pythonw.exe`; dabei kann die Batch-Konsole kurz aufblitzen. Für den Start vollständig ohne Konsolenfenster **Schwebelabor.pyw** verwenden.

Ein vorhandener Desktop-Link muss ebenfalls auf **Schwebelabor.pyw** zeigen. Zum Neuerstellen: Rechtsklick auf die Datei → **Weitere Optionen anzeigen → Senden an → Desktop (Verknüpfung erstellen)**. Fehlerausgaben werden in `schwebelabor_start.log` im Programmordner gespeichert. Für eine Fehlersuche lässt sich das Programm weiterhin bewusst mit `python app.py` in einer PowerShell starten.
Bei mehreren Python-Versionen für Installation und Start denselben Interpreter verwenden.
Die Vorschau und die Temperaturberechnung funktionieren auch ohne FEMM und pyFEMM.

## Neue Feldfarben

**Neu: Tesla-Messpunkte**

- Im Reiter **Magnetfeld** **Tesla messen** aktivieren. Am Mauszeiger erscheint der Betrag **|B| in Tesla**, zusammen mit x und z in mm.
- Ein Klick in den Schnitt setzt einen bleibenden, nummerierten Messpunkt mit seinem Wert. Weitere Klicks setzen weitere Punkte.
- Einen vorhandenen Punkt oder seine Beschriftung erneut anklicken, um ihn zu entfernen. Gedrückt halten und ziehen verschiebt ihn; Position und Wert werden dabei aktualisiert.
- **Messpunkte löschen** entfernt alle Punkte des angezeigten Falls. Mit **Tesla messen** aus bleibt die Ansicht wieder mit der Maus verschiebbar. Die normalen Pan-/Zoom-Tasten schalten das Messwerkzeug automatisch aus; das Mausrad zoomt auch bei aktiviertem Messwerkzeug.
- Punkte bleiben während der laufenden Sitzung beim Zoomen, beim Farbwechsel und beim Wechsel zwischen berechneten Fällen erhalten. Jeder Fall besitzt seine eigenen Punkte. Sie werden im PNG der Ansicht mit exportiert; die vorübergehende Mausanzeige wird dabei ausgeblendet. Ein Neustart übernimmt diese Anmerkungen nicht.

**Was wird angezeigt?** Die Felddateien enthalten den originalen FEMM-Wert am Mittelpunkt jedes Netzelements. Der Messpunkt zeigt den Wert des Dreiecks, in dem er liegt; **≈** kennzeichnet diese räumliche Näherung. Feinere Netze lösen Ortsänderungen besser auf. Die Messwerte sind unabhängig von der logarithmischen/linearen Skala, deren Farbgrenzen und der geglätteten Farbdarstellung. In ausgeblendeten Bauteilen ist weiterhin ein Messwert verfügbar; ausserhalb des FEMM-Netzes wird kein Wert erfunden. Es wird keine neue FEMM-Rechnung gestartet. Angezeigt wird die Flussdichte, keine Kraft und keine Feldkomponente.

Die Beschriftung **schwach** steht mit Abstand unter der unteren Spitze der logarithmischen Farbskala. Der Hinweis unter dem Bild wird über zwei Zeilen verteilt, damit er auch in kleineren PNGs vollständig bleibt.

Diese Ausgabe wurde mit **73 Logiktests**, den originalen Werten sämtlicher Netzelemente zweier gespeicherter FEMM-Fälle sowie Bedienprüfungen in vier Fenstergrössen bei 100 %, 150 % und 225 % Skalierung geprüft. Setzen, schnelles erneutes Anklicken, Ziehen, Live-Anzeige, Pan-/Zoom-Wechsel, fallbezogene Punkte und PNG-Exporte funktionieren. Zusätzlich wurde die tatsächliche Tk-Mausereigniskette für Setzen, Ziehen und Entfernen geprüft. Magnetische Kraftrechnung und thermische Berechnung bleiben unverändert.

Im Reiter **Magnetfeld** zeigt die Farbkarte **Turbo** schwache Flussdichte dunkelblau/violett, mittlere grün/gelb und starke orange/rot. Die Standardeinstellung ist **Logarithmisch** über drei Grössenordnungen, mit Werten in Tesla an der Farbskala. Gleiche Farbschritte entsprechen gleichen Faktoren. **Linear** zeigt gleiche absolute Unterschiede.

**Feld auch in Bauteilen** ist standardmässig eingeschaltet: Die Farbskala gilt für Luft, Kern, Wicklung und Objekt; die Bauteile bleiben durch Konturen erkennbar. Häkchen aus zeigt wieder feste Bauteilfarben und Flussdichtefarben nur im Luftraum. Die Geometrievorschau behält ihre Bauteilfarben.

Die Farbgrenzen werden aus dem Feld in der Grundansicht bestimmt und bleiben beim Zoomen und Verschieben konstant. Verschiedene berechnete Fälle erhalten ihre eigene Skala; zum Vergleichen die Zahlen an der Farbskala beachten. Die logarithmische Untergrenze ist das Maximum geteilt durch 1000. Kleinere Werte einschliesslich 0 T sind in der dunkelsten Farbe zusammengefasst und an der Skala mit **≤** gekennzeichnet. Ein vollständiges Nullfeld verwendet eine lineare Anzeige mit 0 T.

Die Anzeige wird innerhalb jeder FEMM-Blockgruppe aus flächengewichteten Nachbarelementen geglättet. An Materialgrenzen wird nicht gemittelt. Die ursprünglichen FEMM-Daten und Kraftresultate bleiben unverändert. Feldlinien und Bauteilkonturen liegen weiterhin über der Farbdarstellung. PNG-Exporte verwenden die gewählte Darstellung; die native FEMM-Ansicht behält ihre eigenen Darstellungsfunktionen.

Die 64 vorhandenen Tests sowie Darstellungs- und Bedienprüfungen mit gespeicherten FEMM-Daten bestanden: log/linear, alle Materialien/Luft, Nullfeld, Beibehalten des Zooms und PNG-Export.

## Änderung dieser Ausgabe

In **Oben**, **Unten** und **Objekt** aktivieren oder deaktivieren Häkchen die jeweiligen Bauteile. Deaktivierte Elektromagnete fehlen vollständig samt Kern, Wicklung und Stromkreis. Das deaktivierte Objekt fehlt samt Innenmagnet; Kraft und Gewicht werden dann nicht ausgewertet. Die vorhandenen Eingabewerte bleiben zum erneuten Aktivieren erhalten.

Jede Spule kann zwischen **Zylinderkern (Stabkern)** und **Topfkern (offen)** wechseln. Eingabefelder, Vorschau, Masspfeile, FEMM-Geometrie und thermische Kernmasse folgen der gewählten Form. Die vorhandenen Temperatur- und Navigationsfunktionen bleiben erhalten.

## Aktivierung und Topfkerne

- **Spule und Kern aktiv** in Oben/Unten: Häkchen aus entfernt den ganzen Elektromagneten aus der Vorschau und dem neuen FEMM-Modell. Sein gespeicherter Strom ist dann unwirksam; Ergebnis und CSV zeigen 0 A. Inaktive Spulen sind auch für die Temperaturrechnung gesperrt.
- **Objekt aktiv**: Häkchen aus entfernt Kugel, Schale und gegebenenfalls Innenmagnet. Einzelfälle liefern das Magnetfeld ohne Objekt. Kraftanzeigen sind 0 und mit „reine Feldsimulation“ gekennzeichnet. Strom- und Haltestrom-Sweeps benötigen die obere Spule und ein aktives Objekt und werden andernfalls gesperrt.
- Der Polabstand bleibt beim Deaktivieren unverändert. Kugel-Referenzdurchmesser und beide nominalen Luftspalte bestimmen weiterhin die Positionen. Der Referenzdurchmesser bleibt deshalb auch bei deaktiviertem Objekt editierbar.
- **Kernform** in jedem Spulenreiter unabhängig auswählen. Der runde Stabkern verwendet Kern-Ø und Kernlänge. Beim Topfkern sind diese Felder als **Mittelpol-Ø** und **Gesamthöhe** beschriftet; zusätzlich erscheinen **Topf innen Ø**, **Topf aussen Ø** und **Rückwand**.
- Der Topf ist objektseitig offen. Mittelpol und äussere Wand verbinden sich über die Rückwand. Die Wicklung sitzt dazwischen. Es wird eine offene Topfhälfte rotationssymmetrisch ohne Bohrungen oder Wicklungsschlitze gerechnet; ein geschlossenes Paar aus zwei Topfhälften ist nicht enthalten.
- Mittelpol-Ø ≤ Spulen-Innen-Ø < Spulen-Aussen-Ø ≤ Topf-Innen-Ø < Topf-Aussen-Ø. Wicklungsposition ≥ 0 und Position + Wickelhöhe ≤ Gesamthöhe − Rückwandstärke. Unpassende Abmessungen werden gemeldet und nicht automatisch verändert.
- Kernmaterial weiterhin aus der installierten FEMM-Bibliothek wählen. Bei Ferrit die thermische Kerndichte und Wärmekapazität im Temperaturreiter passend zum tatsächlichen Material anpassen; die magnetische Materialwahl setzt diese Stoffwerte nicht automatisch.
- Die Topfkernmasse folgt aus Mittelpol, Rückwand und Aussenwand ohne doppelt gezählte Volumina. Direkte Umgebungskühlung der Wicklung wird beim Topf nur über die offene Ring-Stirnfläche angesetzt. Am Kern zählen äusserer Mantel, Rückseite und offene Stirnflächen; die Topf-Innenflächen sind ausgeschlossen. Flächenanteile, Wärmeübergänge und Kopplung zum Kern bleiben sichtbar und anpassbar.
- In FEMM werden gemeinsame Teilkanten zerlegt, damit an Mittelpol, Rückwand und Aussenwand keine überlappenden Segmente entstehen. Dünne Topfwände und Rückwände werden auf höchstens ein Drittel ihrer Stärke vernetzt. Ein eingeschlossener Luftraum hinter einer radial vollständig anliegenden Wicklung erhält ein eigenes Luftlabel.

Dateiformat dieser Ausgabe: **Version 6**. Einstellungsdateien aus Version 1, 3 und 5 bleiben ladbar und erhalten aktive Bauteile mit Stabkernen. Alte gespeicherte Ergebnisse behalten ihre ursprüngliche Geometrie.

Die Kernform-Namen beschreiben das hier verwendete Modell, keine Zusage für ein beliebiges Kaufteil. Beispielzeichnungen realer Topfkerne: [TDK, Pot cores](https://www.tdk-electronics.tdk.com/download/187040/8b512cb09e47c9a244d46221339a0a9b/pdf-pcores.pdf).

Ein direkt ladbares Beispiel ist eispiele/topfkern.json: im Programm **Laden** wählen und diese Datei öffnen. Alle Masse sind Beispielabmessungen und frei anpassbar.

## Bedienung

Die sechs Eingabereiter sind Aufbau, Oben, Unten, Objekt, Sweeps und Netz. Kern, Wicklung und Ansteuerung sind getrennt gruppiert; beim Objekt erscheinen nur passende Eingabefelder. Beide Magnete sind unabhängig. Abmessungen werden nie automatisch korrigiert. Fehler stehen unter der Vorschau und blockieren die Berechnung. Dezimalkommas sind erlaubt. Scrollbalken halten sämtliche Eingaben erreichbar.

Über den Eingabereitern stehen **Speichern**, **Laden** und **Zurücksetzen**. Speichern schreibt die vollständigen Aufbau-Einstellungen in eine frei benennbare JSON-Datei: beide Magnete und Wicklungen, Materialien, Windungszahlen, Ströme, Schwebeobjekt und Masse, Luftspalte, Sweep-Werte, numerische Einstellungen und die thermischen Annahmen samt Spulenauswahl. Mit mehreren Dateien lassen sich verschiedene Aufbauten aufbewahren. Laden stellt die gespeicherten Werte exakt wieder her, auch nach einem Neustart. Fehlerhafte oder geometrisch ungültige Dateien verändern die aktuellen Eingaben nicht. Zurücksetzen stellt die Programm-Standardwerte wieder her; gespeicherte Dateien bleiben bestehen. Während eines FEMM-Auftrags sind diese drei Tasten gesperrt.

Der Reiter **Ergebnisse** zeigt oben Magnetkraft, Gewichtskraft und Nettokraft des ausgewählten gespeicherten Falls. Ein Klick auf eine Tabellenzeile wechselt den angezeigten Fall. Die Tabelle besitzt ausreichend hohe Zeilen und zeigt beide Luftspalte. Details und Sweep-Auswertung stehen kompakt darunter. Geänderte oder geladene Eingaben erfordern eine neue Berechnung; vorhandene Ergebnisse behalten ihre ursprünglichen Werte. CSV-Exporte enthalten weiterhin die vollständige numerische Genauigkeit.

Im Reiter **Geometrie** stehen über dem Schnitt die Abmessungen des gewählten Eingabereiters: oben/unten die Kern- und Spulenmasse, beim Objekt Kugeldurchmesser, gegebenenfalls Wandstärke und Innenmagnetmasse. Beim Anklicken eines Massfelds wird das entsprechende Mass mit einem blauen Pfeil direkt am Bauteil markiert. Änderungen aktualisieren Vorschau und Massangaben sofort; FEMM wird dabei nicht aufgerufen. Die Gesamtmasse des Objekts wird zusätzlich angezeigt.

Magnetfeld und Diagramm passen ihre Zeichenflächen bei Reiterwechsel, Fensteränderung und Windows-Skalierung an. Vor dem ersten Sweep zeigt das Diagramm einen Hinweis. Eine Einzelberechnung liefert das Feldbild; für ein Diagramm anschliessend **Stromsweep** oder **Haltestrom-Sweep** starten.

Die Wicklungsposition bezeichnet den Abstand vom objektseitigen Pol bis zum Anfang der Wicklung, positiv vom Objekt weg. Beim Stabkern ist negativer Überstand zulässig, wenn die Wicklung ihren Kern teilweise umgibt und keine Bauteile kollidieren. Ein gleicher Kern- und Spulen-Innendurchmesser ist zulässig; ein realer Spulenkörper benötigt entsprechend mehr Innendurchmesser.

`H = Kugeldurchmesser + Luftspalt oben + Luftspalt unten`. z=0 liegt zwischen den Polflächen; verschiedene Luftspalte verschieben die Kugel. Stahlmasse folgt aus Geometrie und eingegebener Dichte. Eine gemessene Gesamtmasse ersetzt nur die Gewichtskraft. Für die nichtmagnetische Kugel mit Permanentmagnet ist die Gesamtmasse erforderlich.

- **Einzelfall berechnen:** gemeinsames Modell beider Magnete. Danach öffnet sich der Reiter **Magnetfeld** mit Feldlinien direkt in der massstäblichen Geometrie. Im Reiter Ergebnisse stehen Magnetkraft Fz, Gewichtskraft und Nettokraft. Fz ist nach oben positiv; `Fnetto = Fz - m·9,81`.
- **Stromsweep:** oberer Strom von Start bis Ende; unterer Strom aus dem Reiter Unten bleibt konstant.
- **Haltestrom-Sweep:** beide Luftspalte sind gleich und werden gemeinsam variiert. Der eingegebene Suchbereich darf negative Ströme enthalten. Grobscan, Vorzeichenintervalle und erkennbare Residualminima werden untersucht; gefundene Kandidaten werden mit FEMM nachgerechnet. Mehrere Lösungen werden angezeigt. Ein endlicher Scan kann schmale Lösungsbereiche übersehen. „Nicht erreichbar im untersuchten Scan“ gilt nur für den gewählten Suchbereich und Scan.

**Abbrechen nach diesem Fall** beendet den Auftrag zwischen FEMM-Berechnungen. Die Oberfläche reagiert weiter; abgeschlossene Ergebnisse bleiben erhalten. Beim Schliessen wird die aktuelle Einzelberechnung beendet und die eigene FEMM-Instanz geschlossen.

## Magnetfeld mit der Maus anschauen

Die Startansicht behält den bisherigen Ausschnitt. Im Reiter **Magnetfeld** kannst du das gespeicherte Feld direkt erkunden:

- **Mausrad vor/zurück:** hinein- und herauszoomen. Über dem Feld dient die Mausposition als Zoomzentrum; über einer freien Fläche wird um die Bildmitte gezoomt.
- **Shift + Mausrad:** nur die Breite verändern. Herauszoomen zeigt seitlich mehr Feld, während der Höhenbereich gleich bleibt.
- **Mehr Breite / Weniger Breite:** den sichtbaren horizontalen Ausschnitt mit einem Klick erweitern oder wieder verengen. Der Höhenbereich bleibt gleich; der Schnitt bleibt massstäblich und wird nicht verzerrt.
- **Grundansicht:** Zoom, Breitenänderung und Verschiebung auf den ursprünglichen Ausschnitt des angezeigten Falls zurücksetzen. Die Ansichts-Tasten stehen in einem eigenen Bereich und verteilen sich bei wenig Platz auf mehrere Zeilen.
- **Linke Maustaste halten und ziehen:** das Bild frei verschieben. Ist der Pan- oder Rechteckzoom-Modus in der Werkzeugleiste eingeschaltet, übernimmt weiterhin dessen übliche Bedienung.
- **Haus-Symbol (Home) oder Doppelklick:** zur Startansicht zurückkehren. Bei Fokus im Plot funktionieren auch die Tasten Home, H und R. Die Zurück-/Vorwärts-Pfeile der Werkzeugleiste wechseln zwischen den Ansichten.

Zoom und Verschieben bleiben bei Reiterwechsel und Fensteränderung erhalten. Die Auswahl eines anderen berechneten Falls startet wieder mit dessen ursprünglicher Ansicht und einer neuen Ansichtshistorie. **PNG speichern** unter dem Magnetfeld exportiert den aktuellen Ausschnitt; **Feldbild speichern** im Reiter Ergebnisse exportiert weiterhin die ursprüngliche Feldansicht bzw. das native FEMM-Bild.

Die Navigation nutzt bereits gespeicherte FEMM-Felddaten des gesamten berechneten Luftbereichs. Sie startet keine neue Simulation. Mausrad und freies Ziehen bleiben innerhalb dieses Datenbereichs; die Flussdichte-Farbskala bleibt während der Navigation gleich. Der Farbbalken selbst wird nicht mitgezoomt. Die geometrische Vorschau und die Eingabereiter behalten ihre bisherige Bedienung.

## Drahtdurchmesser und elektrische Schätzung

In **Oben** und **Unten** unter **Wicklung** den **Draht-Ø Kupfer [mm]** eintragen. Gemeint ist der Durchmesser des runden Kupferleiters ohne Lack. Der Standardwert 1 mm ist ein Beispielwert und muss zum realen Draht passen. Dezimalkommas funktionieren, etwa `0,8`.

**Draht-Ø mit Lack [mm]** ist optional: Dort den Gesamtdurchmesser einschliesslich Isolation eintragen, falls bekannt. Er muss mindestens so gross wie der Kupferdurchmesser sein. Leer bedeutet unbekannt. Ist auch der Kupferdurchmesser unbekannt, beide Drahtfelder leerlassen; die magnetische Berechnung funktioniert weiterhin, elektrische Schätzung und Platzprüfung entfallen.

Unter **Elektrische Schätzung (20 °C)** werden beim Ändern der Werte sofort Querschnitt, geschätzte Drahtlänge, Widerstand, stationäre DC-Spannung, Kupferverlustleistung, Stromdichte und Füllgrad angezeigt. Beide Spulen werden unabhängig ausgewertet. Die Berechnung nimmt runden Kupferdraht und über den Wickelraum verteilte Windungen an:

- Querschnitt: `A = π · d² / 4` in mm².
- Mittlere Drahtlänge: `l = N · π · (D innen + D aussen) / 2 / 1000` in m.
- Widerstand bei 20 °C: `R20 = 0,017241 · l / A` in Ω (Kupfer, 100 % IACS).
- Stationäre Gleichstromspannung: `U20 = |I| · R20`; Kupferverlustleistung: `P20 = I² · R20`; Stromdichte: `J = |I| / A`.
- Füllgrad: Drahtquerschnitt mal Windungszahl geteilt durch radiale Wickelbreite mal Wickelhöhe. Ist der Durchmesser mit Lack bekannt, wird zusätzlich dessen Platzbedarf verwendet.

Ein einzelner Draht muss in Wickelbreite und Höhe passen. Überschreitet der Füllgrad die ideale Runddraht-Packgrenze von rund 90,7 %, wird die Berechnung blockiert. Über 75 % erscheint ein Hinweis. Diese Grenzen garantieren keine herstellbare Wicklung: Lack, Spulenkörper, Randabstände und Wickelanordnung benötigen Platz. Bei leerem Lackdurchmesser bezieht sich die Prüfung nur auf das Kupfer.

Widerstand, Spannung und Leistung sind Schätzwerte **bei 20 °C**. Anschlussdrähte und Wicklungsenden sind nicht berücksichtigt. Der reale Widerstand steigt bei Erwärmung; die Anzeige berechnet keine Spulentemperatur. Die DC-Spannung umfasst weder die induktive Spannung bei Stromänderung noch die Versorgungsspannung eines PWM-Stellers. Aus der Stromdichte wird keine pauschale Dauerstromfreigabe abgeleitet.

Im magnetostatischen FEMM-Modell bleiben **Windungszahl und Strom die vorgegebenen Grössen**. Ein anderer Drahtdurchmesser verändert weder die geometrischen Spulenabmessungen noch die Windungszahl automatisch. Bei gleichen Abmessungen, N und I bleiben Magnetfeld und Kraft gleich; Widerstand, Verlustleistung und Platzbedarf ändern sich. FEMM zeichnet weiterhin die homogenisierte Wicklung, keine einzelnen Drahtwindungen.

Speichern/Laden und Zurücksetzen umfassen die neuen Drahtwerte. Einstellungsdateien dieser Ausgabe verwenden Formatversion 6; Versionen 1, 3 und 5 bleiben ladbar. Alte Dateien und Ergebnisse enthalten keinen Drahtdurchmesser: Er bleibt beim Laden leer, damit kein Beispielwert als Messwert übernommen wird. Drahtwerte im Ergebnisbericht und in den zusätzlichen CSV-Spalten gehören zum **gespeicherten berechneten Fall**, einschliesslich des jeweiligen Sweep-Stroms. Geänderte aktuelle Eingaben ändern vorhandene Ergebnisse nicht. Während eines Auftrags sind die Drahtfelder gesperrt.

## Temperatur

1. Unter **Oben** bzw. **Unten** die Spule inklusive Kupfer-Drahtdurchmesser und Strom eingeben.
2. Im Reiter **Temperatur** die **Obere Spule** oder **Untere Spule** wählen. Die aktuellen Geometrie-, Windungs-, Draht- und Stromwerte werden automatisch übernommen.
3. Direkt oben Umgebungstemperatur, Betriebsdauer in Minuten, Temperaturgrenze und Kühlprofil einstellen. **Ruhende Luft** und **Luftstrom** sind veränderbare Beispielannahmen.
4. Bei Bedarf unter **Kühlung und Stoffwerte** Starttemperatur, Wärmeübergänge, freie Flächen und Materialwerte anpassen. Eine leere Starttemperatur bedeutet, dass Wicklung und Kern bei Umgebungstemperatur starten. Die Felder sind nach Bedeutung gruppiert und jeweils kurz erklärt.
5. **Temperatur berechnen** drücken. Unter **Temperaturverlauf** stehen drei grosse Werte für Wicklung, Kern und Kupferverluste am Ende, der Grenzstatus und das Diagramm. Das Diagramm wächst mit dem Fenster; der ausführliche Ergebnistext steht separat unter **Rechendetails**. Bei wenig Fensterhöhe werden kurze Erläuterungen ausgeblendet, damit mehr Platz für die Kurven bleibt. Fehlermeldungen bleiben sichtbar.

Die Berechnung läuft vollständig in Python, ohne FEMM und ohne Magnetfeldberechnung. Es wird ein konstanter Strom angenommen. Änderungen an Eingaben markieren das vorhandene Ergebnis als älteren Fall; Diagramm und Exporte bleiben bei dessen gespeicherten Werten, bis erneut gerechnet wird. Fehler im Schwebeobjekt oder in der nicht gewählten Spule blockieren die unabhängige Temperaturrechnung nicht.

**Ergebnis:** Wicklungs- und Kerntemperatur über der Zeit, Widerstand bei 20 °C sowie beim Start und Ende, Kupferverlustleistung beim Start und Ende und der erste Zeitpunkt, an dem der Grenzwert erreicht wird. Grenzzeiten werden unabhängig von der Plotauflösung gesucht; ein bereits zu Beginn erreichter Grenzwert ergibt 0 Minuten. Die Kurve läuft nach dem gewählten Grenzwert weiter. Spätestens bei **300 °C** endet sie mit einem sichtbaren Hinweis, weil die konstanten Stoff- und Kühlannahmen nicht weiter extrapoliert werden. Nicht erreichte Grenzwerte beziehen sich auf den tatsächlich berechneten Zeitraum, bei einem Modellende also auf die gekürzte Dauer.

Ein asymptotisch stabiles Gleichgewicht liefert den **rechnerischen Langzeitwert beider Teile** unter den eingegebenen Annahmen. Dieser steht in den Rechendetails. Bei instabilen oder isolierten neutralen Fällen erscheint kein zugesagter Langzeitwert. Werte über 300 °C werden ausdrücklich als formale Extrapolation ausserhalb des Modellbereichs und als nicht belastbarer Wert für den Dauerbetrieb gekennzeichnet.

### Zwei mittlere Temperaturen

Mit `Ta` als Umgebung, `Tcu` als Wicklungstemperatur und `Tfe` als Kerntemperatur gilt:

```text
R(Tcu) = R20 · [1 + alpha · (Tcu − 20 °C)]
Ccu · dTcu/dt = I² · R(Tcu) − Gcu · (Tcu − Ta) − Gk · (Tcu − Tfe)
Cfe · dTfe/dt = Gk · (Tcu − Tfe) − Gfe · (Tfe − Ta)
Gcu = hcu · Acu; Gfe = hfe · Afe; C = Masse · spezifische Wärmekapazität
```

Die lineare Kopplung wird analytisch über eine symmetrisch transformierte 2×2-Matrix gelöst. Eine neue SciPy-Abhängigkeit ist nicht nötig. Auch 0 A, negative Ströme, sehr starker Wärmeübergang und der Übergang zur Instabilität werden behandelt. Bei 0 A und Start bei Umgebungstemperatur bleiben beide Kurven konstant; ein warmer Start kann abkühlen.

Kupfermasse und R20 entstehen aus derselben mittleren Drahtlänge und Querschnittsformel wie die elektrische Schätzung. Die Kernmasse folgt aus dem vollen Stabzylinder beziehungsweise den drei nicht überlappenden Topfkernteilen. Die Spulenposition beeinflusst die Länge des von der Wicklung bedeckten Kernmantels und damit die angenommene freie Kernfläche. Wärmeübertragung zum Kern wird über den separat eingegebenen Leitwert `Gk` erfasst, nicht automatisch aus dem Luftspalt zum Kern abgeleitet.

### Kühlung und Materialannahmen

- **Wärmeabgabe h** für Wicklung und Kern ist einzeln veränderbar. Die Profile **Ruhende Luft** (8 W/(m² K)) und **Luftstrom** (30 W/(m² K)) sind reine Beispielannahmen; sie ersetzen keine Messung oder geometriespezifische Wärmeübergangsberechnung. Eigene Werte bleiben sichtbar als Benutzerdefiniert.
- **Übergang Wicklung–Kern:** Standard 0,3 W/K als Beispielwert für den gesamten Übergang durch Lack, Spulenkörper und Kontakt. 1 W/K bedeutet 1 W bei 1 °C Temperaturunterschied; 0 unterbindet den Austausch. Dieser Wert ist unabhängig von den zwei h-Werten anpassbar.
- **Freie Flächen:** Beim Stabkern Wicklungsaussenmantel plus beide Ring-Stirnflächen und Kernstirnflächen plus unbedeckter Kernmantel. Beim Topfkern nur die offene Wicklungs-Stirnfläche und äussere Kernflächen wie oben beschrieben. Beide Flächen können mit 0–100 % reduziert werden, etwa wegen einer Halterung oder Abdeckung. Die ermittelten Flächen stehen im Ergebnis.
- **Stoffwerte:** Kupferdichte 8930 kg/m³, Kupfer-Wärmekapazität 385 J/(kg K), Kupferkoeffizient alpha = 0,00393/K; Kerndichte 7870 kg/m³ und Kern-Wärmekapazität 450 J/(kg K) als veränderbare Eisen-/Stahl-Näherung. Die magnetische Materialauswahl setzt diese thermischen Werte nicht automatisch. Wärmekapazitäten und Dichten bleiben im Modell konstant.

Spulenkörpermasse, Gehäuse-/Halterungswärmekapazität, Eisenverluste, zusätzliche AC-/PWM-Verluste und gegenseitige Erwärmung zweier Spulen fehlen. Strahlung wird nicht separat berechnet; h ist ein angenommener konstanter effektiver Wärmeübergang. Für die reale Spule insbesondere die Kühlung und den Übergang zum Kern anhand eines Erwärmungsversuchs anpassen. **Die Anzeige ist eine Schätzung mittlerer Temperaturen und keine maximale lokale Temperatur oder Dauerstromfreigabe.**

**PNG speichern** exportiert das Temperaturdiagramm. **CSV speichern** exportiert beide Temperaturreihen, temperaturabhängigen Widerstand und Verlustleistung sowie die zugehörigen Spulendaten und sämtliche thermischen Annahmen als kommentierte Kopfzeilen. **Speichern/Laden** im allgemeinen Einstellungsbereich umfasst auch den optionalen neuen Abschnitt `temperature`; alte Aufbau-Dateien ohne diesen Abschnitt werden mit thermischen Standardwerten geladen. Fehlerhafte thermische Dateien verändern den Aufbau nicht. **Thermische Annahmen zurücksetzen** betrifft nur die neuen Parameter und erhält die gewählte Spule.

Hintergrund zu den Beispiel-Stoffwerten: [ELEKTRISOLA: Leiterwerkstoffe, Dichte und Temperaturkoeffizient](https://www.elektrisola.com/en-us/Metal), [Copper Development Association: C11000, spezifische Wärmekapazität](https://alloys.copper.org/alloy/C11000), [NIST: Wärmekapazität von Eisen](https://webbook.nist.gov/cgi/cbook.cgi?ID=C7439896&Mask=2). NIST gibt für Eisen bei 298 K 25,09 J/(mol K) an, entsprechend ungefähr 449 J/(kg K); 450 ist hier ein gerundeter, veränderbarer Anfangswert, keine Materialidentifikation.

## Netzfeinheit auswählen

Im Reiter **Netz** ein Profil wählen oder die Zahlen selbst eingeben. Die Auswahl gilt für Einzelfälle, Stromsweeps und Haltestromsweeps. Kleinere Netzgrössen und Kreisbogen-Schritte verfeinern das Netz und erhöhen die Rechenzeit. Die massstäbliche Vorschau benötigt kein FEMM-Netz.

| Profil | Lokal [mm] | Äussere Luft [mm] | Kreisbogen [°] | Empfohlene Verwendung |
|---|---:|---:|---:|---|
| Grob | 1,2 | 20 | 6 | Erster Stromsweep und Feldüberblick; Kräfte danach feiner prüfen |
| Standard | 0,6 | 10 | 3 | Normale Stromsweeps und erste Kraft-/Haltestromberechnungen |
| Fein | 0,3 | 5 | 1,5 | Kräfte, Halteströme und auffällige Kurvenstellen genauer prüfen |
| Sehr fein | 0,15 | 2,5 | 0,75 | Konvergenzvergleich mit Fein, vorzugsweise ausgewählte Einzelfälle |

Diese Werte sind Ausgangspunkte für den Standardaufbau, keine garantierten Genauigkeiten. Dünne Schalen oder Magnete und kleine Luftspalte können kleinere lokale Werte erfordern. Für eine Kraft oder einen Knick in einer Kurve denselben Fall bei unveränderter Geometrie und unveränderten Strömen mit Standard, Fein und bei Bedarf Sehr fein vergleichen. Erst ausreichend kleine Änderungen für den eigenen Zweck sprechen für ein brauchbares Netz. FEMM empfiehlt für Kraftberechnungen insbesondere feines Netz im Luftbereich am untersuchten Objekt: [offizielle FEMM-FAQ, Frage 16](https://www.femm.info/doku/doku.php?id=faq).

**Lokal** gilt an Kernen, Polflächen, Objekt und naher Luft. Eine Hohlkugelschale wird zusätzlich auf höchstens Wandstärke/3 verfeinert; die homogenisierte Wicklung bleibt im Inneren bei mindestens 1 mm. **Äussere Luft** bestimmt das gröbere Netz weit vom Aufbau. **Kreisbogen** begrenzt den Winkelschritt an runden Konturen; kleinere lokale Netzgrössen können diese Konturen zusätzlich verfeinern. Werte müssen positiv sein, der Kreisbogen-Schritt zwischen 0,1° und 90° liegen.

Der **Luftbereich-Faktor** verändert die Entfernung des äusseren Modellrands, nicht die Netzfeinheit. Standardwert 4, Mindestwert 2. Zur Randprüfung beispielsweise 4 auf 6 erhöhen, bei gleichen Netzgrössen. Die Netzprofile ändern diesen Faktor nicht.

Eigene Netzwerte werden als **Benutzerdefiniert** angezeigt. Speichern/Laden und Zurücksetzen umfassen auch sämtliche Netzwerte. Ältere Einstellungsdateien bleiben kompatibel. Während einer Berechnung sind diese Eingaben gesperrt; eine Änderung wirkt erst beim nächsten Auftrag. Die Details eines gespeicherten Falls und seine FEMM-Zeilen im CSV zeigen stets dessen tatsächlich verwendete Netzwerte.

## Dateien und Modell

Berechnungen verwenden ausschliesslich temporäre FEMM-Arbeitsdateien. **Ergebnisse speichern…** öffnet die Ordnerwahl und erzeugt erst danach einen vollständigen Ergebnis-Unterordner: Geometrie, Werte als CSV/JSON, elektrische Kurven, bei Sweeps Diagramme und pro Fall ursprüngliches FEMM-Modell und Lösung. Beim Einzelfall werden zusätzlich `feld.png` und die originalen FEMM-Knoten- und Elementdaten übernommen. Ohne Speichern werden die Ergebnisse beim Beenden verworfen. **PNG speichern** exportiert nur die gewählte Ansicht. Die Matplotlib-Werkzeugleiste erlaubt Zoom und Verschieben.

Die Feldlinien sind Konturen des von FEMM berechneten magnetischen Flusses auf dem exportierten FEMM-Netz. Der achsensymmetrische Meridianschnitt wird links gespiegelt, damit der gesamte Aufbau erkennbar ist. Die Turbo-Farbskala zeigt die Flussdichte in Tesla, standardmässig auch in den Bauteilen. Über die Farbskala und das Häkchen im Reiter Magnetfeld lassen sich die Darstellung und der Bereich umschalten. Die Feldansicht gehört zum angezeigten berechneten Fall; geänderte Eingaben werden erst nach erneuter Berechnung übernommen. Sweeps exportieren ihre Kurven und Kräfte, keine Feldbilder für jeden Zwischenfall.

Im Reiter Ergebnisse stehen "FEMM öffnen", "Feldbild speichern" und "CSV speichern". "Feldbild speichern" bietet beim Einzelfall die gemeinsame Feld-/Geometrieansicht als PNG und zusätzlich die native FEMM-Ansicht als BMP. "FEMM öffnen" zeigt das Original mit Feldlinien und Flussdichte. Dessen Farbskala beträgt 0–2 T; höhere Werte erhalten die oberste Farbe. In FEMM lässt sich diese Skala ändern.

FEMM rechnet magnetostatisch und achsensymmetrisch für r≥0. Bibliotheksmaterialien behalten ihre B-H-Kurven. Die Stahl-Hohlkugel enthält Schale und Luftinnenraum. Die nichtmagnetische Hülle wird als µr=1 modelliert. Kraftintegral 19 wird auf die Stahlschale, massive Kugel oder den Innenmagneten angewendet, ohne zusätzliche Skalierung. Ein endlicher Luftbereich besitzt A=0 am Rand; das Netz wird am Objekt verfeinert.

## Prüfung dieser Ausgabe

Am 2. Oktober 2026 erfolgreich geprüft:

- 64 Logiktests für bestehende Funktionen, Kernformen, Einstellungen, Wickelraum, FEMM-Blockzuordnung und das thermische Zweiknotenmodell.
- Echte Tkinter-Bedienprüfungen bei drei Skalierungen (100 %, 150 %, 225 %): unabhängige Kernwahl, Massfelder, Dezimalkomma, Vorschau, Fehlersperren, Temperaturrechnung sowie Speichern/Laden inklusive ursprünglicher Version 3.
- Überarbeitete Temperaturansicht in fünf Fenstergrössen von 1280 × 720 und 1100 × 800 bis 3200 × 1900 bei drei Skalierungen geprüft. Kurvenbeschriftungen, Ergebniswerte, Grenzstatus, Modellende bei 300 °C, warme Starts, Kühlprofile, Fehlersperren, veraltete Ergebnisse und JSON-/CSV-/PNG-Ausgaben funktionieren. Das thermische Rechenmodell bleibt unverändert.
- Fünf echte FEMM-4.2-Läufe mit Zylinderkernen, zwei Topfkernen, gemischten Kernformen, einer Spule mit eingeschlossener Luftkammer sowie dünner Topfwand und Rückwand. Originale Felddaten und Feldbilder wurden erzeugt. Die Kernvolumina stimmen mit den analytischen Volumina überein; der Kugelvolumenfehler liegt im verwendeten Basisnetz bei etwa 0,069 %.

Die neuen Beispielresultate stehen in `pruefwerte_topfkern.csv`. Sie prüfen die Implementierung und ersetzen keine Konvergenzprüfung oder Messung eines realen Aufbaus.

Im Programmordner ausführen:

```powershell
python -m unittest -v tests tests_navigation tests_thermal tests_core_switch
```

Die Werte in `pruefwerte.csv` und in der folgenden Tabelle stammen aus früheren Prüfungen der Stabkernversion. **Sie sind keine Validierung der neuen Topfkern-Geometrie.**

| Objekt, Beispiel Ø10 mm | Basis Fz [N] | Feineres Netz [N] | Zusätzlich grösserer Luftbereich [N] |
|---|---:|---:|---:|
| Massive Stahlkugel | 0,040699 | 0,039859 | 0,040818 |
| Hohlkugel, Wand 1 mm | 0,041044 | 0,040445 | 0,040572 |
| Kugel mit Scheibenmagnet | 0,050787 | 0,049367 | 0,048118 |

Prüffall: Standard-Magnete, 15 mm Luftspalt je Seite, oben 2,81 A, unten 0,393 A. Basisnetz 0,6 mm, äusseres Luftnetz 10 mm, Luftbereichfaktor 4. Feinprüfung halbiert Netzgrössen und Bogenwinkel; Luftprüfung vergrössert anschliessend den Bereich um Faktor 1,5. Änderungen betragen bis 2,9 %. Die Such-Krafttoleranz 0,0002 N ist ein numerisches Abbruchkriterium und keine physikalische Genauigkeitsgarantie. Neue Geometrien benötigen eigene Konvergenzprüfungen; Netz und Luftbereich lassen sich jetzt im Reiter Netz ändern.

Logiktests erneut ausführen: `python -m unittest -v tests tests_navigation tests_thermal tests_core_switch tests_field_measurements`.

Ein Kräftegleichgewicht beweist weder geregeltes Schweben noch seitliche Stabilität oder thermische Dauerbetriebsfähigkeit. Kaufproduktwerte sind nur dann vergleichbar, wenn die gewählte Zylinder- oder offene Topfkerngeometrie und das Kernmaterial dem realen Aufbau entsprechen.

API-Referenz: [offizielles pyFEMM-Handbuch](https://www.femm.info/doku/lib/exe/fetch.php?media=upload%3Apyfemm%3Apyfemm-manual.pdf).
