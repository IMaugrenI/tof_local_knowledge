"""Bounded user-approved file copies into the configured read-only source mount."""
from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
import tempfile
from pathlib import Path, PurePosixPath

from tof_cli.core.env_ops import read_env
from tof_cli.knowledge.source_ops import source_root_from_env

SUPPORTED = {".txt", ".md", ".log", ".py", ".rst", ".ini", ".cfg",
             ".yaml", ".yml", ".json", ".htm", ".html", ".csv", ".eml",
             ".pdf", ".docx", ".xlsx"}
MAX_FILES = 4
MAX_TOTAL_BYTES = 16 * 1024 * 1024
MAX_FILE_BYTES = 12 * 1024 * 1024
IMPORT_SUBDIR = "Importierte_Dateien"


def _relative_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not 1 <= len(value) <= 600 or "\\" in value:
        raise ValueError("invalid_filename")
    path = PurePosixPath(value)
    if (path.is_absolute() or len(path.parts) > 12
            or any(part in {".", ".."} or part.startswith(".")
                   or ":" in part or any(ord(c) < 32 for c in part)
                   for part in path.parts)):
        raise ValueError("invalid_filename")
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError("unsupported_file_type")
    return path


def _root() -> Path:
    env = read_env()
    if not env.get("LOCAL_SOURCE_ROOT_1", "").strip():
        raise ValueError("source_root_not_configured")
    root = source_root_from_env(env).resolve()
    if not root.is_dir():
        raise ValueError("source_root_unavailable")
    return root


def _save(root: Path, path: PurePosixPath, content: bytes) -> None:
    parent = root / IMPORT_SUBDIR
    for name in path.parts[:-1]:
        if parent.is_symlink():
            raise ValueError("unsafe_destination")
        parent.mkdir(mode=0o700, exist_ok=True)
        parent = parent / name
    if parent.is_symlink():
        raise ValueError("unsafe_destination")
    parent.mkdir(mode=0o700, exist_ok=True)
    target = parent / path.name
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError("unsafe_destination")
    if not parent.resolve().is_relative_to(root):
        raise ValueError("invalid_source_boundary")
    fd, staging = tempfile.mkstemp(prefix=".tof_import_", dir=parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.chmod(staging, 0o600)
        if target.is_symlink():
            raise ValueError("unsafe_destination")
        os.replace(staging, target)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def import_selected_files(items: list[dict[str, str]]) -> dict[str, object]:
    """User submits only explicitly selected files. Never browse the host disk."""
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_FILES:
        raise ValueError("invalid_file_count")
    root = _root()
    validated: list[tuple[PurePosixPath, bytes]] = []
    total = 0
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("invalid_upload")
        path = _relative_path(item.get("name", ""))
        try:
            content = base64.b64decode(item.get("data", ""), validate=True)
        except (ValueError, binascii.Error, TypeError) as exc:
            raise ValueError("invalid_file_data") from exc
        total += len(content)
        if len(content) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise ValueError("upload_too_large")
        validated.append((path, content))
    for path, content in validated:
        _save(root, path, content)
    source_id = "space_" + hashlib.sha256(IMPORT_SUBDIR.encode()).hexdigest()[:16]
    return {"status": "ok", "copied": len(validated),
            "source_id": source_id, "source_label": IMPORT_SUBDIR,
            "requires_index": True, "mode": "manual_snapshot"}
