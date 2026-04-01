# Runtime Stack

## Active runtime stack
For the real core runtime, `compose.full.yml` is the authoritative compose file.

## Included services
- postgres
- auth_api
- catalog_api
- ingest_api
- extractor_api
- search_api
- qa_api
- optional ollama
- optional open_webui

## Important paths
- runtime Dockerfile: `services/_runtime_fastapi.Dockerfile`
- runtime requirements: `services/_runtime_requirements.txt`
- start script: `scripts/start_full.sh`
- check script: `scripts/check_full.sh`

## Core idea
The runtime stack uses real database access, real file scans, real extraction, FTS search, and evidence-based QA without free-form answer generation.
