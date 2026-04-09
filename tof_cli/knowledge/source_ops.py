from __future__ import annotations

from pathlib import Path

from tof_cli.core.path_ops import normalize_path, path_state


def source_root_from_env(env: dict[str, str]) -> Path:
    raw = env.get("LOCAL_SOURCE_ROOT_1", "").strip()
    return normalize_path(raw) if raw else Path()


def source_root_report(env: dict[str, str]) -> dict[str, str]:
    path = source_root_from_env(env)
    if not str(path):
        return {"path": "", "state": "missing_config"}
    return {"path": str(path), "state": path_state(path)}
