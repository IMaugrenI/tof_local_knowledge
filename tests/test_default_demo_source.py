from pathlib import Path


def test_fresh_clone_uses_synthetic_demo_source():
    repo_root = Path(__file__).resolve().parents[1]
    env_example = (repo_root / ".env.example").read_text(encoding="utf-8")
    source_line = next(line for line in env_example.splitlines() if line.startswith("LOCAL_SOURCE_ROOT_1="))
    assert source_line == "LOCAL_SOURCE_ROOT_1=./demo/source_1"
    assert (repo_root / "demo" / "source_1").is_dir()
