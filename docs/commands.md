# Commands

> English is the primary text in this document. A German mirror is available in `commands_DE.md`.

This repository exposes a small public operator path so local startup and shutdown stay easy to understand.

## Fastest beginner path

If you want the shortest safe path:

```bash
bash scripts/start_here.sh
```

Equivalent entry points:

- PowerShell: `pwsh ./scripts/start_here.ps1`
- macOS: `./scripts/start_here.command`

That path runs setup, startup, and health check in the expected order.

## Direct Linux/macOS runtime path

```bash
python3 run.py setup
python3 run.py up
python3 run.py check
python3 run.py status
python3 run.py down
```

## Browser control path

If you want a simpler local control surface in the browser:

```bash
python3 run.py ui
```

That path opens a local page with:

- large buttons for setup, start, check, status, doctor, and stop
- direct links to the main local pages
- a local search form
- a grounded-answer form

## Standard command flow

```bash
bash scripts/setup.sh
bash scripts/up.sh
bash scripts/check.sh
bash scripts/logs.sh
bash scripts/down.sh
```

## Commands

- `bash scripts/start_here.sh` — beginner path that runs setup, up, and check in sequence
- `python3 run.py ui` — local browser control surface for startup, search, and grounded answer
- `bash scripts/setup.sh` — prepare `.env` and local directories
- `bash scripts/up.sh` — start the full stack through the public wrapper
- `bash scripts/check.sh` — run health checks for the live stack
- `bash scripts/logs.sh` — follow compose logs
- `bash scripts/pull.sh` — pull upstream images where available
- `bash scripts/down.sh` — stop the stack cleanly without deleting data
- `bash scripts/restart.sh` — restart through the public wrappers
- `bash scripts/reset.sh` — destructive reset for local service data and derived/export storage

## Browser UI notes

The current browser UI can directly call the local:

- search endpoint `POST /search`
- grounded-answer endpoint `POST /answer`

The UI also links to:

- Open WebUI
- search API docs
- QA API docs
- catalog API docs

## Safety markers

- SAFE: `start_here`, `setup`, `check`, `status`, `doctor`, `down`, `python3 run.py ui`
- ADVANCED: `logs`, `pull`, `restart`
- DESTRUCTIVE: `reset`

## Notes

- Linux shell wrappers call `python3 run.py ...`
- `down.sh` is non-destructive by default
- `reset.sh` is the destructive path and should be used deliberately
