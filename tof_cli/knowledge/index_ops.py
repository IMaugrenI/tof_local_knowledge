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


def index_configured_source() -> dict[str, object]:
    """Run one explicit index batch; never deletes or rewrites source files."""
    env = read_env()
    source_id = env.get("LOCAL_SOURCE_ID_1", "demo_source_1").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", source_id):
        return {"status": "error", "detail": "invalid_local_source_id"}
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
            {"source_id": source_id, "root_path": SOURCE_CONTAINER_PATH,
             "include_hidden": False, "limit_files": MAX_FILES_SCANNED},
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
                    {"source_id": source_id, "root_path": SOURCE_CONTAINER_PATH,
                     "document_id": row["document_id"],
                     "relative_path": row["relative_path"], "persist": True},
                )
                if response.get("status") != "ok" or not response.get("segment_count", 0):
                    failed.append({"path": row["relative_path"], "detail": "no_extractable_text"})
                else:
                    processed += 1
            except (OSError, urllib.error.URLError, ValueError) as exc:
                failed.append({"path": row["relative_path"], "detail": type(exc).__name__})
        return {
            "status": "partial" if failed else "ok",
            "source_id": source_id,
            "scan_counts": scan.get("counts", {}),
            "files_scanned": scan.get("files_scanned", 0),
            "scan_complete": bool(scan.get("scan_complete")),
            "indexed_this_pass": processed,
            "failed": failed,
            "remaining_in_sample": max(0, len(candidates) - MAX_EXTRACTED_PER_CLICK),
            "batch_size": MAX_EXTRACTED_PER_CLICK,
            "message": "Run another batch if documents are still pending.",
        }
    except (OSError, urllib.error.URLError, ValueError) as exc:
        return {"status": "error", "detail": type(exc).__name__}
