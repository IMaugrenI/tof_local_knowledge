# tof_local_knowledge

<p align="center">
  <img src="https://raw.githubusercontent.com/IMaugrenI/IMaugrenI/main/assets/banner/tof_local_knowledge_banner_clean.png" alt="tof_local_knowledge banner" width="100%" />
</p>

> Die englische Hauptfassung liegt in `README.md`.

**Lokales Wissenssystem für Suche und evidenzbasierte Antworten**

Ein On-Prem-System für Dokumenten-Indexierung, Suche und belegte Antworten statt freiem Raten.

On-prem lokales Wissenssystem für Dokumenten-Indexierung, Suche und grounded Answers.

## Was dieses Repo ist

Dieses Repository ist das öffentliche **Ground**-Repo in der Produktlinie.

## Für wen es gedacht ist

Dieses Repo ist für Menschen und Teams, die lokale Dokumenten-Indexierung, prüfbare Suche und evidenzgebundene Antworten statt freiem Raten wollen.

## Was es nicht ist

Dieses Repo ist kein Cloud-first Produkt, kein versteckter Remote-Sync-Dienst und kein allgemeines Builder-System.

## Wohin du als Nächstes gehen kannst

- `tof-showcase` — öffentlicher Architektur- und Produktlinien-Überblick
- `tof_local_builder` — kontrollierte Generierung aus grounded Input
- `local_case_organizer` — grounded Material strukturieren und exportieren

## Warum dieses Repo existiert

Der Hauptpunkt dieses Repos ist nicht nur, lokale Daten nutzbar zu machen, sondern Antworten zu erzeugen, die an sichtbare Evidenz gebunden bleiben.

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

Primärer Runtime-Einstieg:

```bash
python run.py setup
python run.py up
python run.py check
```

Weitere Runtime-Befehle:

```bash
python run.py status
python run.py doctor
python run.py down
```

## Plattform-Wrapper

Die unterstützte Runtime-Wahrheit ist `python run.py ...`.

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
- `docs/13_python_cli_runtime.md`
- `docs/11_runtime_stack.md`
- `docs/commands.md`

## Verwandte öffentliche Repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler KI-Builder-Stack
- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — öffentlicher Architektur-Einstieg
- [`tof-v7-public-frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduzierter V7-Grenzrahmen
