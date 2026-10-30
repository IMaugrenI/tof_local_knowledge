# ToF Local Knowledge V1 – verbindliche Abnahme- und Gutachtenliste

**Status:** Freigegebene *Prüfspezifikation* für den Testkandidaten, **keine Abnahmebescheinigung**.  
**Geltung:** Local Knowledge, *einseitiger lokaler Dokumenten-Chat* auf **einem von DOM benannten Referenz-Zielrechner**; keine allgemeine Produktions-, Kunden- oder Mehrbetriebssystemfreigabe.  
**Vertrag:** Blueprints `01_BAUPRINZIPIEN`, `02_SMOKE_CHECK`, `03_DOCKER_RUNTIME`, `05_MANDATS_GRENZEN`, `06_RELEASE_RUNTIME`, `13_TARGET_PC_INSTALL` sowie die nachgewiesene Produktarchitektur. Produktfremde Messenger-, Door-/Auto-Send-, Langzeit-Memory- und Assistenten-Lifecycle-Funktionen sind **nicht** Teil dieses Produkts.

## A. Unveränderlicher Abnahmerahmen (Scope-Freeze)

- **Zu prüfender Kandidat:** Git-Commit `3071f07651ec9bacb6e3a1ba7acfb93a5f190753`; GitHub-Quellpaket `tof_local_knowledge-source-candidate-3071f07651ec.zip`; Paketworkflow [40976973063](https://github.com/IMaugrenI/tof_local_knowledge/actions/runs/40976973063).
- **Kontrollwert des ursprünglich erzeugten ZIP:** SHA-256 `8be43becc4f973a8508fe3e6e5a4bbaec22f0d3aa75c51f8b8e9388facd919dc`. Dieser Wert gilt **nur** für genau dieses ZIP und seinen im Paket mitgelieferten Namen. Andere ZIPs, geänderte Inhalte oder neue Kandidaten benötigen eigene Checksummen.
- Der ZIP-Stand ist **nicht** identisch mit späteren rein dokumentarischen Änderungen an dieser Prüfliste; allein der obige Code-Commit ist die erste Prüfbasis.
- **Produktumfang:** vorhandener `run.py`-/`tof_cli`-/`compose.full.yml`-Startweg; lokaler Browser `http://127.0.0.1:8785/`; ausdrücklich ausgewählte Dateien/Ordner importieren, automatisch indexieren, Status und Dateifehler sehen, dokumentenbezogen fragen/nachfragen, Quellen öffnen, „Neuer Chat“. Einbenutzerbetrieb mit lokalen Ports und aktivierten Quellen.
- **Nicht enthalten:** echte dauerhafte Gesprächs-Memory, frei generierte/semantisch unabhängig geprüfte Antworten, OCR/Bild-/Audio-/Videoimport, Multiuser-ACLs, öffentlicher Webzugang, Hintergrund-Watcher, nativer Installer, allgemeine Freigabe für Windows und macOS sowie ein öffentliches Release.
- **Optional und nicht GO-blockierend:** explizit aktiviertes lokales Ollama-Reranking und 768D-pgvector-Ähnlichkeitssuche. Im Standardversuch **ausgeschaltet**. Falls DOM diese Funktion gesondert testen möchte, wird sie als `OPTIONAL` mit eigener Beweislage bewertet, nicht als nachträgliche Pflichtanforderung.
- **Keine Scope-Erweiterung während der Abnahme.** Echte Sicherheitsmängel (P0/P1) dürfen korrigiert werden; sonstige Funktionswünsche wandern ins nachgelagerte Backlog. Ein Prüfbericht behauptet nur tatsächlich ausgeführte Nachweise.

## B. Verantwortlichkeiten und Nachweistypen

| Rolle | Verantwortung |
| --- | --- |
| **ChatGPT** | Prüfbündel und Belege analysieren, diese **eine** Liste führen, P0/P1/P2 und fehlende Nachweise einordnen, gezielte kopierfertige Prüf-/Korrekturaufträge und Abschlussgutachten erstellen. |
| **Lokale KI** | Bestehendes DEV-Repository lesen, vorhandene Tests/CI übernehmen, fehlende **isolierte** Prüfungen durchführen und Testberichte liefern; keine selbstständigen Produktkorrekturen oder Bündelerstellung während der Abnahme. |
| **DOM** | Kandidat/Zielsystem festlegen, Review-Bündel bereitstellen, echte Terminal-/Browser-/Betriebsprüfungen ausführen, Betreiberentscheidungen treffen und abschließendes **GO oder NO-GO** erklären. |

Nachweistyp `DEV` = GitHub-CI/Quellcode/isolierter Test. `RUNTIME` = tatsächlicher Betrieb auf DOMs Zielrechner. `BETREIBER` = ausdrückliche Entscheidung DOMs. Kein DEV-Nachweis darf als Runtime-Nachweis ausgegeben werden.

**Status je Prüfpunkt:** `OFFEN` (noch unbewertet), `DEV_BESTANDEN` (nur CODE-Nachweis), `RUNTIME_BESTANDEN` (mit nachvollziehbarem Runtime-Beleg), `NICHT_BESTANDEN`, `BLOCKIERT_UMGEBUNG`, `NACHWEIS_FEHLT`, `NICHT_ANWENDBAR` (nur mit DOM-Begründung). `OPTIONAL_NICHT_GEPRUEFT` gilt nur für echte Optionen.

## C. Einzige verbindliche Prüfliste (P01–P20)

**Regel:** Die hier aufgeführten *20* IDs sind die vollständige Liste. **P01–P18** sind Pflicht, **P19** ist optional, **P20** ist die verbindliche Abschlussentscheidung. Bestehende Evidenz darf übernommen werden; nur die jeweils noch offene **Nachweisart** wird geprüft.

| ID | Abnahmegegenstand und objektives Bestehen-Kriterium | Genügender Nachweis | Startstatus |
| --- | --- | --- | --- |
| **P01** | **Identität/Integrität:** Exakt festgelegtes ZIP, Commit und SHA-256 stimmen überein; ZIP lesbar; keine `.env`, privaten Daten, Secrets oder unerlaubten generierten Laufzeitdateien im Kandidat. | **DEV:** GitHub-Paketworkflow, SHA-256-Abgleich und Archiv-Inhaltsliste. | DEV_BESTANDEN; Ziel-ZIP-Abgleich offen |
| **P02** | **Nur offizieller Betriebsweg:** Starter verwenden `run.py` und bestehendes Compose; keine zweiten Repos, Zweitstacks oder konkurrierenden Prozesse. Auf dem Zielrechner startbar, Pflichtdienste im erwarteten Zustand. | **DEV:** vorhandene Compose-CI; **RUNTIME:** Start-/Statusprotokoll, vorhandene Dienste. | DEV_BESTANDEN; RUNTIME offen |
| **P03** | **Lokalität/Ports:** UI lokal erreichbar, Ports wie konfigurierte Bindings; keine unerwartete öffentliche Erreichbarkeit (IPv4 und, soweit Host unterstützt, IPv6), kein stiller Portwechsel. | **DEV:** Port-/Bind-Konfiguration; **RUNTIME:** tatsächliche Socket-/Compose-Portliste, nur Adressen/Ports. | DEV_BESTANDEN; RUNTIME offen |
| **P04** | **Eine Benutzerseite:** `/` zeigt Dateiauswahl, Status, Chat und Quellen ohne technischen Seitenwechsel; „Weitere Funktionen“ ist vorhanden; keine sichtbaren internen Stacktraces. | **DEV:** vorhandene UI-Tests; **RUNTIME:** ein Browserablauf, ggf. Screenshot neutraler UI. | DEV_BESTANDEN; RUNTIME offen |
| **P05** | **Bewusste Dateifreigabe:** Nur bewusst ausgewählte Dateien/Ordner werden kopiert; Originale bleiben unverändert; nicht ausgewählte Ordner werden nicht durchsucht. | **DEV:** Upload-/Path-Tests; **RUNTIME:** neutrale Quell- und Nicht-Quell-Fixture mit Soll/Ist-Vergleich. | DEV_BESTANDEN; RUNTIME offen |
| **P06** | **Einzelimport:** Eine geeignete TXT-/MD-Datei wird ohne zusätzlichen Index-Klick übernommen, verarbeitet und anschließend über Suche/Chat gefunden. | **DEV:** Import-UI-Tests; **RUNTIME:** ein echter Datei-zu-Antwort-Durchlauf. | DEV_BESTANDEN; RUNTIME offen |
| **P07** | **Mehrfachimport/Indexfortschritt:** Ein zusammenhängender Lauf mit **mindestens neun gültigen kleinen Dateien plus einer ungültigen** überschreitet die Acht-Dateien-Indexcharge; gültige Dokumente werden nicht durch einen Fehler blockiert. Scan-Cursor bleibt nicht auf leeren Seiten stecken. | **DEV:** Index-/Pagination-Tests; **RUNTIME:** eine neutrale 10-Dateien-Auswahl und sichtbarer Endstand. | DEV_BESTANDEN; RUNTIME offen |
| **P08** | **Dateigrenzen/Ablehnung:** Nicht unterstützte Endung, zu große Datei oder unsicherer Pfad werden abgewiesen und begründet; bekannte Limits (12 MiB/Datei, 4 Dateien/Request, 300 Dateien/Auswahl) werden nicht still aufgeweicht. | **DEV:** Import-/Path-Tests; **RUNTIME:** ungültige Datei aus P07; keine 300er-Lastprüfung erforderlich. | DEV_BESTANDEN; RUNTIME teilweise über P07 |
| **P09** | **Ehrlicher Endstatus:** Kopier-/Indexfortschritt endet nicht fälschlich mit „alles bereit“, solange Dateien übersprungen, fehlerhaft oder unvollständig sind. Betroffene Dateinamen/Gründe erkennbar; bei Fehler Abschluss statt endlosem Spinner. | **DEV:** UI-Status-/Stillstandstests; **RUNTIME:** Status aus P06/P07. | DEV_BESTANDEN; RUNTIME offen |
| **P10** | **Geänderte und fehlende Quellen:** Geänderte Dateien werden wieder als bearbeitungsbedürftig erkannt; fehlende/fehlgeschlagene Dateien erscheinen nicht als gültiger, aktueller Suchbeleg. Keine stillen Änderungen an Originalen. | **DEV:** vorhandene Ingest-/Extraktions-/Search-Tests; **RUNTIME:** nur falls aus P06/P07 nicht bereits belegbar, ein gezielt geänderter neutraler Testfall. | DEV_BESTANDEN; RUNTIME gegebenenfalls offen |
| **P11** | **Dokumentensuche:** Bekannte neutrale Stichworte finden die erwarteten Originaldokumente samt relativen Quellen-/Segmentreferenzen; inaktive und nicht freigegebene Dokumente erscheinen nicht als aktuelle Treffer. | **DEV:** Such- und Scope-Tests; **RUNTIME:** Suche zu P06/P07, Sollantwort aus Fixture bekannt. | DEV_BESTANDEN; RUNTIME offen |
| **P12** | **Quellengebundene Antwort:** Frage zu festgelegtem Fixture-Inhalt zeigt zutreffenden Originalauszug, Dokument/Segment und anklickbaren Beleg auf der einen Seite; keine freien ungestützten Tatsachen. | **DEV:** QA-/Evidenz-Tests; **RUNTIME:** eine belegte Frage und ein geöffneter Originalbeleg. | DEV_BESTANDEN; RUNTIME offen |
| **P13** | **Negativfall/fail-closed:** Zu nachweislich fehlender Information keine erfundene Antwort, keine Zitate; breite OR-Treffer zählen ausdrücklich nicht als Beweise. | **DEV:** Negativ-/OR-Tests; **RUNTIME:** eine unbelastete Frage, z. B. „What is the private customer contract number?“. | DEV_BESTANDEN; RUNTIME offen |
| **P14** | **Gesprächsfolge:** Zwei aufeinanderfolgende Anschlussfragen behalten begrenzten Themenbezug; neue eigenständige Frage oder „Neuer Chat“ trennt den Kontext; kein dauerhaftes Memory behauptet. | **DEV:** Mehrturn-/Reset-Tests; **RUNTIME:** die drei Fragen plus Reset im selben Chat. | DEV_BESTANDEN; RUNTIME offen |
| **P15** | **Quellen- und Berechtigungsgrenzen:** Nur aktivierte Quellen und aktueller erlaubter `source_scope`; keine fremden Ordner, Quell-IDs, absoluten Hostpfade oder veralteten Dokumente als Beleg. Bestehender lokaler Einbenutzervertrag bleibt klar. | **DEV:** Source-/Path-/Scope-Tests; **RUNTIME:** neutrale negative Quellprobe, soweit gefahrlos. | DEV_BESTANDEN; RUNTIME offen |
| **P16** | **Fehler-/Ausfallverhalten:** Ein simuliert unerreichbarer Dienst oder fehlendes Modell führt zu verständlichem Fehler-/Fallback-Status, weder Sensitivdatenleck noch Endlosschleife; kein riskanter Live-Ausfalltest nötig. | **DEV:** vorhandene Mock-/Fallback-/Timeout-Tests, gezielte Auswertung. | DEV_BESTANDEN; nur bei Befund RUNTIME-Nachtest |
| **P17** | **Kontrollierter Betrieb:** Die bestehende Installation lässt sich regulär prüfen und kontrolliert beenden/erneut starten; neutrale indexierte Daten bleiben nach Neustart erhalten; keine produktive Datenlöschung, unnötige Neuinstallation oder Zweitinstanz. | **DEV:** dokumentierter Start-/Statusweg; **RUNTIME:** ein geplanter Start/Stop im neutralen Testsystem. | DEV_BESTANDEN; RUNTIME offen |
| **P18** | **Dokumentation/Bedienbarkeit:** Download- und Offline-Startanleitung stimmen mit genau dem getesteten Kandidaten überein; Fehler/Restbedarf sind auffindbar; Secrets und echte Kundendaten fehlen in Screenshots, Reports und Artefakten. | **DEV:** README/Offline-Anleitung/Paketprüfung; **RUNTIME:** ein tatsächlicher Benutzerablauf plus redigierter Nachweis. | DEV_BESTANDEN; RUNTIME offen |
| **P19** | **OPTIONAL: Lokales Ollama/pgvector:** Nur wenn DOM explizit einschaltet: 768D-Modell passend, lokale Adressen, Embedding-/Reranking-Fallback und Kennzeichnung „Ähnlichkeit ≠ verifizierte Antwort“. Keine automatische Modellinstallation. | **DEV:** K23-/K25-Tests vorhanden; **RUNTIME:** nur nach Betreiberentscheidung. **Kein Pflichtblocker** des Standard-Chats. | OPTIONAL_NICHT_GEPRUEFT |
| **P20** | **Abschlussgutachten:** Alle Pflichtpunkte sind nachgewiesen oder als Blocker entschieden, Befunde klassifiziert, P2 von DOM akzeptiert/abgelehnt, Kandidat/Plattform und Resultat dokumentiert. | **BETREIBER:** unterschriebenes bzw. ausdrücklich bestätigtes GO/NO-GO durch DOM. | OFFEN |

**Evidenz genügt**, wenn sie Kandidat/Plattform, überprüftes Soll, tatsächliches Ist und eine nachvollziehbare Quelle enthält (CI-Link, gezielter Testbericht, bereinigte Terminalausgabe, neutraler Screenshot). Ein bloßes „funktioniert“ ist kein Nachweis; komplette Rohdaten/Secrets sind nicht erwünscht.

## D. Ein einziger organisierter Prüfdurchlauf

### Phase 0 – Eingang / Freeze (vor Betriebsprüfung)

DOM legt **vorher** verbindlich fest: den o. g. Commit und sein unverändertes ZIP, das **eine** zu prüfende Referenz-Betriebssystem, isolierten oder neutralen Quellenbereich sowie den Umfang der optionalen Modellprüfung (Standard: aus). SHA-256 muss **vor dem Entpacken/Start** zum genauen heruntergeladenen Archiv passen. Bei bestehender Runtime vor einer Änderung Backup-/Rollback-Situation klären; niemals das laufende Produktivsystem ungefragt verändern.

Die lokale KI liest im DEV-Repository **nur noch fehlende** Code-Nachweise und vorhandene CI-Läufe. DOM erstellt das Review-Bündel. ChatGPT bewertet und führt P01–P20 zentral.

### Phase 1 – Ein Praxislauf (P02–P18)

1. Den offiziellen vorhandenen Starter auf dem festgelegten Zielsystem nutzen und Betriebs-/Portzustand ohne Secrets erfassen.
2. Auf **derselben** Browserseite eine neutrale Datei importieren und eine belegte Antwort mit Originalstelle abrufen.
3. Danach einmal **neun kleine gültige und eine ungültige** Datei auswählen; Fortschritt, Paginierung, Teilmeldung und Suchbarkeit erfolgreicher Dateien nachweisen.
4. Aus demselben Testmaterial zwei Anschlussfragen, eine unabhängige Themenfrage, „Neuer Chat“ und eine unbelegte Negativfrage ausführen.
5. Bewusste Quellen- und Sicherheitsgrenzen, kontrolliertes Verhalten bei Fehlern sowie Datenbestand/Start-Stop prüfen. Bereits vorhandene präzise DEV-Beweise **nicht erneut ausführen**.
6. P19 nur bei ausdrücklich genehmigter optionaler Modellaktivierung; ansonsten `OPTIONAL_NICHT_GEPRUEFT`.

**Keine zusätzlichen Tests** ohne klar benannten fehlenden Nachweis, sicherheitsrelevanten Befund oder ausdrückliche Betreiberentscheidung.

### Phase 2 – Einmalige Sammelbewertung

Jeder Befund erhält genau eine Art: **PRODUKTFEHLER**, **UMGEBUNGSPROBLEM**, **NACHWEIS_FEHLT** oder **BETREIBERENTSCHEIDUNG**; bei Produkt-/Sicherheitsfehlern zusätzlich Schweregrad:

- **P0:** z. B. offengelegte Secrets/Kundendaten, unzulässiger externer Zugriff, falscher Host, unerlaubte Änderungen. **Sofortiger Stopp, NO-GO bis gesondert behoben.**
- **P1:** z. B. Kern-Import/Index/Chat unter Soll, falsche Quellen oder irreführend grüne Sicherheitsprüfung. **Blockiert GO, vor weiterer abhängiger Prüfung gezielt beheben.**
- **P2:** z. B. kosmetische Texte, unkritische UX-/Dokudrift. **Dokumentieren; DOM entscheidet ausdrücklich Annahme oder Nacharbeit vor GO.**

Umgebungsprobleme und Nachweislücken dürfen **niemals** stillschweigend als bestandene Produktprüfung gelten. Dokumentierte `NICHT_ANWENDBAR`-Fälle benötigen DOM-Begründung.

### Phase 3 – Begrenzter Korrektur-/Nachtest und STOPP

**Maximal ein gebündelter Korrekturdurchgang und ein gezielter Nachtest** sind Bestandteil *dieses* Abnahmelaufs. Bei P0 wird die Prüfung unmittelbar abgebrochen; nach Sicherheitsklärung und bewusstem DOM-Beschluss kann ein gesonderter neuer Lauf beginnen.

Bei P1: nur betroffene Funktionen im bestehenden DEV-Repository korrigieren, gezielte CI-/isolierte Tests, neuer Commit/Quellpaket-Hash bei geänderter Runtime, dann **nur** betroffene Nachweise und direkte Abhängigkeiten erneut prüfen. Keine pauschale Dauerschleife.

**Danach ist der Lauf zwingend beendet** – entweder:
- **GO für lokalen Einbenutzer-Referenzbetrieb**: P01–P18 nachweislich erfüllt, keine offenen P0/P1, P2 durch DOM entschieden, P20 freigegeben.
- **NO-GO**: Ein Pflichtnachweis fehlt, Umgebung blockiert die Bewertung, P0/P1 sind offen oder DOM gibt nicht frei. Restpunkte erhalten einen konkreten neuen Bau-/Abnahmetermin **nur durch neue bewusste Entscheidung**, nicht als automatische Fortsetzung.
- **GO mit akzeptierten P2** ist nur bei ausdrücklicher, dokumentierter DOM-Entscheidung zulässig; keine Ausnahmen bei P0/P1 oder fehlenden Pflichtnachweisen.

Ein GO gilt **nur für den genannten Commit, die bewertete Konfiguration und das tatsächlich geprüfte Zielsystem**. Kein implizites GO für Windows/macOS, öffentliche Bereitstellung, Mehrbenutzerbetrieb oder optionale KI.

## E. Abschlussprotokoll – auszufüllen, nicht vorwegnehmen

| Feld | Wert / Status |
| --- | --- |
| Prüflauf-ID / Datum | **OFFEN** |
| Prüfkandidat (Commit/ZIP/Prüfsumme) | `3071f07651ec…` / siehe Abschnitt A; exakter Zielrechner-Hash **OFFEN** |
| Zielsystem / OS / Runtime-Pfad | **OFFEN – DOM** |
| Quellfixture (neutral, keine Kundendaten) | **OFFEN – DOM** |
| DEV-/CI-Nachweise übernommen | Quellpaket [40976973063](https://github.com/IMaugrenI/tof_local_knowledge/actions/runs/40976973063), GitHub-CI; konkrete Einzelnachweise je Pxx ergänzen |
| P01–P18 bewertete Ergebnisse | **OFFEN** |
| P19 Modelloption | `OPTIONAL_NICHT_GEPRUEFT`, solange nicht ausdrücklich gewählt |
| Befunde P0/P1/P2 + Art | **OFFEN** |
| Korrektur-/Nachtestrunde (max. 1) | **Noch nicht begonnen** |
| Restbedarf und von DOM angenommene P2 | **OFFEN** |
| Endentscheidung | **GO / NO-GO – offen** |
| DOM-Freigabe / Datum | **OFFEN** |

Das Abschlussgutachten nennt auch bei **NO-GO** alle geprüften und nicht geprüften Punkte, den exakten Restbedarf und erklärt den Vorgang für **geschlossen**. Kein verdecktes „nochmal alles testen“.

## F. Abgrenzung zum späteren Release

Der vorhandene ZIP-Kandidat ist **kein nach Blueprint 06 freigegebenes Produktions-Release-Bundle** und besitzt kein entsprechendes `RELEASE_MANIFEST.txt`. Die gesonderte spätere Release-/Deployfreigabe kann unter anderem Manifest, separates Backup/Restore, Migration, kontrollierten Recreate und Post-Deploy-Smokes verlangen. Diese Release-Bedingungen werden **nicht stillschweigend** zu neuen Anforderungen an die hier definierte **lokale Referenzabnahme** gemacht.

**Eine Liste. Ein Kandidat. Ein zusammenhängender Lauf. Höchstens ein gebündelter Nachtest. Dann GO oder NO-GO.**
