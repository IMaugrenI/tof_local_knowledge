"""QA evidence metadata must point to actual search hit segments."""
from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "qa_api" / "app" / "runtime.py"
spec = importlib.util.spec_from_file_location("k3_qa", MODULE_PATH)
assert spec and spec.loader
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class FakeResponse:
    def __init__(self, hits):
        self.hits = hits
    def raise_for_status(self):
        return None
    def json(self):
        return {"hits": self.hits}


class FakeClient:
    def __init__(self, hits):
        self.hits = hits
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def post(self, url, json):
        return FakeResponse(self.hits)


def test_answer_preserves_legacy_citations_and_adds_exact_refs(monkeypatch):
    hits = [{
        "document_id": "doc-a", "source_id": "source-1",
        "relative_path": "guide.md", "segment_id": "seg-1",
        "citation_label": "guide.md:part-1", "preview_text": "The handbook excerpt.",
    }]
    monkeypatch.setattr(qa.httpx, "Client", lambda **kwargs: FakeClient(hits))
    output = qa.answer(qa.QaRequest(question="What does the handbook say?"))
    assert output["citations"] == ["guide.md:part-1"]
    assert output["evidence_refs"] == [{
        "segment_id": "seg-1", "document_id": "doc-a",
        "source_id": "source-1", "relative_path": "guide.md",
        "citation_label": "guide.md:part-1",
    }]
    assert output["used_documents"] == ["doc-a"]


def test_no_evidence_returns_empty_refs(monkeypatch):
    monkeypatch.setattr(qa.httpx, "Client", lambda **kwargs: FakeClient([]))
    output = qa.answer(qa.QaRequest(question="A question without evidence?"))
    assert output["citations"] == []
    assert output["evidence_refs"] == []
    assert "no_evidence" in output["uncertainties"]
