# Architecture

## Functional chain
1. see source
2. scan source
3. register file object
4. extract content
5. translate and normalize extraction
6. catalog document segments
7. search
8. answer with evidence

## Technical services
- postgres
- auth_api
- catalog_api
- ingest_api
- extractor_api
- search_api
- qa_api
- optional ollama
- optional open_webui

## Architecture principles
- Docker-first
- Postgres-only
- clear service boundaries
- API and contract thinking
- fail-closed
- append-only audit thinking
- read is not the same as merely seen
- answer only with evidence or uncertainty
- Open WebUI as UI only, not a truth layer

## Important edge
The QA layer must never answer directly from raw files. It must work through catalog, segments, and source references.
