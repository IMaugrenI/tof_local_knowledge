# tof_local_knowledge

<p align="center">
  <img src="https://raw.githubusercontent.com/IMaugrenI/IMaugrenI/main/assets/banner/tof_local_knowledge_banner_clean.png" alt="tof_local_knowledge banner" width="100%" />
</p>

**Lokale Dokumente durchsuchen und Antworten anhand sichtbarer Belege nachvollziehen.**

Local Knowledge hilft bei der Indexierung und Suche lokaler Dokumente sowie beim Erzeugen beleggestützter Antworten. Es richtet sich an Menschen und Teams, die **nachprüfbare Quellen statt unbelegter Freitextantworten** benötigen.

**Einstieg:** [Sicherer Schnellstart und Demo](START_HERE_DE.md) · [English README](README.md) · [ToF Systems Übersicht](https://github.com/IMaugrenI/tof-showcase)

**Quellpaket-Kandidat (B8/K8):** Die vorhandenen Windows-/Linux-/macOS-Starter lassen sich über den manuellen GitHub-Workflow **Source distribution candidate** oder `python scripts/build_source_candidate.py --output-dir dist` aus einem Git-Commit bündeln. Enthalten sind eine [Offline-Anleitung](docs/RELEASE_PACKAGE_DE.md) und eine SHA-256-Prüfsumme. **Noch kein freigegebenes Produkt-Release und kein nativer Installer; die Abnahme erfolgt erst nach dem Ausbau.**

## So sieht eine belegte Antwort aus

Die öffentliche Demo verwendet synthetische Dokumente aus `demo/source_1/`. Der Screenshot zeigt eine echte lokale Ansicht mit Suchtreffern, zitierter Antwort und verwendeten Dokumenten.

![Local Knowledge: belegte Antwort](assets/screenshots/knowledge-07-ui-grounded-answer-dark.png)

[Demo-Nachweise und Screenshots](docs/03_demo_evidence_screenshots.md) · [Beispiel ohne ausreichende Evidenz](assets/screenshots/knowledge-06-no-evidence-contract-number.png)

**Einordnung:** Dieses Repository ist das eigenständige **Ground**-Werkzeug. Es ist weder ein Cloud-Synchronisierungsdienst noch ein allgemeiner KI-Builder oder eine automatische Wahrheitsinstanz. Belegte Informationen und fehlende Evidenz bleiben unterscheidbar. Eine Verbindung mit anderen Werkzeugen ist möglich, wird aber nicht als bereits integriert vorausgesetzt.

## Neu im K1-Entwicklungsbranch

Die vorhandene lokale Browseroberfläche bietet jetzt einen Bereich **Quellen & Index** mit den registrierten Quellen, indexierten Dokumenten, offenen/fehlgeschlagenen/fehlenden Zuständen und dem letzten Scan. Eine Quellenauswahl übernimmt den Filter in die vorhandene Suche und Frageseite. Dies ist eine **lokale Einzelbenutzerübersicht**, keine neue Anmeldung oder durchgesetzte Mehrbenutzerberechtigung.

Der Scan bewahrt erfolgreiche Zustände unveränderter Dokumente, erkennt geänderte und fehlende Dateien und markiert bei unvollständigen Scans unbesuchte Dateien nicht fälschlich als fehlend. Die Suche schließt veraltete Indexzustände aus. Bei einem Extraktionsfehler bleiben frühere Segmente zur Wiederherstellung erhalten, werden aber nicht als aktuelle Belege ausgegeben.

Der angezeigte QA-Wert wird ausdrücklich als **unkalibrierte Heuristik** bezeichnet, nicht als Wahrscheinlichkeit einer richtigen Antwort. Grenzen stehen im [K1-Entwicklungs-PR](https://github.com/IMaugrenI/tof_local_knowledge/pull/16) und im [Code-Status](docs/10_build_status.md).

## Ausbau K2: Quellen mit einem Klick indexieren

Die vorhandene lokale Browseroberfläche bietet nun **„Konfigurierte Quelle indexieren“**. Diese ausdrücklich ausgelöste Aktion scannt nur den bereits über `LOCAL_SOURCE_ROOT_1` schreibgeschützt eingebundenen Quellordner (`/sources/source_1` innerhalb der bestehenden Container). Die Quellkennung ist `LOCAL_SOURCE_ID_1` oder standardmäßig `demo_source_1`.

Pro Klick werden höchstens 100 Dateien gescannt und höchstens acht neue/geänderte/erneut zu verarbeitende Dokumente extrahiert. Ergebnis, fehlgeschlagene Extraktionen und verbleibende Arbeit werden angezeigt; weitere Chargen können manuell gestartet werden. **Keine Hintergrundindexierung, keine neuen Dienste und keine Mehrbenutzerfreigabe.** Die Funktion ist für die bestehende lokale Einzelbenutzer-Nutzung vorgesehen.

## Ausbau K4 — Belegte Textstelle direkt ansehen

Suchtreffer und konkrete Belegreferenzen in Antworten bieten nun **„Textstelle ansehen“**. Die bestehende lokale Browseroberfläche liest das exakt referenzierte Segment und zeigt Quelle, Dokumentkennung, Zitierlabel sowie bis zu 2.000 Zeichen des Textausschnitts. Nur aktuell indexierte Dokumente aus aktivierten Quellen dürfen angezeigt werden. Fehlende, deaktivierte, fehlgeschlagene und noch offene Dokumente liefern keine aktuellen Belege.

Die Funktion ist ausschließlich **lesend und lokal für Einzelbenutzer**. Sie schafft weder einen neuen Login, eine Quellenberechtigungsprüfung noch eine allgemeine Freigabe für das Netzwerk. Bestehende `citations`- und `evidence_refs`-Felder bleiben erhalten.

## Ausbau K5 — Große Quellen schrittweise indexieren

Die Aktion **„Konfigurierte Quelle indexieren“** kann jetzt auch Dokumente hinter den ersten 100 Dateien erreichen. Der Scanner verarbeitet begrenzte 100-Dateien-Abschnitte und liefert einen Fortsetzungszeiger. Über die bestehende Browseroberfläche können weitere Chargen manuell gestartet oder der Dateidurchlauf zurückgesetzt werden. Pro Klick werden weiterhin höchstens acht Dokumente extrahiert. Unveränderte, bereits erfolgreich verarbeitete Dateien bleiben unberührt; einzelne dauerhaft fehlerhafte Dateien verhindern den Fortschritt zu späteren Abschnitten nicht.

**Wichtige Grenze:** Ein nicht mehr vorhandenes Dokument darf nur bei einem vollständig ausgeführten Scan ohne Seitenteilung als fehlend markiert werden. Bei aufgeteilten Durchläufen erfolgt bewusst kein solcher Abgleich. Es wurden weder neue Dienste noch weitere Quell-Mounts oder Mehrbenutzerrechte eingeführt.

## Ausbau K6 — Deutschsprachige Wissensfragen und Belegbewertung

Die bestehende QA-Suche verarbeitet deutsche Fragewörter und Umlaute bei einer **gezielten Stichwortersatzsuche** besser. Bleiben Frage und Stichwörter ohne Treffer, erfolgt zuletzt eine ausdrücklich markierte, breitere OR-Suche. Diese kann auch dann Fundstellen zeigen, wenn nur einzelne Begriffe passen. Der jeweilige Suchweg bleibt im Antwortpaket sichtbar.

Das zusätzliche Feld `evidence_signal` beschreibt lediglich den **Suchbefund** (Anzahl gefundener Textsegmente, unterschiedliche Dokumente, Suchstrategie). Es ist **keine Qualitätsprüfung des Inhalts und keine Wahrscheinlichkeit, dass eine Aussage wahr ist**. Die bestehende numerische `confidence` bleibt nur aus Kompatibilitätsgründen erhalten und ist weiterhin nicht kalibriert.

Suchergebnisse enthalten außerdem Seitenzahl, Segmenttyp und stabile Sortierung. Der ursprüngliche Quellenfilter und die Sperrung veralteter Indexstände bleiben erhalten. Es wird kein Cloud-Dienst, neuer Indexserver oder Mehrbenutzermodus eingeführt.

## K7 – Einheitliche lokale Adressen und verständliche Fehler

Die vorhandene Browseroberfläche verwendet für Quellen, Suche, Fragen, Belegansicht und Dokumentationslinks die bereits in `.env` definierten lokalen Ports. Ungültige Ports werden abgewiesen; fremde Hosts werden nicht aus Webanfragen übernommen.

Such- und Frageeingaben sind auf JSON-Objekte begrenzter Größe beschränkt. Unerreichbare Dienste, ungültige Anfragen und Verarbeitungsprobleme werden getrennt gemeldet. Die Oberfläche zeigt verständliche Hinweise in Deutsch und Englisch, während technische Details aufklappbar bleiben. Noch nicht indexierte oder fehlgeschlagene Dokumente werden in der vorhandenen Quellenübersicht hervorgehoben. Die standardmäßige lokale Einzelbenutzernutzung und die vorhandene Compose-Struktur bleiben verbindlich.

## Einfachster Einstieg

Wenn du den kürzesten sicheren Weg willst, starte hier:

### Linux

```bash
bash scripts/start_here.sh
```

### Windows PowerShell

```powershell
pwsh ./scripts/start_here.ps1
```

### macOS

```bash
./scripts/start_here.command
```

Dieser Pfad führt aus:

1. setup
2. startup
3. health check

Ein Einsteiger-Guide liegt in `docs/00_beginner_quickstart.md`.
Eine Doku-Übersicht liegt in `docs/README.md`.
Ein deutscher Doku-Spiegel liegt in `docs/README_DE.md`.

## Sichere Demo zuerst

Bevor du private oder wichtige Dokumente verwendest, teste den Stack mit den neutralen Demo-Quelldateien in `demo/source_1/`.

Nutze:

- `demo/source_1/` — synthetische lokale Quelldateien für sichere Tests
- `demo/questions.md` — Beispiel-Suchanfragen und grounded Fragen
- `demo/expected_results.md` — erwartete Ergebnisformen und Sicherheitshinweise
- `docs/01_demo_flow.md` — Schritt-für-Schritt-Demo-Ablauf vor echten Screenshots
- `docs/02_demo_validation_checklist_DE.md` — lokale Abnahmecheckliste vor Screenshots oder Release Notes

Öffentliche Screenshots sollten nur aus der echten lokalen UI oder echter lokaler API-Ausgabe mit neutralen Demo-Daten aufgenommen werden. Fake-Screenshots dürfen nicht als echte UI-Ausgabe dargestellt werden.

## Was dieses Repo macht

1. registriert und scannt lokale Quellen
2. extrahiert Inhalte aus gängigen Dokumentenformaten
3. übersetzt rohe Extraktionsblöcke in zitierbare Segmente
4. speichert durchsuchbare Datensätze in Postgres
5. beantwortet Fragen aus Suchtreffern statt freiem Raten
6. kann optional lokale Ollama- und Open-WebUI-Ebenen nutzen

## Was bereits funktioniert

1. Quellen-Scan in Postgres-gestützte Dokumentensätze
2. Extraktionshelfer für txt, md, json, html, csv, eml, pdf, docx und xlsx
3. kanonische zitierbare Segmente
4. Full-Text-Suche über gespeicherte Segmente
5. grounded QA-Endpunkt

## Rolle in der öffentlichen Produktlinie

Grundlage (evidenzbasierte Suche)

### Funktioniert allein
Ja.

### Kann kombiniert werden mit
- `tof_local_builder` zur Weiterverarbeitung evidenzgebundener Ergebnisse
- `local_case_organizer` zur Strukturierung extrahierter Inhalte

### Nicht gedacht für
- generierte Inhalte als Wahrheit zu übernehmen
- als allgemeines Builder-System zu dienen

## Meine Rolle in diesem Repo

Meine Rolle hier ist:

- Architektur und Evidenz-Grenzdefinition
- Trennung zwischen Rohinput, Index-, Such- und Antwort-Ebenen
- Workflow-Design und Runtime-Form
- Review und Korrektur erzeugter Ausgaben
- KI-gestützte Umsetzung unter meiner Führung

## Einstieg

Primärer Runtime-Einstieg für Linux/macOS:

```bash
python3 run.py setup
python3 run.py up
python3 run.py check
```

Weitere Runtime-Befehle für Linux/macOS:

```bash
python3 run.py status
python3 run.py doctor
python3 run.py down
```

Windows-Nutzer sollten normalerweise die unten genannten PowerShell-Wrapper verwenden.

## Plattform-Wrapper

Die unterstützte Runtime-Wahrheit für Linux/macOS ist `python3 run.py ...`.

Unterstützte Komfortstarter:

- Linux: `scripts/setup.sh`, `scripts/up.sh`, `scripts/check.sh`, `scripts/down.sh`, `scripts/status.sh`, `scripts/doctor.sh`, `scripts/start_here.sh`
- Windows PowerShell: `scripts/setup.ps1`, `scripts/up.ps1`, `scripts/check.ps1`, `scripts/down.ps1`, `scripts/status.ps1`, `scripts/doctor.ps1`, `scripts/start_here.ps1`
- macOS-Command-Starter: `scripts/setup.command`, `scripts/up.command`, `scripts/check.command`, `scripts/down.command`, `scripts/status.command`, `scripts/doctor.command`, `scripts/start_here.command`

## Erfolgszustand

Ein erfolgreicher erster Start bedeutet:

- der lokale Knowledge-Stack läuft
- lokale Quellenpfade können registriert werden
- Suche und grounded Answers sind verfügbar

## Was dieses Repo zeigt

1. Architektur vor Umsetzung
2. evidenzorientierte Dokumenten-Workflows
3. klare Trennung zwischen Rohinput, Index-, Such- und Antwort-Ebenen
4. KI-gestützte Systemarbeit, die trotzdem belegbar und prüfbar bleibt
5. Dokumentations- und Runtime-Disziplin

## Grenze

1. das ist nicht das Builder-Repo
2. das ist kein Cloud-first Produkt
3. das ist kein verstecktes Remote-Sync-System
4. dieses Repo konzentriert sich auf lokale oder interne Dokumentenräume

## Zentrale Runtime-Dateien

- `run.py`
- `tof_cli/`
- `compose.full.yml`
- `.env.example`
- `docs/00_beginner_quickstart.md`
- `docs/01_demo_flow.md`
- `docs/02_demo_validation_checklist_DE.md`
- `docs/13_python_cli_runtime.md`
- `docs/11_runtime_stack.md`
- `docs/commands.md`

## Verwandte öffentliche Repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler KI-Builder-Stack
- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — öffentlicher Architektur-Einstieg
- [`tof-v7-public-frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduzierter V7-Grenzrahmen
