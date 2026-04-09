from __future__ import annotations

import argparse

from tof_cli.core.compose_profile import knowledge_compose_profile
from tof_cli.core.docker_ops import compose_file_args, docker_exists, docker_reachable, run_docker_compose
from tof_cli.core.env_ops import ensure_env_file, read_env
from tof_cli.core.platform_profile import detect_platform
from tof_cli.knowledge.source_ops import source_root_report


def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("status", help="show platform and compose status")
    parser.set_defaults(handler=handle)


def handle(_args: argparse.Namespace) -> int:
    env_path, _ = ensure_env_file()
    env = read_env()
    profile = knowledge_compose_profile(env)
    platform_info = detect_platform()
    source = source_root_report(env)

    print("runtime status")
    print(f"- env_path: {env_path}")
    print(f"- platform: {platform_info.system} {platform_info.release} / {platform_info.machine}")
    print(f"- cpu_cores: {platform_info.cpu_cores}")
    print(f"- compose_files: {[str(path) for path in profile.files]}")
    print(f"- compose_profiles: {profile.profiles or ['default']}")
    print(f"- source_root: {source['path']}")
    print(f"- source_state: {source['state']}")

    if not docker_exists():
        print("- docker: missing")
        return 1
    if not docker_reachable():
        print("- docker: installed but not reachable")
        return 1

    compose_args = compose_file_args(profile.files) + ["ps"]
    result = run_docker_compose(compose_args, capture_output=True, check=False)
    print("- compose_ps:")
    output = result.stdout.strip() if result.stdout else "(no output)"
    print(output)
    return 0 if result.returncode == 0 else int(result.returncode)
