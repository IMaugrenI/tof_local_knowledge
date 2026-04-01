# tof_local_knowledge

> Deutsch ist die Spiegelversion dieses Repositories. Der englische Primärtext liegt in `README.md`.

On-prem lokales Wissenssystem für Dokumenten-Indexierung, Suche und belegte Frage-Antwort.

## Kurzüberblick

- local-first / on-prem Wissens- und Dokumentensystem
- lokale Dateien bleiben lokal
- Mehrnutzerzugriff im lokalen oder internen Netz
- saubere Trennung zwischen Rohdaten, Extraktion, Index und Antwortschicht
- Antworten sollen auf lokaler Evidenz beruhen statt auf freier Vermutung

## Aktiver Runtime-Pfad

Der aktive Runtime-Pfad in diesem Repository ist:

- `compose.full.yml`
- `services/*/app/runtime.py`
- `docs/11_runtime_stack.md`
- `docs/12_first_run.md`

## Was im Repository bereits funktioniert

- Source-Scan in Postgres-gestützte Dokumentobjekte
- Extraktionshilfen für txt, md, json, html, csv, eml, pdf, docx und xlsx
- Übersetzung roher Extraktionsblöcke in kanonische, zitierbare Segmente
- Postgres-Volltextsuche über gespeicherte Segmente
- belegter QA-Endpoint, der auf Suchtreffern antwortet
- optional lokales Ollama und optionale Open-WebUI-Schicht

## Wofür dieses Repository da ist

Dieses Repository soll ein sauberes lokales Wissensprodukt für private / interne Dokumenträume werden:

- lokale Quellen registrieren
- lokale Pfade scannen
- Inhalte extrahieren
- Manifest und Katalog aufbauen
- mit Belegen suchen
- Fragen mit Quellenbezug beantworten

## Was dieses Repository nicht ist

- nicht ToF V7
- nicht das Builder-Repo
- kein cloud-first Produkt
- kein verstecktes Remote-Sync-System
- keine Behauptung, dass schon alles fertig ist

## Schnellstart

1. lokale Vorbereitung ausführen:

```bash
bash scripts/setup.sh
```

2. den Runtime-Stack starten:

```bash
bash scripts/up.sh
```

3. Health prüfen:

```bash
bash scripts/check.sh
```

## Befehle für den Betrieb

Nutze für den normalen Betrieb diese kleinen Befehle:

```bash
bash scripts/setup.sh
bash scripts/up.sh
bash scripts/check.sh
bash scripts/logs.sh
bash scripts/down.sh
```

Mehr Details:

- [`docs/commands.md`](docs/commands.md)
- [`docs/commands_DE.md`](docs/commands_DE.md)

## Wichtige Dokumente

- [`docs/00_product_scope.md`](docs/00_product_scope.md) — Produktgrenze
- [`docs/01_architecture.md`](docs/01_architecture.md) — Architekturüberblick
- [`docs/04_ingest_flow.md`](docs/04_ingest_flow.md) — Datei- und Ingestfluss
- [`docs/05_search_qa.md`](docs/05_search_qa.md) — Such- und QA-Konzept
- [`docs/11_runtime_stack.md`](docs/11_runtime_stack.md) — aktiver Runtime-Stack
- [`docs/12_first_run.md`](docs/12_first_run.md) — erster echter Lauf
- [`docs/commands.md`](docs/commands.md) — öffentliche Kommandos

## Verwandte öffentliche Repositories

- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — öffentlicher Architekturrahmen
- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler Builder-Stack
