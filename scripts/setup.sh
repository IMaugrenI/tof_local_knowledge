#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

bash scripts/bootstrap_dev.sh

echo
echo "Knowledge setup prepared."
echo "Check or set these values in .env before starting:"
echo "- POSTGRES_PASSWORD"
echo "- DATABASE_URL"
echo "- LOCAL_SOURCE_ROOT_1"
echo
echo "Next steps:"
echo "bash scripts/up.sh"
echo "bash scripts/check.sh"
