from __future__ import annotations

import argparse

from tof_cli.core.env_ops import ensure_env_file, read_env
from tof_cli.core.health_ops import check_url, print_health_result
from tof_cli.knowledge.service_health import health_targets


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("check", help="check service health endpoints")
    parser.set_defaults(handler=handle)


def handle(_args: argparse.Namespace) -> int:
    ensure_env_file()
    env = read_env()
    failures = 0
    for label, url in health_targets(env):
        ok, detail = check_url(url)
        print_health_result(label, ok, detail)
        if not ok:
            failures += 1
    print(f"healthcheck finished: failures={failures}")
    return 0 if failures == 0 else 1
