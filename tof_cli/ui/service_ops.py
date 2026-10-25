"""Local-only UI port configuration and bounded JSON request validation.

No new server or access policy is introduced. The existing UI still proxies only
to fixed loopback hosts with ports from the repository's .env configuration.
"""
from __future__ import annotations

import json
from typing import BinaryIO, Mapping

PORTS = {
    "search": ("SEARCH_API_PORT", 8105, "/search"),
    "answer": ("QA_API_PORT", 8106, "/answer"),
    "sources": ("CATALOG_API_PORT", 8102, "/sources/status"),
    "evidence": ("SEARCH_API_PORT", 8105, "/evidence"),
    "openwebui": ("OPENWEBUI_PORT", 3000, ""),
    "search_docs": ("SEARCH_API_PORT", 8105, "/docs"),
    "qa_docs": ("QA_API_PORT", 8106, "/docs"),
    "catalog_docs": ("CATALOG_API_PORT", 8102, "/docs"),
}
MAX_JSON_BYTES = 16_384


def configured_targets(env: Mapping[str, str]) -> dict[str, str]:
    """Resolve ports without accepting client-provided hosts, paths or schemes."""
    result = {}
    for name, (key, default, path) in PORTS.items():
        raw = env.get(key, str(default))
        if not raw or not raw.isascii() or not raw.isdecimal():
            raise ValueError(f"invalid_local_port:{key}")
        port = int(raw)
        if not 1 <= port <= 65535:
            raise ValueError(f"invalid_local_port:{key}")
        result[name] = f"http://127.0.0.1:{port}{path}"
    return result


def parse_bounded_json(stream: BinaryIO, content_length: str) -> dict[str, object]:
    """Strict JSON-only object payload; refuse unlimited or malformed request bodies."""
    try:
        count = int(content_length)
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid_content_length") from exc
    if count < 1 or count > MAX_JSON_BYTES:
        raise ValueError("invalid_request_size")
    raw = stream.read(count)
    if len(raw) != count:
        raise ValueError("incomplete_request")
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid_json") from exc
    if not isinstance(parsed, dict):
        raise ValueError("json_object_required")
    return parsed


def classify_error(error: str) -> str:
    """A small stable set of end-user problems, not raw infrastructure details."""
    if error in {"source_status_unavailable", "request_failed", "service_unavailable"}:
        return "service_unavailable"
    if error.startswith("http_error_4") or error in {
        "invalid_json", "invalid_request_size", "invalid_content_length",
        "json_object_required", "incomplete_request",
    }:
        return "invalid_request"
    if error.startswith("invalid_local_port:") or error == "invalid_local_port":
        return "invalid_configuration"
    return "processing_error"
