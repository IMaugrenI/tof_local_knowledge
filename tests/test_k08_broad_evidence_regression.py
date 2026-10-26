"""K-08 regression for false-grounding via broad OR retrieval (no Docker needed)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "k08_qa", ROOT / "services/qa_api/app/runtime.py"
)
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
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, json):
        self.calls.append(json)
        return FakeResponse(self.responses.get(json["query"], []))


def hit(document_id, preview_text, filename="company_handbook.md"):
    return {
        "document_id": document_id,
        "segment_id": "seg-" + document_id,
        "source_id": "demo_source_1",
        "relative_path": filename,
        "citation_label": document_id + "#seg-1",
        "preview_text": preview_text,
    }


def test_reported_negative_customer_contract_number_has_no_false_evidence(monkeypatch):
    question = "What is the private customer contract number?"
    broad_query = "private OR customer OR contract OR number"
    candidates = [
        hit("doc-1", "Do not use private customer files in screenshots."),
        hit("doc-2", "No customer data is shown in meeting notes.", "meeting_notes.md"),
        hit("doc-3", "The local demo source is private by default.", "product_notes.md"),
    ]
    client = FakeClient({broad_query: candidates})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)

    packet = qa.answer(qa.QaRequest(
        question=question, source_scope=["demo_source_1"], limit=5
    ))

    assert [request["query"] for request in client.calls] == [
        question, "private customer contract number", broad_query,
    ]
    assert all(request["source_scope"] == ["demo_source_1"] for request in client.calls)
    assert all(request["limit"] == 5 for request in client.calls)
    assert "Keine belastbare Antwort gefunden" in packet["answer_text"]
    assert "contract number:" not in packet["answer_text"].lower()
    assert packet["confidence"] == 0.0
    assert packet["citations"] == []
    assert packet["used_documents"] == []
    assert packet["evidence_refs"] == []
    assert packet["uncertainties"] == ["no_evidence", "broad_keyword_search"]
    assert packet["search_queries"][-1] == broad_query
    assert packet["evidence_signal"]["status"] == "no_evidence"
    assert packet["evidence_signal"]["matching_segments"] == 0
    assert packet["evidence_signal"]["distinct_documents"] == 0
    assert packet["evidence_signal"]["search_strategy"] == "broad"
    assert packet["evidence_signal"]["unverified_candidates"] == 3
    assert packet["evidence_signal"]["calibrated"] is False


@pytest.mark.parametrize(("question", "fallback", "broad"), [
    ("Wie lautet die private Kundennummer?",
     "lautet private kundennummer",
     "lautet OR private OR kundennummer"),
    ("Wo finde ich die geheime Vertragsnummer?",
     "finde geheime vertragsnummer",
     "finde OR geheime OR vertragsnummer"),
])
def test_german_negative_question_remains_unanswered_with_broad_hits(
    monkeypatch, question, fallback, broad,
):
    client = FakeClient({broad: [hit(
        "doc-de", "Private Dateien dürfen keine Screenshots enthalten.",
        "sicherheit.md",
    )]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=question))
    assert [call["query"] for call in client.calls] == [question, fallback, broad]
    assert result["citations"] == []
    assert result["evidence_refs"] == []
    assert result["confidence"] == 0.0
    assert result["evidence_signal"]["status"] == "no_evidence"


def test_positive_vacation_policy_retains_exact_segment_citations(monkeypatch):
    question = "What does the demo say about vacation policy?"
    evidence = hit(
        "doc-vacation",
        "Vacation requests should be submitted at least two weeks before the planned absence.",
    )
    client = FakeClient({question: [evidence]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=question, source_scope=["demo_source_1"]))
    assert len(client.calls) == 1
    assert result["citations"] == ["doc-vacation#seg-1"]
    assert result["evidence_refs"] == [{
        "segment_id": "seg-doc-vacation",
        "document_id": "doc-vacation",
        "source_id": "demo_source_1",
        "relative_path": "company_handbook.md",
        "citation_label": "doc-vacation#seg-1",
    }]
    assert result["evidence_signal"]["status"] == "single_document_matches"
    assert "two weeks" in result["answer_text"]
    assert result["confidence"] > 0


def test_positive_keyword_fallback_preserves_existing_evidence_path(monkeypatch):
    question = "What does the demo say about vacation policy?"
    evidence = hit("doc-vacation", "## Vacation policy: apply two weeks in advance.")
    client = FakeClient({"demo vacation policy": [evidence]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=question))
    assert len(client.calls) == 2
    assert result["evidence_signal"]["search_strategy"] == "keywords"
    assert result["citations"] == ["doc-vacation#seg-1"]


def test_empty_retrieval_keeps_original_no_evidence_shape(monkeypatch):
    client = FakeClient({})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question="What is the private customer contract number?"))
    assert result["evidence_signal"]["status"] == "no_evidence"
    assert result["citations"] == []
    assert result["used_documents"] == []
    assert result["evidence_refs"] == []
    assert result["confidence"] == 0.0
