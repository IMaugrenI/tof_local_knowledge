# Runtime Stack

## Aktiver Runtime-Stack
Für den echten Kernbetrieb ist `compose.full.yml` die maßgebliche Compose-Datei.

## Enthaltene Dienste
- postgres
- auth_api
- catalog_api
- ingest_api
- extractor_api
- search_api
- qa_api
- optional ollama
- optional open_webui

## Wichtige Pfade
- Runtime-Dockerfile: `services/_runtime_fastapi.Dockerfile`
- Runtime-Requirements: `services/_runtime_requirements.txt`
- Startscript: `scripts/start_full.sh`
- Checkscript: `scripts/check_full.sh`

## Kernidee
Der Runtime-Stack verwendet echte Datenbankzugriffe, echte Dateiscans, echte Extraktion, FTS-Suche und belegbasierte QA ohne freie Antwortgenerierung.
