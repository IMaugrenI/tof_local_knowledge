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
- runtime entrypoint: `python3 run.py ...`
- compose file: `compose.full.yml`

## Default host ports

The internal Postgres service still listens on container port `5432`.

The public host port defaults to `55432` in `.env.example` to avoid colliding with an existing local Postgres installation on the host machine.

If `python3 run.py up` fails with a message like:

```text
Bind for 0.0.0.0:5432 failed: port is already allocated
```

then an older local `.env` probably still has:

```text
POSTGRES_PORT=5432
```

Change it to:

```text
POSTGRES_PORT=55432
```

Then run:

```bash
python3 run.py down
python3 run.py up
python3 run.py check
```

`DATABASE_URL` should continue to point to `postgres:5432` because service-to-service traffic inside Docker still uses the container port.

## Core idea

The runtime stack uses real database access, real file scans, real extraction, FTS search, and evidence-based QA without free-form answer generation.
