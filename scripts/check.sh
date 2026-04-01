#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://127.0.0.1:${AUTH_API_PORT:-8101}/health
curl -fsS http://127.0.0.1:${CATALOG_API_PORT:-8102}/health
curl -fsS http://127.0.0.1:${INGEST_API_PORT:-8103}/health
curl -fsS http://127.0.0.1:${EXTRACTOR_API_PORT:-8104}/health
curl -fsS http://127.0.0.1:${SEARCH_API_PORT:-8105}/health
curl -fsS http://127.0.0.1:${QA_API_PORT:-8106}/health
