"""K-10: default .env permission boundary; isolated filesystem tests only."""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from tof_cli.core import env_ops


@pytest.fixture
def local_paths(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    template = tmp_path / ".env.example"
    template.write_text("POSTGRES_PASSWORD=demo-only-placeholder\n", encoding="utf-8")
    monkeypatch.setattr(env_ops, "ENV_PATH", env)
    monkeypatch.setattr(env_ops, "ENV_EXAMPLE_PATH", template)
    return env, template


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits")
def test_env_creation_is_private_even_under_permissive_umask(local_paths):
    env, template = local_paths
    previous = os.umask(0)
    try:
        path, created = env_ops.ensure_env_file()
    finally:
        os.umask(previous)
    assert created is True
    assert path == env
    assert env.read_text(encoding="utf-8") == template.read_text(encoding="utf-8")
    assert stat.S_IMODE(env.stat().st_mode) == 0o600


@pytest.mark.skipif(os.name != "posix", reason="POSIX mode bits")
def test_existing_env_is_restricted_without_overwriting_content(local_paths):
    env, _ = local_paths
    custom = "POSTGRES_PASSWORD=user-changed-value\nLOCAL_SOURCE_ROOT_1=/example\n"
    env.write_text(custom, encoding="utf-8")
    env.chmod(0o664)

    path, created = env_ops.ensure_env_file()
    assert created is False
    assert path == env
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert env.read_text(encoding="utf-8") == custom

    same_path, created_again = env_ops.ensure_env_file()
    assert same_path == env
    assert created_again is False
    assert stat.S_IMODE(env.stat().st_mode) == 0o600


def test_env_symlink_is_rejected_without_touching_target(local_paths, tmp_path):
    env, _ = local_paths
    target = tmp_path / "external.txt"
    target.write_text("external content", encoding="utf-8")
    old_mode = stat.S_IMODE(target.stat().st_mode)
    try:
        env.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable on this system")

    with pytest.raises((ValueError, OSError)):
        env_ops.ensure_env_file()
    assert target.read_text(encoding="utf-8") == "external content"
    assert stat.S_IMODE(target.stat().st_mode) == old_mode


def test_env_directory_is_rejected(local_paths):
    env, _ = local_paths
    env.mkdir()
    with pytest.raises(ValueError, match="regular file"):
        env_ops.ensure_env_file()
    assert env.is_dir()


def test_missing_template_does_not_create_env(local_paths):
    env, template = local_paths
    template.unlink()
    with pytest.raises(FileNotFoundError):
        env_ops.ensure_env_file()
    assert not env.exists()
