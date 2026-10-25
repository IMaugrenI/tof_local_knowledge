"""Targeted catalog status contract test without a running database."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


class Cursor:
    def __init__(self):
        self.query = ""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql):
        self.query = " ".join(sql.split()).lower()
    def fetchall(self):
        return [{
            "source_id": "demo", "display_name": "Demo",
            "enabled": True, "documents_total": 3, "indexed": 1,
            "pending": 1, "failed": 1, "missing": 0,
            "last_scan_at": None, "last_scan_files": None,
        }]


class Db:
    def __init__(self, cursor):
        self.cursor_value = cursor
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def cursor(self):
        return self.cursor_value


def test_source_status_uses_existing_catalog_and_manifests(monkeypatch):
    cursor = Cursor()
    fake = types.ModuleType("_shared_db")
    fake.db_conn = lambda: Db(cursor)
    fake.make_id = lambda category: "demo-id"
    monkeypatch.setitem(sys.modules, "_shared_db", fake)

    root = Path(__file__).resolve().parents[1]
    path = root / "services" / "catalog_api" / "app" / "runtime.py"
    spec = importlib.util.spec_from_file_location("knowledge_catalog_status_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    response = module.list_source_status()
    assert response["count"] == 1
    assert response["sources"][0]["indexed"] == 1
    assert response["scope"] == "local_single_user_only"
    assert "left join documents" in cursor.query
    assert "from manifests" in cursor.query
    assert "extraction_status = 'missing'" in cursor.query
