from __future__ import annotations

import argparse

from tof_cli.core.compose_profile import knowledge_compose_profile
from tof_cli.core.docker_ops import compose_file_args, docker_exists, docker_reachable, run_docker_compose
from tof_cli.core.env_ops import ensure_env_file, read_env
from tof_cli.core.path_ops import DEFAULT_SETUP_DIRS, ensure_directories


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("up", help="start the stack with docker compose")
    parser.add_argument("--build", action="store_true", default=True, help="build images before start")
    parser.set_defaults(handler=handle)


def handle(args: argparse.Namespace) -> int:
    ensure_env_file()
    ensure_directories(DEFAULT_SETUP_DIRS)
    env = read_env()
    profile = knowledge_compose_profile(env)

    if not docker_exists():
        print("FAIL: docker is not installed or not on PATH.")
        return 1
    if not docker_reachable():
        print("FAIL: docker is installed but not reachable.")
        return 1

    compose_args = compose_file_args(profile.files)
    for compose_profile in profile.profiles:
        compose_args.extend(["--profile", compose_profile])
    compose_args.extend(["up"])
    if args.build:
        compose_args.append("--build")
    compose_args.extend(["-d"])

    result = run_docker_compose(compose_args, capture_output=False, check=False)
    if result.returncode != 0:
        print(f"FAIL: docker compose exited with code {result.returncode}")
        return int(result.returncode)

    print("stack started")
    print(f"- compose_files: {[str(path) for path in profile.files]}")
    print(f"- profiles: {profile.profiles or ['default']}")
    return 0
