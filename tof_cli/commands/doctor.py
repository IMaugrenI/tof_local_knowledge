from __future__ import annotations

import argparse
import socket

from tof_cli.core.docker_ops import docker_exists, docker_reachable
from tof_cli.core.env_ops import ensure_env_file, read_env
from tof_cli.core.platform_profile import detect_platform
from tof_cli.knowledge.source_ops import source_root_report

PORT_KEYS = [
    "POSTGRES_PORT",
    "AUTH_API_PORT",
    "CATALOG_API_PORT",
    "INGEST_API_PORT",
    "EXTRACTOR_API_PORT",
    "SEARCH_API_PORT",
    "QA_API_PORT",
    "OPENWEBUI_PORT",
    "OLLAMA_PORT",
]


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("doctor", help="run local readiness checks")
    parser.set_defaults(handler=handle)


def _port_state(port: int) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        result = sock.connect_ex(("127.0.0.1", port))
    return "listening" if result == 0 else "free_or_unreachable"


def handle(_args: argparse.Namespace) -> int:
    env_path, _ = ensure_env_file()
    env = read_env()
    platform_info = detect_platform()
    source = source_root_report(env)

    failures = 0

    print("doctor report")
    print(f"- env_path: {env_path}")
    print(f"- platform: {platform_info.system} {platform_info.release} / {platform_info.machine}")

    docker_installed = docker_exists()
    docker_live = docker_reachable()
    print(f"- docker_installed: {docker_installed}")
    print(f"- docker_reachable: {docker_live}")
    if not docker_installed or not docker_live:
        failures += 1

    print(f"- source_root: {source['path']}")
    print(f"- source_state: {source['state']}")
    if source["state"] != "ok":
        failures += 1

    print("- port_scan:")
    for key in PORT_KEYS:
        raw = env.get(key, "").strip()
        if not raw.isdigit():
            print(f"  - {key}: invalid")
            failures += 1
            continue
        port = int(raw)
        state = _port_state(port)
        print(f"  - {key}={port}: {state}")

    print(f"doctor finished: failures={failures}")
    return 0 if failures == 0 else 1
