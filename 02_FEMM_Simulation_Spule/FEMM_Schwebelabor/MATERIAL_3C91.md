# 3C91 im Schwebelabor

In **Oben / Unten → Kernform und Abmessungen → Material** den Eintrag
**3C91 (25 C, Naeherung)** wählen. Funktioniert für Zylinder- und Topfkerne.
Keine Änderung an der FEMM-Installation nötig. Die Definition wird bei jedem
Modellaufbau direkt in das FEMM-Dokument geschrieben und im `.fem` gespeichert.
Die bisher verfügbaren Bibliotheksmaterialien bleiben erhalten.

## Daten und Quelle

Ferroxcube, *3C91 Material specification*, 2008-09-01, Tabelle auf Seite 2:
https://megatron.ch/downloads/pdf/materialien/3c91.pdf

| Grösse | Datenblattwert |
| --- | --- |
| Anfangspermeabilität µi | 3000 ±20 %, 25 °C, ≤10 kHz, 0,25 mT |
| Flussdichte bei H = 1200 A/m | ca. 0,47 T bei 25 °C und 10 kHz |
| Flussdichte bei H = 1200 A/m | ca. 0,37 T bei 100 °C und 10 kHz |
| Spezifischer elektrischer Widerstand | ca. 5 Ω·m bei 25 °C |
| Dichte | ca. 4800 kg/m³ |

3C91 ist ein Leistungsferrit und darf nicht durch eine Stahlkennlinie ersetzt
werden: insbesondere liegt der Sättigungsbereich deutlich niedriger.

## Verwendetes Schätzmodell

Das Datenblatt enthält keine vollständige tabellierte DC-Neukurve. Daher ist
dieser Eintrag ausdrücklich eine **Näherung für erste Vergleiche**, keine
verifizierte 3C91-Gleichstromkennlinie. Die AC-Kennwerte dienen als Anker für
eine angenommene hysteresefreie, isotrope Sättigungsfunktion:

    µ0 = 4π · 10^-7 H/m
    µi = 3000
    Js = 0,470 T - µ0 · 1200 A/m
    B(H) = µ0 · H + Js · tanh[µ0 · (µi - 1) · H / Js]

Die Anfangssteigung entspricht µ0·µi, und B(1200 A/m) liegt näherungsweise bei
0,470 T. Oberhalb der Sättigung wächst B mit der Vakuumsteigung weiter;
0,47 T ist keine harte obere Grenze. Die Zwischenwerte sind Modellannahmen,
keine aus dem Diagramm digitalisierten Messwerte. Sie sind besonders für
die Vorhersage von Kräften und differentiellen Induktivitäten unsicher.
Die Punkte werden FEMM als B [T], H [A/m] übergeben; die elektrische
Leitfähigkeit ist 0,0000002 MS/m. Die Feldrechnung bleibt magnetostatisch.

Für belastbare Auslegung die Kennlinie anhand gemessener Kräfte/Ströme
überprüfen oder durch gemessene DC-B-H-Daten ersetzen. Das Modul
`core_materials.py` hält die Definition zentral.

## Temperatur und Geometrie

Der Materialeintrag gilt fest für **25 °C Kerntemperatur**. Die Eingabe der
Wicklungstemperatur und der Temperaturreiter ändern diese Kennlinie nicht.
Hysterese-, Frequenz- und Kernverluste werden nicht modelliert. Für die
thermische Schätzung im Temperaturreiter die Kerndichte auf **4800 kg/m³**
setzen und Wärmekapazität/Wärmeübergang des realen Ferrits separat prüfen;
die bisherigen thermischen Stahl-Standardwerte werden nicht automatisch ersetzt.
Bei einem Ferrit-Schwebeobjekt dessen Dichte ebenfalls separat anpassen.

Die Kernabmessungen werden durch die Materialwahl nicht verändert. Beim
P66/56 bleiben die vorhandenen Vereinfachungen des offenen Topfkernmodells
(ohne Bohrung und Schlitze) bestehen.

## Prüfung dieser Änderung

Automatisierte Tests prüfen Auswahl mit/ohne FEMM-Materialbibliothek,
Filterung, Validierung, Speichern/Laden, B-H-Einheiten und die tatsächlichen
Materialaufrufe beim FEMM-Modellaufbau mit einem aufzeichnenden Testobjekt.
Ein echter FEMM-Solverlauf auf Windows ist in dieser Umgebung nicht möglich.
