"""Search ranking metadata and indexed-source filtering contract."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Cursor:
    def __init__(self):
        self.query = ""
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        self.query = " ".join(sql.lower().split())
        self.params = params

    def fetchall(self):
        return [{
            "document_id": "doc-1", "source_id": "source-1",
            "relative_path": "policy.pdf", "segment_id": "seg-1",
            "citation_label": "policy:page2", "text_content": "Urlaub hat Fristen",
            "score": 0.12, "page_no": 2, "segment_kind": "paragraph",
            "ordinal": 3,
        }]


class Db:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self.cursor_obj


def test_search_has_stable_order_and_page_metadata(monkeypatch):
    cur = Cursor()
    shared = types.ModuleType("_shared_db")
    shared.db_conn = lambda: Db(cur)
    monkeypatch.setitem(sys.modules, "_shared_db", shared)
    spec = importlib.util.spec_from_file_location(
        "k6_search", ROOT / "services/search_api/app/runtime.py"
    )
    assert spec and spec.loader
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)

    result = runtime.search(runtime.SearchRequest(
        query="Urlaub", source_scope=["source-1"], limit=4,
    ))
    assert result["count"] == 1
    assert result["hits"][0]["page_no"] == 2
    assert result["hits"][0]["segment_kind"] == "paragraph"
    assert result["hits"][0]["ordinal"] == 3
    assert cur.params == ["Urlaub", "Urlaub", ["source-1"], 4]
    assert "d.extraction_status = 'done'" in cur.query
    assert "source.enabled is true" in cur.query
    assert "s.ordinal asc, s.segment_id asc" in cur.query
    # A document name such as incident_log_sample.csv is searchable together
    # with the extracted "resolved" status stored in the same segment.
    assert cur.query.count("translate(d.relative_path, '_./-', '    ')") == 2
    assert cur.query.count("to_tsvector('simple', s.text_content || ' ' ||") == 2
    assert "d.source_id = any(%s)" in cur.query

