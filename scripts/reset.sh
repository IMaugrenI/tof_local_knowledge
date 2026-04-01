#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "WARNING: reset.sh is destructive."
echo "It stops the stack, removes local service data, and clears derived/export storage."

docker compose -f compose.full.yml down -v --remove-orphans || true
rm -rf data/postgres data/ollama storage/derived storage/previews storage/exports
bash scripts/bootstrap_dev.sh

echo "Knowledge reset finished."
