from __future__ import annotations

from tof_cli.knowledge import index_ops


def test_index_batch_processes_bounded_actionable_files(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {
        "BIND_HOST": "127.0.0.1", "LOCAL_SOURCE_ID_1": "demo_source_1"
    })
    seen = []

    def fake_post(url, payload, **kwargs):
        seen.append((url, payload))
        if url.endswith("/scan/run"):
            return {
                "status": "ok", "files_scanned": 50,
                "counts": {"new": 12}, "scan_complete": True,
                "sample_documents": [
                    {"document_id": f"doc-{i}", "relative_path": f"d{i}.md",
                     "scan_status": "new"} for i in range(12)
                ]
            }
        return {"status": "ok", "segment_count": 1}

    monkeypatch.setattr(index_ops, "_local_post", fake_post)
    result = index_ops.index_configured_source()
    assert result["status"] == "ok"
    assert result["indexed_this_pass"] == index_ops.MAX_EXTRACTED_PER_CLICK
    assert result["remaining_in_sample"] == 4
    assert len(seen) == 1 + index_ops.MAX_EXTRACTED_PER_CLICK
    assert seen[0][1]["root_path"] == "/sources/source_1"
    assert all(x[1]["source_id"] == "demo_source_1" for x in seen)


def test_index_batch_rejects_untrusted_binding(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {"BIND_HOST": "0.0.0.0"})
    monkeypatch.setattr(index_ops, "_local_post", lambda *a, **kw: (_ for _ in ()).throw(
        AssertionError("must not access endpoints")
    ))
    assert index_ops.index_configured_source()["detail"] == "local_only_indexing"


def test_index_batch_rejects_invalid_source_id(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {"LOCAL_SOURCE_ID_1": "../../outside"})
    assert index_ops.index_configured_source()["detail"] == "invalid_local_source_id"


def test_index_batch_records_extraction_failures_without_lying(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {})
    def fake_post(url, payload, **kwargs):
        if url.endswith("/scan/run"):
            return {
                "status": "ok", "files_scanned": 1, "scan_complete": True,
                "counts": {"new": 1}, "sample_documents": [
                    {"document_id": "doc-1", "relative_path": "bad.pdf", "scan_status": "new"}
                ],
            }
        return {"status": "ok", "segment_count": 0}
    monkeypatch.setattr(index_ops, "_local_post", fake_post)
    result = index_ops.index_configured_source()
    assert result["status"] == "partial"
    assert result["indexed_this_pass"] == 0
    assert result["failed"][0]["detail"] == "no_extractable_text"


def test_index_batch_resumes_page_after_fresh_files_are_finished(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {})
    observed = []

    def fake_post(url, payload, **kwargs):
        observed.append((url, payload))
        if url.endswith("/scan/run"):
            return {
                "status": "ok", "files_scanned": 100, "scan_complete": False,
                "next_cursor": "file-099.md",
                "sample_documents": [
                    {"document_id": f"doc-{i}", "relative_path": f"file-{i:03d}.md",
                     "scan_status": "new"} for i in range(10)
                ],
            }
        return {"status": "ok", "segment_count": 1}

    monkeypatch.setattr(index_ops, "_local_post", fake_post)
    first = index_ops.index_configured_source()
    assert first["page_has_more"] is True
    assert first["next_cursor"] is None  # recheck page: fresh work remains
    assert first["remaining_in_sample"] == 2
    assert observed[0][1]["start_after"] is None

    observed.clear()
    second = index_ops.index_configured_source(start_after="file-099.md")
    assert observed[0][1]["start_after"] == "file-099.md"
    assert second["next_cursor"] == "file-099.md"


def test_cursor_validation_rejects_traversal_and_absolute_paths(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {})
    for cursor in ["../file", "/tmp/file", "C:\\\\folder", "X" * 2049]:
        assert index_ops.index_configured_source(start_after=cursor)["detail"] == "invalid_scan_cursor"


def test_failed_retries_do_not_block_later_pages(monkeypatch):
    monkeypatch.setattr(index_ops, "read_env", lambda: {})
    def fake_post(url, payload, **kwargs):
        if url.endswith("/scan/run"):
            return {
                "status": "ok", "scan_complete": False,
                "next_cursor": "page-end.md", "files_scanned": 100,
                "sample_documents": [
                    {"document_id": f"bad-{i}", "relative_path": f"bad-{i}.pdf",
                     "scan_status": "retry"} for i in range(20)
                ],
            }
        return {"status": "ok", "segment_count": 0}
    monkeypatch.setattr(index_ops, "_local_post", fake_post)
    result = index_ops.index_configured_source()
    assert result["status"] == "partial"
    assert result["next_cursor"] == "page-end.md"
    assert result["page_has_more"] is True
