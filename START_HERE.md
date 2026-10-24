# Start here

This is the shortest safe path for a first-time user.

> German version: [START_HERE_DE.md](START_HERE_DE.md)

## What this tool does

`tof_local_knowledge` indexes local documents, lets you search the indexed evidence, and can answer questions from retrieved evidence instead of guessing freely.

The safest first run uses only the synthetic demo files already included in the repository. A fresh clone defaults `LOCAL_SOURCE_ROOT_1` to `./demo/source_1`, so no private source path is needed for the first run.

## Requirements

- Python 3.11+ (`py` or `python` on Windows)
- Docker with Docker Compose
- a local browser
- enough disk space for Postgres and any optional local model layer you enable

## First start

### Linux

```bash
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
bash scripts/start_here.sh
```

### Windows PowerShell

```powershell
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
pwsh ./scripts/start_here.ps1
```

### macOS

```bash
git clone https://github.com/IMaugrenI/tof_local_knowledge.git
cd tof_local_knowledge
./scripts/start_here.command
```

The start-here path performs setup, starts the local stack, and checks service health.

## Check that it is running

Linux/macOS:

```bash
python3 run.py check
```

Then start/open the local UI:

```bash
python3 run.py ui
```

The UI is intended to stay local on `127.0.0.1:8785`. Docker-published service ports also default to `127.0.0.1` through `BIND_HOST=127.0.0.1`.

## Safe first test

Before using private documents, use the repository demo:

- source files: `demo/source_1/`
- example questions: `demo/questions.md`
- expected result shapes: `demo/expected_results.md`

Follow [docs/01_demo_flow.md](docs/01_demo_flow.md).

A successful demo should show the full chain:

```text
local file
  → scan
  → extraction
  → citable segment
  → search hit
  → grounded answer
  → visible citation
```

A question with no supporting evidence should remain clearly unsupported instead of being invented.

## Everyday commands

```bash
python3 run.py up
python3 run.py status
python3 run.py check
python3 run.py ui
python3 run.py down
```

If something is unclear:

```bash
python3 run.py doctor
```

## Before using real documents

Read [SECURITY.md](SECURITY.md).

Do not publish:

- real private documents
- screenshots of private sources
- credentials or `.env` values
- private paths, hostnames, or customer data

Use synthetic demo data for public issues and screenshots.

## What this tool is not

It is not:

- a cloud-first document service
- a guarantee that every answer is correct
- a substitute for professional/legal review
- a builder that is allowed to turn generated text into evidence automatically

## More detail

- [Beginner quickstart](docs/00_beginner_quickstart.md)
- [Demo flow](docs/01_demo_flow.md)
- [Validation checklist](docs/02_demo_validation_checklist.md)
- [Search and QA](docs/05_search_qa.md)
- [Runtime](docs/11_runtime_stack.md)
- [Commands](docs/commands.md)
