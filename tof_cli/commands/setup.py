from __future__ import annotations

import argparse

from tof_cli.core.env_ops import ensure_env_file, read_env
from tof_cli.core.path_ops import DEFAULT_SETUP_DIRS, ensure_directories
from tof_cli.knowledge.source_ops import source_root_report


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("setup", help="prepare local env and directories")
    parser.set_defaults(handler=handle)


def handle(_args: argparse.Namespace) -> int:
    env_path, created = ensure_env_file()
    env = read_env()
    ensure_directories(DEFAULT_SETUP_DIRS)
    report = source_root_report(env)

    print("setup complete")
    print(f"- env_path: {env_path}")
    print(f"- env_created: {'yes' if created else 'no'}")
    print("- prepared_dirs:")
    for path in DEFAULT_SETUP_DIRS:
        print(f"  - {path}")
    print("- source_root:")
    print(f"  - path: {report['path']}")
    print(f"  - state: {report['state']}")
    if report["state"] != "ok":
        print("WARN: LOCAL_SOURCE_ROOT_1 is not ready yet.")
    return 0
