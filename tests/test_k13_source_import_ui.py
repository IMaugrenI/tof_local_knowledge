"""Focused source-import safety tests using only temporary synthetic files."""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

import pytest

from tof_cli.knowledge import source_imports
from tof_cli.ui import app


@pytest.fixture
def root(tmp_path, monkeypatch):
    configured = tmp_path / "approved_source"
    configured.mkdir()
    monkeypatch.setattr(source_imports, "_root", lambda: configured)
    return configured


def entry(name, raw=b"synthetic test material"):
    return {"name": name, "data": base64.b64encode(raw).decode("ascii")}


def test_explicit_single_and_folder_files_copy_only_to_approved_root(root):
    result = source_imports.import_selected_files([
        entry("notes.md", b"allowed"),
        entry("Meeting/notes.csv", b"Date,Name\n2026-10-26,Demo"),
    ])
    assert result["status"] == "ok"
    assert result["copied"] == 2
    assert result["requires_index"] is True
    dest = root / "Importierte_Dateien"
    assert (dest / "notes.md").read_bytes() == b"allowed"
    assert (dest / "Meeting/notes.csv").read_bytes().startswith(b"Date")
    assert result["source_id"] == "space_" + hashlib.sha256(
        b"Importierte_Dateien"
    ).hexdigest()[:16]


@pytest.mark.parametrize("filename", [
    "../outside.md", "/etc/passwd", "a/../../escape.txt", ".secret.txt",
    "a/.hidden/private.md", "x\\..\\file.md", "C:/temp/file.md",
    "private.exe", "a/" + "nested/" * 12 + "test.md",
])
def test_rejects_unsafe_paths_and_unsupported_types(root, filename):
    with pytest.raises(ValueError):
        source_imports.import_selected_files([entry(filename)])
    assert not list(root.iterdir())


def test_rejects_oversized_file_and_upload_count_before_writing(root):
    with pytest.raises(ValueError, match="upload_too_large"):
        source_imports.import_selected_files([
            entry("large.pdf", b"x" * (source_imports.MAX_FILE_BYTES + 1))
        ])
    with pytest.raises(ValueError, match="invalid_file_count"):
        source_imports.import_selected_files([entry("x.md")] * 5)
    assert not list(root.iterdir())


def test_import_updates_only_managed_copy_not_any_original_file(root, tmp_path):
    original = tmp_path / "contract.md"
    original.write_text("ORIGINAL", encoding="utf-8")
    source_imports.import_selected_files([entry("contract.md", b"COPY")])
    source_imports.import_selected_files([entry("contract.md", b"UPDATED COPY")])
    assert original.read_text(encoding="utf-8") == "ORIGINAL"
    assert (root / "Importierte_Dateien/contract.md").read_bytes() == b"UPDATED COPY"


def test_does_not_follow_symlinks_within_import_destination(root, tmp_path):
    outside = tmp_path / "private"
    outside.mkdir()
    (root / "Importierte_Dateien").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="unsafe_destination"):
        source_imports.import_selected_files([entry("folder/test.md")])
    assert list(outside.iterdir()) == []


def test_invalid_base64_never_persists(root):
    with pytest.raises(ValueError, match="invalid_file_data"):
        source_imports.import_selected_files([{"name": "valid.md", "data": "-@"}])
    assert not list(root.iterdir())


def test_source_chooser_visible_with_manual_indexing_and_privacy_text():
    html = app._render_page("/quellen-index")
    assert 'id="source-files"' in html
    assert 'id="source-folder"' in html
    assert 'webkitdirectory' in html
    assert 'onclick="chooseFolder()"' in html
    assert 'onclick="syncFolder()"' in html
    assert 'id="source-import-status"' in html
    assert 'id="index-batch-button"' in html
    assert 'id="source-index-now"' in html
    assert 'onclick="indexImportedSource()"' in html
    assert "for (let batch = 0; batch < 45; batch++)" in html
    assert 'id="index-advanced"' in html
    assert "X-ToF-UI-Action" in html
    assert "indexedDB.open('tof_knowledge_folder_permission', 1)" in html
    assert "window.showDirectoryPicker" in html
    assert "await handle.requestPermission({mode: 'read'})" in html
    assert "if (imported && sourceId)" in html


def test_upload_does_not_add_public_routes_to_api_map():
    assert "/api/import-files" not in app.PAGE_ROUTES
    assert app.run_ui.__defaults__[:2] == ("127.0.0.1", 8785)
    assert app._render_page("/") == app._render_page("/uebersicht")
