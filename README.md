# tof_local_knowledge

> English is the primary text in this repository. A German clone is available in `README_DE.md`.
> Design reasoning: see `docs/product/WHY.md`. A German clone is available in `docs/product/WHY_DE.md`.
> Product entry notes: see `docs/product/START_HERE.md` and `docs/product/REPO_NOTE.md`.

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

## Quick start

1. prepare local setup:

```bash
bash scripts/setup.sh
```

2. start the runtime stack:

```bash
bash scripts/up.sh
```

3. check health:

```bash
bash scripts/check.sh
```

## Operator commands

Use the small public command surface for normal operation:

```bash
bash scripts/setup.sh
bash scripts/up.sh
bash scripts/check.sh
bash scripts/logs.sh
bash scripts/down.sh
```

More details:

- [`docs/commands.md`](docs/commands.md)
- [`docs/commands_DE.md`](docs/commands_DE.md)
- [`docs/product/START_HERE.md`](docs/product/START_HERE.md)
- [`docs/product/WHY.md`](docs/product/WHY.md)
- [`docs/product/WHY_DE.md`](docs/product/WHY_DE.md)
- [`docs/product/REPO_NOTE.md`](docs/product/REPO_NOTE.md)

## Key docs

- [`docs/00_product_scope.md`](docs/00_product_scope.md) — product boundary
- [`docs/01_architecture.md`](docs/01_architecture.md) — architecture overview
- [`docs/04_ingest_flow.md`](docs/04_ingest_flow.md) — file and ingest flow
- [`docs/05_search_qa.md`](docs/05_search_qa.md) — search and QA concept
- [`docs/11_runtime_stack.md`](docs/11_runtime_stack.md) — active runtime stack
- [`docs/12_first_run.md`](docs/12_first_run.md) — first real run
- [`docs/commands.md`](docs/commands.md) — public command surface

## Related public repos

- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — public architectural frame
- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — local builder stack
