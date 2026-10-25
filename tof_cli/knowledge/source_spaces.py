"""Read-only choices for logical sources inside the configured Compose source mount.

The existing Docker mount remains /sources/source_1. Operators can organize
multiple spaces as subfolders without introducing new binds or stack instances.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

MAX_SPACES = 50


def discover_source_spaces(env: dict[str, str]) -> dict[str, object]:
    base_id = env.get("LOCAL_SOURCE_ID_1", "demo_source_1").strip()
    if not base_id or not base_id.replace("-", "").replace("_", "").isalnum():
        return {"status": "error", "reason": "invalid_local_source_id", "spaces": []}
    configured = env.get("LOCAL_SOURCE_ROOT_1", "").strip()
    spaces: list[dict[str, object]] = [{
        "id": base_id, "label": "All mounted documents",
        "relative_dir": "", "container_path": "/sources/source_1",
        "available": False,
    }]
    if not configured:
        return {"status": "unavailable", "reason": "source_root_not_configured",
                "spaces": spaces, "truncated": False}
    root = Path(configured).expanduser().resolve()
    if not root.is_dir():
        return {"status": "unavailable", "reason": "source_root_not_available",
                "spaces": spaces, "truncated": False}
    spaces[0]["available"] = True
    # Inspect only immediate directories, never follow links or recursively walk.
    candidates: list[Path] = []
    try:
        for child in root.iterdir():
            if child.name.startswith(".") or child.is_symlink() or not child.is_dir():
                continue
            if not child.resolve().is_relative_to(root):
                continue
            candidates.append(child)
    except OSError:
        return {"status": "unavailable", "reason": "source_root_unreadable",
                "spaces": spaces, "truncated": False}
    candidates.sort(key=lambda p: p.name.casefold())
    for child in candidates[:MAX_SPACES]:
        digest = hashlib.sha256(child.name.encode("utf-8")).hexdigest()[:16]
        spaces.append({
            "id": "space_" + digest, "label": child.name,
            "relative_dir": child.name,
            "container_path": "/sources/source_1/" + child.name,
            "available": True,
        })
    return {
        "status": "ok", "spaces": spaces,
        "truncated": len(candidates) > MAX_SPACES,
        "scope": "configured_read_only_mount_only",
    }


def resolve_source_space(env: dict[str, str], source_id: str | None) -> dict[str, object]:
    available = discover_source_spaces(env)
    if not available["spaces"]:
        raise ValueError(available.get("reason", "invalid_local_source_id"))
    default = available["spaces"][0]
    if source_id is None or source_id == default["id"]:
        return default
    if available["status"] != "ok":
        raise ValueError("source_root_unavailable")
    for space in available["spaces"][1:]:
        if source_id == space["id"]:
            # Revalidate after discovery; a directory may have been replaced.
            root = Path(env["LOCAL_SOURCE_ROOT_1"]).expanduser().resolve()
            child = root / str(space["relative_dir"])
            if (child.is_symlink() or not child.is_dir()
                    or not child.resolve().is_relative_to(root)):
                raise ValueError("source_space_changed")
            return space
    raise ValueError("unconfigured_source_space")
