from pathlib import Path


def test_compose_published_ports_default_to_loopback():
    compose = (Path(__file__).resolve().parents[1] / "compose.full.yml").read_text(encoding="utf-8")
    published_port_lines = [
        line.strip()
        for line in compose.splitlines()
        if line.strip().startswith('- "${BIND_HOST')
    ]

    assert len(published_port_lines) == 9
    assert all(line.startswith('- "${BIND_HOST:-127.0.0.1}:') for line in published_port_lines)
