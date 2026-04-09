# Python CLI runtime

This repo now has a Python-first runtime entrypoint.

## primary entrypoint

```bash
python run.py setup
python run.py up
python run.py check
python run.py status
python run.py doctor
python run.py down
```

## goal

- one operational runtime entrypoint
- cross-platform start logic in Python
- compose remains the runtime truth
- shell scripts can become thin wrappers later

## current migration state

- `run.py` is available now
- `tof_cli/` contains the new command and core runtime modules
- legacy shell scripts still remain for backward compatibility during transition

## command summary

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
