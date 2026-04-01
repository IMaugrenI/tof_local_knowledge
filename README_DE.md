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

## Erster echter Lauf

1. `.env.example` nach `.env` kopieren
2. mindestens setzen:
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `LOCAL_SOURCE_ROOT_1`
3. Verzeichnisse vorbereiten:

```bash
bash scripts/bootstrap_dev.sh
```

4. Runtime-Stack starten:

```bash
bash scripts/start_full.sh
```

5. Health prüfen:

```bash
bash scripts/check_full.sh
```

## Wichtige Dokumente

- [`docs/00_product_scope.md`](docs/00_product_scope.md) — Produktgrenze
- [`docs/01_architecture.md`](docs/01_architecture.md) — Architekturüberblick
- [`docs/04_ingest_flow.md`](docs/04_ingest_flow.md) — Datei- und Ingestfluss
- [`docs/05_search_qa.md`](docs/05_search_qa.md) — Such- und QA-Konzept
- [`docs/11_runtime_stack.md`](docs/11_runtime_stack.md) — aktiver Runtime-Stack
- [`docs/12_first_run.md`](docs/12_first_run.md) — erster echter Lauf

## Verwandte öffentliche Repositories

- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — öffentlicher Architekturrahmen
- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — lokaler Builder-Stack
