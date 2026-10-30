# ToF Local Knowledge – Meilenstein Dokumenten-Chat

**Zweck:** Zentrale, einmalige Abnahmeliste für den bestehenden lokalen
Dokumenten-Chat nach Abschluss des Funktionsausbaus. Kein Nachweis eines
bereits auf DOMs Zielsystem installierten Produkts.

## Verbindlicher Funktionsumfang

Der Alltagsweg ist die bestehende lokale Browser-Startseite `/`:
bewusst freigegebene Dateien oder Ordner auswählen, automatischer Import
in den konfigurierten Quellenbereich, begrenzte automatische Indexierung,
sichtbare Fortschritts- und Fehlerzustände, Fragen und begrenzte
Anschlussfragen, belegte Antworten und aufklappbare Originalstellen.
Erweiterte Diagnosefunktionen bleiben unter „Weitere Funktionen“.
Die bestehenden `run.py`-/Compose-Startwege, Quellen-/Portgrenzen,
optionalen Ollama-Profile und das einbenutzerlokale Betriebsmodell
bleiben verbindlich.

## Zentrale Meilenstein-Liste

| ID | Nachweis | Status | Quelle / konkreter Restbedarf |
| --- | --- | --- | --- |
| M01 | Offizieller Repository-/Compose-Startweg beibehalten | CODE_OK | `run.py`, `compose.full.yml`; CI Compose-Konfiguration |
| M02 | Eine Startseite für Dateien, Chat, Quellen und Rückmeldung | CODE_OK | UI und gezielte JS-Tests; Browser-Abnahme offen |
| M03 | 1-Datei- und Mehrfachimport mit verständlicher Teilmeldung | CODE_OK | Node-UI-Tests; physischer Import auf Zielrechner offen |
| M04 | Seitennavigation beim Indexieren über leere Chargen | CODE_OK | gezielter synthetischer Test; Runtime-Prüfung offen |
| M05 | Beliebige Antworten ohne Belege verhindern | CODE_OK | QA-Negativtests; gezielte Runtime-Abnahme offen |
| M06 | Natürliche begrenzte Nachfragen, Themenwechsel, Neuer Chat | CODE_OK | QA-/UI-Tests; kein persistentes Gedächtnis |
| M07 | Optionale ausschließlich lokale LLM-Treffersortierung | CODE_OK | QA-Test: validierte Treffer-IDs / Fallback; realer Modellbetrieb offen |
| M08 | Quellpaket auf eingefrorenem Commit erzeugen | CODE_OK | GitHub-Paketlauf [40964535162](https://github.com/IMaugrenI/tof_local_knowledge/actions/runs/40964535162) bestanden; nächster Kandidat nutzt den aktuellen eingefrorenen Ausbau-Commit. ZIP-/Checksum-Nachweis getrennt von Runtime-Abnahme. |
| M09 | Zielsystem: Start, Index, Suche, Chat, Quellen, Negativfrage | OFFEN | DOM führt **eine** zusammenhängende Runtime-Prüfung durch |
| M10 | Betriebssysteme und Einbenutzer-/Netzgrenzen | OFFEN | Nur tatsächlich getestete Plattformen freigeben |
| M11 | DOM: GO/NO-GO über genau diesen Kandidaten | OFFEN | Entscheidung nach M08–M10 und gegebenenfalls gezieltem Nachtest |

`CODE_OK` bedeutet ausschließlich: Quellcode implementiert und relevante
GitHub-Entwicklungsprüfungen vorhanden. Es bedeutet **nicht**
`RUNTIME_BESTANDEN`, Produktfreigabe oder Installer-Zusage.

## Ein gemeinsamer Praxislauf statt vieler Schleifen

1. **Nur neutrale Testdokumente:** eine TXT/MD, danach fünf oder mehr gemischte
   Dateien einschließlich einer absichtlich ungültigen oder unlesbaren.
2. **Verarbeitung verfolgen:** Auswahl führt zu Kopie/Index ohne weiteren
   Indexklick; Fortschritt und Dateinamen/Fehler sind sichtbar. Keine falsche
   „alles fertig“-Meldung bei Teilfehlern.
3. **Fragen/Quellen:** eine belegte Antwort, zwei zusammenhängende Nachfragen,
   eine unabhängige neue Frage, eine angezeigte Originalstelle.
4. **Negativfall:** Frage ohne ausreichende Belege erhält keine erfundene
   Antwort oder Zitate; „Neuer Chat“ setzt Gesprächskontext zurück.
5. **Grenzen:** Originaldateien unverändert, kein Zugriff auf ungewählte
   Ordner, keine fremde Hostfreigabe, kein automatisches Modell-Laden.
6. **Betrieb:** nur erforderliche Checks des offiziell gestarteten Stacks,
   keine zweite Compose-Instanz, keine produktiven Daten verändern.
7. Ergebnisse und tatsächliche Nachweise in M08–M11 eintragen;
   P0/P1 vor GO beheben, P2 dokumentieren und von DOM entscheiden lassen.

## Paketbereitstellung

Nur der vorhandene GitHub-Workflow
`Actions → Source distribution candidate` erzeugt ein Quellpaket-ZIP
mit `CHECKSUMS.sha256`. Für den Meilenstein kann dieser Workflow
durch einen **explizit angelegten** Branch `candidate/**` genau einmal
ausgelöst werden. Das Archiv enthält keine private lokale Datenbank,
keine `.env` und keine produktiven Dokumente.

Das Archiv ist **kein nativer Installer**. Vor GO keine öffentliche
Release-Behauptung. Download- und Startdetails stehen in
`docs/RELEASE_PACKAGE_DE.md`.


## K25 – zusätzlicher optionaler semantischer Nachweis

Die festgelegte Gesamt-Abnahme M01–M11 wird **nicht** um eine neue Pflicht-Testschleife erweitert. Die lokale Vektorsuche ist ausdrücklich optional und steht im Standardpaket ohne konfiguriertes Modell nicht zur Verfügung. Die Architektur nutzt das vorhandene `VECTOR(768)`-Feld und den vorhandenen Ollama-Dienst. Ein semantischer Modelllauf auf DOMs Zielsystem darf nur nach bewusst aktivierter optionaler Modellkonfiguration als gesonderter Nachweis bewertet werden. Ohne Modell gilt weiterhin das bestehende lexikalische, beleggebundene Produkt. Die rein codebasierten Tests für Ein-/Ausgabegrenzen ersetzen keine Modell-Abnahme.
