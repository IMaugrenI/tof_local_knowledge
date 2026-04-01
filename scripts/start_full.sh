#!/usr/bin/env bash
set -euo pipefail

bash scripts/bootstrap_dev.sh
docker compose -f compose.full.yml up --build -d
