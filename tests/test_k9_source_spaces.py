"""Separate read-only source spaces inside the existing configured Compose mount."""
from __future__ import annotations

import pytest

from tof_cli.knowledge import index_ops, source_spaces
from tof_cli.ui import app


def test_discovery_lists_only_existing_directories_inside_fixed_root(tmp_path):
    root = tmp_path / "mounted"
    root.mkdir()
    (root / "contracts").mkdir()
    (root / "research").mkdir()
    (root / "file.md").write_text("test", encoding="utf-8")
    (root / ".private").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "outside-link").symlink_to(outside, target_is_directory=True)
    env = {"LOCAL_SOURCE_ROOT_1": str(root), "LOCAL_SOURCE_ID_1": "demo_source_1"}
    found = source_spaces.discover_source_spaces(env)
    assert found["status"] == "ok"
    assert len(found["spaces"]) == 3
    assert {entry["label"] for entry in found["spaces"][1:]} == {"contracts", "research"}
    assert found["spaces"][0]["container_path"] == "/sources/source_1"
    for entry in found["spaces"][1:]:
        assert entry["container_path"].startswith("/sources/source_1/")
        assert entry["available"] is True


def test_logical_ids_remain_stable_and_reject_unlisted_sources(tmp_path):
    root = tmp_path / "mounted"
    root.mkdir()
    (root / "customers").mkdir()
    env = {"LOCAL_SOURCE_ROOT_1": str(root)}
    before = source_spaces.discover_source_spaces(env)["spaces"][1]
    after = source_spaces.resolve_source_space(env, before["id"])
    assert after == before
    with pytest.raises(ValueError, match="unconfigured"):
        source_spaces.resolve_source_space(env, "/etc/passwd")
    (root / "customers").rename(root / "customers_old")
    with pytest.raises(ValueError, match="unconfigured"):
        source_spaces.resolve_source_space(env, before["id"])


def test_default_source_id_preserves_existing_single_mount_contract():
    result = source_spaces.resolve_source_space({}, None)
    assert result["id"] == "demo_source_1"
    assert result["container_path"] == "/sources/source_1"


def test_indexing_selected_space_uses_existing_services_and_path(monkeypatch, tmp_path):
    root = tmp_path / "mounted"
    root.mkdir()
    (root / "reports").mkdir()
    env = {"LOCAL_SOURCE_ROOT_1": str(root)}
    space = source_spaces.discover_source_spaces(env)["spaces"][1]
    monkeypatch.setattr(index_ops, "read_env", lambda: env)
    calls = []

    def post(url, payload, **kwargs):
        calls.append((url, payload))
        if url.endswith("/scan/run"):
            return {
                "status": "ok", "files_scanned": 1, "scan_complete": True,
                "sample_documents": [{
                    "scan_status": "new", "document_id": "doc-1",
                    "relative_path": "report.md",
                }],
            }
        return {"status": "ok", "segment_count": 1}

    monkeypatch.setattr(index_ops, "_local_post", post)
    result = index_ops.index_configured_source(space_id=space["id"])
    assert result["status"] == "ok"
    assert result["source_id"] == space["id"]
    assert result["source_label"] == "reports"
    assert result["indexed_this_pass"] == 1
    assert len(calls) == 2
    assert all(payload["source_id"] == space["id"] for _, payload in calls)
    assert all(payload["root_path"] == "/sources/source_1/reports" for _, payload in calls)


def test_unconfigured_space_never_calls_ingest(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {})
    monkeypatch.setattr(index_ops, "_local_post",
                        lambda *a, **kw: (_ for _ in ()).throw(
                            AssertionError("unsafe target must not scan")))
    output = index_ops.index_configured_source(space_id="untrusted")
    assert output["status"] == "error"
    assert output["detail"] in {"source_root_unavailable", "unconfigured_source_space"}


def test_source_space_ui_offers_explicit_selection_and_existing_status():
    assert "loadSourceSpaces()" in app.HTML
    assert "id=\"index-source-select\"" in app.HTML
    assert "space_id: document.getElementById('index-source-select').value" in app.HTML
    assert "refreshSources()" in app.HTML
