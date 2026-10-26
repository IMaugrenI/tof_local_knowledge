"""K-09 targeted search/QA demo regressions; no Docker or second stack."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "k09_qa", ROOT / "services/qa_api/app/runtime.py"
)
assert spec and spec.loader
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


class Response:
    def __init__(self, hits):
        self.hits = hits

    def raise_for_status(self):
        pass

    def json(self):
        return {"hits": self.hits}


class Client:
    def __init__(self, by_query):
        self.by_query = by_query
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, json):
        self.calls.append(json)
        return Response(self.by_query.get(json["query"], []))


def hit(name, snippet):
    return {
        "source_id": "demo_source_1",
        "document_id": "doc-" + name,
        "relative_path": name,
        "segment_id": "seg-" + name,
        "citation_label": name + "#seg-1",
        "preview_text": snippet,
    }


def test_why_demo_screenshots_safe_to_publish_uses_strict_public_variant(monkeypatch):
    q = "Why are demo screenshots safe to publish?"
    candidate = hit(
        "company_handbook.md",
        "Demo documents are safe for public screenshots because they contain only artificial information.",
    )
    client = Client({"demo screenshots safe public": [candidate]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=q, source_scope=["demo_source_1"]))

    assert [x["query"] for x in client.calls] == [
        q,
        "demo screenshots safe publish",
        "demo screenshots safe public",
    ]
    assert all(x["source_scope"] == ["demo_source_1"] for x in client.calls)
    assert result["evidence_signal"]["search_strategy"] == "keywords_variant"
    assert result["citations"] == ["company_handbook.md#seg-1"]
    assert result["evidence_refs"][0]["relative_path"] == "company_handbook.md"
    assert result["confidence"] > 0
    assert "lexical_variant_not_semantically_verified" in result["uncertainties"]


def test_which_incident_resolved_uses_strict_keywords_with_filename_match(monkeypatch):
    q = "Which incident was resolved?"
    candidate = hit("incident_log_sample.csv", "2026-01-10,indexing,...,resolved")
    client = Client({"incident resolved": [candidate]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=q))

    assert [x["query"] for x in client.calls] == [q, "incident resolved"]
    assert result["evidence_signal"]["search_strategy"] == "keywords"
    assert result["citations"] == ["incident_log_sample.csv#seg-1"]
    assert result["evidence_refs"][0]["relative_path"] == "incident_log_sample.csv"


def test_private_contract_number_still_rejects_or_matches(monkeypatch):
    q = "What is the private customer contract number?"
    client = Client({
        "private OR customer OR contract OR number": [
            hit("company_handbook.md", "Private customer files should not be used.")
        ]
    })
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=q))
    assert [x["query"] for x in client.calls] == [
        q,
        "private customer contract number",
        "private OR customer OR contract OR number",
    ]
    assert result["confidence"] == 0
    assert result["citations"] == []
    assert result["evidence_refs"] == []
    assert result["evidence_signal"]["status"] == "no_evidence"


def test_why_public_variant_without_match_does_not_cite_or_evidence(monkeypatch):
    q = "Why are demo screenshots safe to publish?"
    client = Client({"demo OR screenshots OR safe OR publish": [
        hit("support_faq.md", "Synthetic example.")
    ]})
    monkeypatch.setattr(qa.httpx, "Client", lambda **_: client)
    result = qa.answer(qa.QaRequest(question=q))
    assert [x["query"] for x in client.calls] == [
        q,
        "demo screenshots safe publish",
        "demo screenshots safe public",
        "demo OR screenshots OR safe OR publish",
    ]
    assert result["confidence"] == 0
    assert result["citations"] == []
    assert result["used_documents"] == []
    assert result["evidence_signal"]["status"] == "no_evidence"
    assert result["evidence_signal"]["unverified_candidates"] == 1
