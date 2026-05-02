# Third-party components

This document lists important third-party components used by `tof_local_knowledge` or referenced by its optional runtime profiles.

It is not a complete legal inventory. The canonical license terms are the upstream projects and package metadata.

## Core runtime

- Python — runtime language
- FastAPI — service API framework
- Uvicorn — ASGI server for local services
- psycopg / PostgreSQL client libraries — database access
- PostgreSQL — local database engine
- pgvector — PostgreSQL vector extension image used by the Compose stack

## Document parsing helpers

Depending on file type and installed dependencies, the extractor layer can use Python libraries for formats such as:

- plain text
- Markdown
- JSON
- HTML
- CSV
- EML
- PDF
- DOCX
- XLSX

See `services/_runtime_requirements.txt` and project code for the exact Python package set used by this repository version.

## Optional local AI/UI layers

The Compose stack includes optional profiles for:

- Ollama — local model runtime
- Open WebUI — optional local browser interface connected to Ollama

These profiles are optional and separate from the default no-LLM demo path.

## Container images

The default Compose stack references public container images, including:

- `pgvector/pgvector:pg17`
- `ollama/ollama:latest` when the `llm` profile is enabled
- `ghcr.io/open-webui/open-webui:main` when the optional UI profile is enabled

Image licenses, bundled components, and update policies are controlled by their upstream projects.

## Local browser UI

The lightweight `python3 run.py ui` browser UI is served by this repository itself and uses plain HTML, CSS, and JavaScript from `tof_cli/ui/app.py`.

It does not require an external frontend framework.

## Safety note

Do not upload private documents, `.env` values, source folders, generated database files, or private screenshots when reporting issues or publishing demos.
Use `demo/source_1/` for public reproduction and screenshots.
