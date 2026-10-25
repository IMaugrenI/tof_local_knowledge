"""K4 checks for the current, read-only evidence inspector."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]


class Cursor:
    def __init__(self, result):
        self.result = result
        self.sql = ""
        self.params = ()
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql, params):
        self.sql = " ".join(sql.lower().split())
        self.params = params
    def fetchone(self):
        return self.result


class Db:
    def __init__(self, cursor):
        self.c = cursor
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def cursor(self):
        return self.c


def load_api(monkeypatch, cursor):
    fake_db = types.ModuleType("_shared_db")
    fake_db.db_conn = lambda: Db(cursor)
    monkeypatch.setitem(sys.modules, "_shared_db", fake_db)
    spec = importlib.util.spec_from_file_location(
        "k4_search_inspector", ROOT / "services/search_api/app/runtime.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inspector_reads_exact_segment_only_when_current_and_enabled(monkeypatch):
    row = {
        "segment_id": "seg-1", "document_id": "doc-1",
        "source_id": "demo", "relative_path": "handbook.md",
        "citation_label": "handbook:1", "segment_kind": "text",
        "page_no": None, "ordinal": 1, "excerpt": "The actual text.",
    }
    cursor = Cursor(row)
    api = load_api(monkeypatch, cursor)
    result = api.evidence("seg-1")
    assert result["evidence"] == row
    assert result["scope"] == "local_single_user_only"
    assert cursor.params == ("seg-1",)
    assert "s.segment_id = %s" in cursor.sql
    assert "d.extraction_status = 'done'" in cursor.sql
    assert "source.enabled is true" in cursor.sql
    assert "left(s.text_content, 2000)" in cursor.sql


def test_missing_or_stale_segment_is_not_exposed(monkeypatch):
    cursor = Cursor(None)
    api = load_api(monkeypatch, cursor)
    with pytest.raises(HTTPException) as exc:
        api.evidence("seg-missing")
    assert exc.value.status_code == 404
    assert exc.value.detail == "evidence_not_available"


def test_browser_proxy_disallows_arbitrary_ids_and_network_binding(monkeypatch):
    from tof_cli.ui import app
    monkeypatch.setattr(app, "read_env", lambda: {"BIND_HOST": "127.0.0.1", "SEARCH_API_PORT": "8105"})
    monkeypatch.setattr(app, "_get_json", lambda url: {"called_url": url})
    assert app._evidence_lookup("../secrets")["error"] == "invalid_segment_id"
    assert app._evidence_lookup("seg_2")["called_url"] == "http://127.0.0.1:8105/evidence/seg_2"
    monkeypatch.setattr(app, "read_env", lambda: {"BIND_HOST": "0.0.0.0"})
    assert app._evidence_lookup("seg_2")["error"] == "local_only"
