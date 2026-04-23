# tof_local_knowledge

<p align="center">
  <img src="https://raw.githubusercontent.com/IMaugrenI/IMaugrenI/main/assets/banner/tof_local_knowledge_banner_clean.png" alt="tof_local_knowledge banner" width="100%" />
</p>

**Search local documents and get evidence-grounded answers**

An on-prem knowledge system for indexing documents, searching them, and answering questions from citable evidence instead of free-form guessing.

> English is the primary text in this repository. A German mirror is available in `README_DE.md`.

On-prem local knowledge system for document indexing, search, and grounded question answering.

## What this repo is

This repository is the public Ground repo in the product line.

## Who it is for

This repo is for people and teams who want local document indexing, inspectable search, and evidence-grounded answers instead of free-form guessing.

## What it is not

This repo is not a cloud-first product, not a hidden remote sync service, and not a general builder system.

## Where to go next

- `tof-showcase` — public architecture and product-line overview
- `tof_local_builder` — controlled generation from grounded input
- `local_case_organizer` — structure and export grounded material

## Why this repo exists

The main point of this repo is not just to make local data usable, but to produce answers that stay tied to visible evidence.

## Use this repo in the simplest way

If you want the shortest safe path, start here:

### Linux

```bash
bash scripts/start_here.sh
```

### Windows PowerShell

```powershell
pwsh ./scripts/start_here.ps1
```

### macOS

```bash
./scripts/start_here.command
```

That path runs:

1. setup
2. startup
3. health check

A beginner guide is available in `docs/00_beginner_quickstart.md`.

## What this repo does

1. registers and scans local sources
2. extracts content from common document formats
3. translates raw extraction blocks into citable segments
4. stores searchable records in Postgres
5. answers questions from search hits instead of free-form guessing
6. can optionally use local Ollama and Open WebUI layers

## What already works

1. source scan into Postgres-backed document records
2. extraction helpers for txt, md, json, html, csv, eml, pdf, docx, and xlsx
3. canonical citable segments
4. full-text search over stored segments
5. grounded QA endpoint

## My role in this repo

My role here is:

- architecture and evidence-boundary definition
- separation between raw input, index, search, and answer layers
- workflow design and runtime shape
- review and correction of generated output
- AI-assisted implementation under my direction

## Start here

Primary runtime entrypoint:

```bash
python run.py setup
python run.py up
python run.py check
```

Additional runtime commands:

```bash
python run.py status
python run.py doctor
python run.py down
```

## Cross-platform wrappers

The supported runtime truth is `python run.py ...`.

Supported convenience wrappers:

- Linux: `scripts/setup.sh`, `scripts/up.sh`, `scripts/check.sh`, `scripts/down.sh`, `scripts/status.sh`, `scripts/doctor.sh`, `scripts/start_here.sh`
- Windows PowerShell: `scripts/setup.ps1`, `scripts/up.ps1`, `scripts/check.ps1`, `scripts/down.ps1`, `scripts/status.ps1`, `scripts/doctor.ps1`, `scripts/start_here.ps1`
- macOS command launchers: `scripts/setup.command`, `scripts/up.command`, `scripts/check.command`, `scripts/down.command`, `scripts/status.command`, `scripts/doctor.command`, `scripts/start_here.command`

## What success looks like

A successful first run means:

- the local knowledge stack is running
- local source paths can be registered
- search and grounded answering are available

## Role in the public product line

Ground (evidence-based retrieval)

### Works standalone
Yes.

### Can be combined with
- `tof_local_builder` for processing grounded results
- `local_case_organizer` for structuring extracted evidence

### Not intended for
- accepting generated content as truth
- acting as a general-purpose builder system

## What this repo shows

1. architecture before implementation
2. evidence-first document workflows
3. clear separation between raw input, index, search, and answer layers
4. AI-assisted system work that still stays grounded and inspectable
5. documentation and runtime discipline

## Boundary

1. this is not the builder repo
2. this is not a cloud-first product
3. this is not a hidden remote sync system
4. this repo focuses on local or internal document spaces

## Key runtime files

- `run.py`
- `tof_cli/`
- `compose.full.yml`
- `.env.example`
- `docs/13_python_cli_runtime.md`
- `docs/11_runtime_stack.md`
- `docs/commands.md`

## Related public repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — local AI builder stack
- [`tof-showcase`](https://github.com/IMaugrenI/tof-showcase) — public architecture entry point
- [`tof-v7-public-frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduced V7 boundary frame
