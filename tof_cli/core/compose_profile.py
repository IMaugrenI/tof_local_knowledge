from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tof_cli.core.env_ops import REPO_ROOT, env_bool


@dataclass(frozen=True)
class ComposeProfile:
    files: list[Path]
    profiles: list[str]


def knowledge_compose_profile(env: dict[str, str]) -> ComposeProfile:
    profiles: list[str] = []
    if env_bool(env, "ENABLE_OLLAMA", default=False):
        profiles.append("llm")
    if env_bool(env, "ENABLE_OPEN_WEBUI", default=False):
        profiles.append("ui")
    return ComposeProfile(files=[REPO_ROOT / "compose.full.yml"], profiles=profiles)
