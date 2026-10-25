"""Explicit, bounded indexing of the single configured read-only source mount.

Only the host-side local control UI calls this helper. Client requests cannot
choose container paths or source IDs. Reuses existing ingest/extractor services.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from tof_cli.core.env_ops import read_env
from tof_cli.knowledge.source_spaces import resolve_source_space

SOURCE_CONTAINER_PATH = "/sources/source_1"
MAX_FILES_SCANNED = 100
MAX_EXTRACTED_PER_CLICK = 8


def _local_post(url: str, payload: dict[str, object], *, timeout: float = 30) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def index_configured_source(start_after: str | None = None, space_id: str | None = None) -> dict[str, object]:
    """Run one explicit index batch; never deletes or rewrites source files."""
    env = read_env()
    try:
        space = resolve_source_space(env, space_id)
    except ValueError as exc:
        return {"status": "error", "detail": str(exc)}
    source_id = str(space["id"])
    container_root = str(space["container_path"])
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", source_id):
        return {"status": "error", "detail": "invalid_local_source_id"}
    if start_after is not None and (
        not isinstance(start_after, str) or len(start_after) > 2048
        or start_after.startswith("/") or "\\x00" in start_after
        or "\\" in start_after or ".." in start_after.split("/")
    ):
        return {"status": "error", "detail": "invalid_scan_cursor"}
    if env.get("BIND_HOST", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        return {"status": "error", "detail": "local_only_indexing"}

    def local_port(name: str, default: str) -> int:
        value = int(env.get(name, default))
        if not 1 <= value <= 65535:
            raise ValueError("invalid_port")
        return value

    try:
        ingest_port = local_port("INGEST_API_PORT", "8103")
        extractor_port = local_port("EXTRACTOR_API_PORT", "8104")
        scan = _local_post(
            f"http://127.0.0.1:{ingest_port}/scan/run",
            {"source_id": source_id, "root_path": container_root,
             "include_hidden": False, "limit_files": MAX_FILES_SCANNED,
             "start_after": start_after},
        )
        if scan.get("status") != "ok":
            return {"status": "error", "detail": scan.get("detail", "scan_failed")}
        candidates = sorted(
            (
                row for row in scan.get("sample_documents", [])
                if row.get("scan_status") in {"new", "changed", "retry"}
            ),
            key=lambda row: (
                {"new": 0, "changed": 0, "retry": 1}[row["scan_status"]],
                row["relative_path"],
            ),
        )
        processed = 0
        failed = []
        for row in candidates[:MAX_EXTRACTED_PER_CLICK]:
            try:
                response = _local_post(
                    f"http://127.0.0.1:{extractor_port}/extract/file",
                    {"source_id": source_id, "root_path": container_root,
                     "document_id": row["document_id"],
                     "relative_path": row["relative_path"], "persist": True},
                )
                if response.get("status") != "ok" or not response.get("segment_count", 0):
                    failed.append({"path": row["relative_path"], "detail": "no_extractable_text"})
                else:
                    processed += 1
            except (OSError, urllib.error.URLError, ValueError) as exc:
                failed.append({"path": row["relative_path"], "detail": type(exc).__name__})
        remaining = max(0, len(candidates) - MAX_EXTRACTED_PER_CLICK)
        # Keep the same page while newer files remain unfinished. Once a
        # page contains only failed retries, allow moving on rather than
        # letting a permanently unreadable file block all later pages.
        fresh_remaining = any(
            row.get("scan_status") in {"new", "changed"}
            for row in candidates[MAX_EXTRACTED_PER_CLICK:]
        )
        next_cursor = start_after if fresh_remaining else scan.get("next_cursor")
        return {
            "status": "partial" if failed else "ok",
            "source_id": source_id,
            "source_label": space["label"],
            "scan_counts": scan.get("counts", {}),
            "files_scanned": scan.get("files_scanned", 0),
            "scan_complete": bool(scan.get("scan_complete")),
            "indexed_this_pass": processed,
            "failed": failed,
            "remaining_in_sample": remaining,
            "next_cursor": next_cursor,
            "page_has_more": bool(scan.get("next_cursor") or fresh_remaining),
            "reconciliation_performed": bool(scan.get("reconciliation_performed", False)),
            "batch_size": MAX_EXTRACTED_PER_CLICK,
            "message": "Run another batch if documents are still pending.",
        }
    except (OSError, urllib.error.URLError, ValueError) as exc:
        return {"status": "error", "detail": type(exc).__name__}
