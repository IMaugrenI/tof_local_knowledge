"""Targeted German QA fallback and evidence coverage tests (no runtime required)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "k6_qa_runtime", ROOT / "services/qa_api/app/runtime.py"
)
assert spec and spec.loader
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class Response:
    def __init__(self, hits):
        self.hits = hits

    def raise_for_status(self):
        return None

    def json(self):
        return {"hits": self.hits}


class Client:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, json):
        self.calls.append(json)
        return Response(self.responses.get(json["query"], []))


HIT = {
    "document_id": "doc-1", "source_id": "local-source",
    "relative_path": "richtlinie.md", "segment_id": "seg-1",
    "citation_label": "richtlinie:1", "preview_text": "Urlaub beträgt 30 Tage",
}


def test_german_fallback_preserves_umlauts_compounds_and_negation():
    assert qa.fallback_search_query(
        "Welche Regelung gilt für Überstunden und Kündigungsfristen?"
    ) == "regelung gilt überstunden kündigungsfristen"
    assert qa.fallback_search_query("Was ist NICHT versichert?") == "nicht versichert"


def test_english_fallback_remains_compatible():
    assert qa.fallback_search_query(
        "What does the demo say about vacation policy?"
    ) == "demo vacation policy"


def test_keyword_fallback_preserves_client_source_scope(monkeypatch):
    client = Client({"urlaubsanspruch tarifvertrag": [HIT]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **kwargs: client)
    answer = qa.answer(qa.QaRequest(
        question="Wie ist der Urlaubsanspruch im Tarifvertrag?",
        source_scope=["allowed"], limit=3,
    ))
    assert len(client.calls) == 2
    assert client.calls[1]["query"] == "urlaubsanspruch tarifvertrag"
    assert all(call["source_scope"] == ["allowed"] for call in client.calls)
    assert all(call["limit"] == 3 for call in client.calls)
    assert answer["evidence_signal"]["search_strategy"] == "keywords"
    assert answer["evidence_signal"]["distinct_documents"] == 1
    assert answer["evidence_signal"]["calibrated"] is False


def test_broad_fallback_is_explicit_and_not_a_verification(monkeypatch):
    client = Client({"urlaub OR tarifvertrag": [HIT]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **kwargs: client)
    answer = qa.answer(qa.QaRequest(
        question="Was steht zu Urlaub und Tarifvertrag?"
    ))
    assert [call["query"] for call in client.calls] == [
        "Was steht zu Urlaub und Tarifvertrag?", "steht urlaub tarifvertrag",
        "steht OR urlaub OR tarifvertrag",
    ] or [call["query"] for call in client.calls] == [
        "Was steht zu Urlaub und Tarifvertrag?", "steht urlaub tarifvertrag",
        "steht OR urlaub OR tarifvertrag",
    ]
    assert "broad_keyword_search" not in answer["uncertainties"]


def test_search_without_any_evidence_keeps_explicit_no_evidence(monkeypatch):
    client = Client({})
    monkeypatch.setattr(qa.httpx, "Client", lambda **kwargs: client)
    output = qa.answer(qa.QaRequest(question="Wo ist der Bericht?"))
    assert output["evidence_signal"]["status"] == "no_evidence"
    assert output["citations"] == []
    assert output["confidence"] == 0.0
