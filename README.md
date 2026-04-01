# tof_local_knowledge

> English is the primary text in this repository. A German clone is available in `README_DE.md`.

On-prem local knowledge system for document indexing, search, and grounded question answering.

## At a glance

- local-first / on-prem knowledge and document system
- local files stay local
- supports multi-user access inside a local or internal network
- separates raw data, extraction, index, and answer layers
- answers should be grounded in local evidence instead of free-form guessing

## Current runtime path

The active runtime path in this repository is:

- `compose.full.yml`
- `services/*/app/runtime.py`
- `docs/11_runtime_stack.md`
- `docs/12_first_run.md`

## What already works in the repository

- source scan into Postgres-backed document records
- extraction helpers for txt, md, json, html, csv, eml, pdf, docx, and xlsx
- translation of raw extraction blocks into canonical, citable segments
- Postgres full-text search over stored segments
- grounded QA endpoint that answers from search hits
- optional local Ollama and optional Open WebUI layer

## What this repository is for

This repository is meant to become a clean local knowledge product for private/internal document spaces:

- register local sources
- scan local paths
- extract contents
- build a manifest and catalog
- search with evidence
- answer questions with source references

## What this repository is not

- not ToF V7
- not the builder repo
- not a cloud-first product
- not a hidden remote sync system
- not a claim that everything is finished

## First run

1. copy `.env.example` to `.env`
2. set at least:
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `LOCAL_SOURCE_ROOT_1`
3. prepare directories:

```bash
bash scripts/bootstrap_dev.sh
```

4. start the runtime stack:

```bash
bash scripts/start_full.sh
```

5. check health:

```bash
bash scripts/check_full.sh
```

## Key docs

- [`docs/00_product_scope.md`](docs/00_product_scope.md) — product boundary
- [`docs/01_architecture.md`](docs/01_architecture.md) — architecture overview
- [`docs/04_ingest_flow.md`](docs/04_ingest_flow.md) — file and ingest flow
- [`docs/05_search_qa.md`](docs/05_search_qa.md) — search and QA concept
- [`docs/11_runtime_stack.md`](docs/11_runtime_stack.md) — active runtime stack
- [`docs/12_first_run.md`](docs/12_first_run.md) — first real run

## Related public repos

- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — public architectural frame
- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — local builder stack
