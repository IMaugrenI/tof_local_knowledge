# tof_local_knowledge

> English is the primary text in this repository. A German clone is available in `README_DE.md`.

On_prem local knowledge system for document indexing, search, and grounded question answering.

I built this repo to turn local files into searchable evidence and answers with visible source grounding.

## start_here

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

## cross_platform_wrappers

The supported runtime truth is `python run.py ...`.

Convenience wrappers now exist for multiple operating systems:

- Linux: `scripts/*.sh`
- Windows PowerShell: `scripts/*.ps1`
- macOS command launchers: `scripts/*.command`

Examples:

```bash
./scripts/setup.sh
pwsh ./scripts/setup.ps1
./scripts/setup.command
```

## what_this_repo_does

1. registers and scans local sources
2. extracts content from common document formats
3. translates raw extraction blocks into citable segments
4. stores searchable records in Postgres
5. answers questions from search hits instead of free_form guessing
6. can optionally use local Ollama and Open WebUI layers

## what_already_works

1. source scan into Postgres_backed document records
2. extraction helpers for txt, md, json, html, csv, eml, pdf, docx, and xlsx
3. canonical citable segments
4. full_text search over stored segments
5. grounded QA endpoint

## what_this_shows

1. hands_on Linux, Docker, and Postgres work
2. evidence_first document workflows
3. clear separation between raw input, index, and answer layers
4. product_minded design for local knowledge spaces
5. practical documentation and runtime discipline

## boundary

1. this is not the builder repo
2. this is not a cloud_first product
3. this is not a hidden remote sync system
4. this repo focuses on local or internal document spaces

## key_runtime_files

- `run.py`
- `tof_cli/`
- `compose.full.yml`
- `.env.example`
- `docs/13_python_cli_runtime.md`
- `docs/11_runtime_stack.md`
- `docs/commands.md`

## wrapper_sets

- Linux shell wrappers: `scripts/*.sh`
- Windows PowerShell wrappers: `scripts/*.ps1`
- macOS command launchers: `scripts/*.command`

## related_public_repos

- [`tof_local_builder`](https://github.com/IMaugrenI/tof_local_builder) — local AI builder stack
- [`tof_showcase`](https://github.com/IMaugrenI/tof-showcase) — public architecture entry point
- [`tof_v7_public_frame`](https://github.com/IMaugrenI/tof-v7-public-frame) — reduced V7 boundary frame
