# tof_local_knowledge

> Die englische Hauptfassung liegt in `README.md`.

On-prem lokales Wissenssystem für Dokumenten-Indexierung, Suche und belegte Antworten.

Dieses Repository ist ein öffentlicher Beleg für evidenzorientierte KI-gestützte Systemarbeit in lokalen Dokumentenräumen.

Ich stelle dieses Repo nicht als klassischen Beweis für manuell Zeile für Zeile geschriebenen Code dar. Ich stelle es als Beleg dafür dar, dass aus Architektur, Evidenzgrenzen, Orchestrierung und Review in einem KI-gestützten Workflow ein konkretes belegtes System entstehen kann.

## Warum dieses Repo existiert

Der Hauptpunkt dieses Repos ist nicht nur, lokale Daten nutzbar zu machen, sondern Antworten zu erzeugen, die an sichtbare Evidenz gebunden bleiben.

Evidenzbasiertes Arbeiten ist mir wichtig, weil ich mich nicht auf Wirkung, Gefühl oder schöne Behauptungen verlassen will. Ich will Antworten, die wirklich tragen, weil sie mit Quellmaterial verbunden bleiben.

## Meine Rolle in diesem Repo

Meine Rolle hier ist:

- Architektur und Evidenz-Grenzdefinition
- Trennung zwischen Rohinput, Index-, Such- und Antwort-Ebenen
- Workflow-Design und Runtime-Form
- Review und Korrektur erzeugter Ausgaben
- KI-gestützte Umsetzung unter meiner Führung

Die konkrete Repo-Oberfläche ist stark KI-gestützt entstanden. Mein Anteil liegt in der Struktur dahinter: warum Antworten an Evidenz gebunden bleiben, warum Extraktion und Index getrennt sind und was als zulässige belegte Ausgabe gilt.

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

- Linux: `scripts/setup.sh`, `scripts/up.sh`, `scripts/check.sh`, `scripts/down.sh`, `scripts/status.sh`, `scripts/doctor.sh`
- Windows PowerShell: `scripts/setup.ps1`, `scripts/up.ps1`, `scripts/check.ps1`, `scripts/down.ps1`, `scripts/status.ps1`, `scripts/doctor.ps1`
- macOS Command-Starter: `scripts/setup.command`, `scripts/up.command`, `scripts/check.command`, `scripts/down.command`, `scripts/status.command`, `scripts/doctor.command`

Beispiele:

```bash
./scripts/setup.sh
pwsh ./scripts/setup.ps1
./scripts/setup.command
```

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
- `docs/13_python_cli_runtime.md`
- `docs/11_runtime_stack.md`
- `docs/commands.md`

## Verwandte öffentliche Repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler KI-Builder-Stack
- [`tof_showcase`](https://github.com/IMaugrenI/tof-showcase) — öffentlicher Architektur-Einstieg
- [`tof_v7_public_frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduzierter V7-Grenzrahmen
