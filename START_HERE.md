# Start here

This is the shortest safe path from a fresh clone to your first answer from local documents.

> German version: [START_HERE_DE.md](START_HERE_DE.md)

## What this product is for

Add documents on your computer, search them, and ask questions about what they contain.

The important rule is simple: **answers should stay tied to visible sources**. If the documents do not support an answer, ToF should say that instead of inventing one.

The first run uses only the synthetic demo documents included in this repository. You do not need to point ToF at private files just to try it.

## What you need

- Python 3.11+ (`py` or `python` on Windows)
- Docker with Docker Compose
- a local browser
- enough local disk space for the document index and optional local AI model

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

The first run prepares the local environment, starts it, and checks whether the important parts are ready.

Open the local page with:

```bash
python3 run.py ui
```

## Your first useful result

Use the bundled demo documents and ask one of the example questions from `demo/questions.md`.

A successful result means:

- you get an answer based on the demo documents
- the answer shows which source material it used
- you can open the matching passages
- a question that is not supported by the documents stays visibly unsupported

You do not need to understand the internal indexing or service layout to use the browser page.

## If nothing is found

That is not automatically an error.

Try:

1. different search words
2. checking whether the document was added
3. asking a narrower question

If the local environment itself is unavailable, open **Setup & technical details → Find problems**.

From the terminal:

```bash
python3 run.py doctor
```

## Before using real documents

The demo is intentionally synthetic. Before adding private documents, read [SECURITY.md](SECURITY.md).

The normal local configuration binds the browser-facing services to this computer by default. Do not publish private documents, screenshots, local paths, credentials or generated answers containing sensitive information.

## Stop and come back later

Stop with:

```bash
python3 run.py down
```

Later:

```bash
python3 run.py up
python3 run.py ui
```

Your local index and configuration remain local unless you remove them yourself.

## Real-life example

See [docs/USER_JOURNEY.md](docs/USER_JOURNEY.md) for a complete question → answer → source journey plus a no-evidence example.

## More detail

- [Beginner quickstart](docs/00_beginner_quickstart.md)
- [Demo flow](docs/01_demo_flow.md)
- [Validation checklist](docs/02_demo_validation_checklist.md)
- [Search and answers](docs/05_search_qa.md)
- [Technical runtime](docs/11_runtime_stack.md)
- [Commands](docs/commands.md)
