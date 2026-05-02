# Python CLI runtime

This repo has a Python-first runtime entrypoint.

## Primary Linux/macOS entrypoint

```bash
python3 run.py setup
python3 run.py up
python3 run.py check
python3 run.py status
python3 run.py doctor
python3 run.py down
```

## Wrapper availability

The Linux/macOS runtime truth is `python3 run.py ...`.

Supported convenience wrappers are limited to these files:

- Linux shell wrappers: `scripts/setup.sh`, `scripts/up.sh`, `scripts/check.sh`, `scripts/down.sh`, `scripts/status.sh`, `scripts/doctor.sh`
- Windows PowerShell wrappers: `scripts/setup.ps1`, `scripts/up.ps1`, `scripts/check.ps1`, `scripts/down.ps1`, `scripts/status.ps1`, `scripts/doctor.ps1`
- macOS command launchers: `scripts/setup.command`, `scripts/up.command`, `scripts/check.command`, `scripts/down.command`, `scripts/status.command`, `scripts/doctor.command`

## Goal

- one operational runtime entrypoint
- cross-platform start logic in Python
- compose remains the runtime truth
- shell scripts stay thin wrappers around `run.py`

## Current migration state

- `run.py` is available now
- `run.py` uses a `python3` shebang
- Linux shell wrappers already call `python3 run.py ...`
- `tof_cli/` contains the command and core runtime modules
- Windows and macOS wrapper sets are available for the primary commands
- older helper scripts are not part of the supported runtime surface

## Command summary

### setup

- creates `.env` from `.env.example` if missing
- prepares local runtime directories
- reports source root state

### up

- resolves the compose runtime profile
- starts the stack with Docker Compose

### check

- checks HTTP health endpoints for the main APIs

### status

- prints platform details
- prints compose file/profile state
- runs `docker compose ps`

### doctor

- verifies Docker presence and reachability
- checks source path readiness
- scans configured ports

### down

- stops the compose stack
