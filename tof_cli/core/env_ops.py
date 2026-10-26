from __future__ import annotations

import os
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
ENV_PATH = REPO_ROOT / ".env"


def parse_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _restrict_env_file_permissions() -> None:
    """Protect existing .env without following a symlink on POSIX systems."""
    if ENV_PATH.is_symlink():
        raise ValueError(".env must be a regular file, not a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(ENV_PATH, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError(".env must be a regular file")
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        else:
            # Windows file ACLs are platform-specific; the chmod call is
            # best-effort and does not replace Windows ACL configuration.
            ENV_PATH.chmod(0o600)
    finally:
        os.close(fd)


def ensure_env_file() -> tuple[Path, bool]:
    if ENV_PATH.is_symlink():
        raise ValueError(".env must be a regular file, not a symlink")
    if ENV_PATH.exists():
        _restrict_env_file_permissions()
        return ENV_PATH, False

    # Read the template before creating .env to avoid leaving an empty secret
    # file when the template is missing or unreadable.
    initial_content = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(ENV_PATH, flags, 0o600)
    except FileExistsError:
        # Another setup process may have created .env in the meantime.
        _restrict_env_file_permissions()
        return ENV_PATH, False

    with os.fdopen(fd, "w", encoding="utf-8") as env_file:
        env_file.write(initial_content)
    return ENV_PATH, True


def read_env() -> dict[str, str]:
    base = parse_env_file(ENV_EXAMPLE_PATH)
    base.update(parse_env_file(ENV_PATH))
    return base


def env_bool(env: dict[str, str], key: str, default: bool = False) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
