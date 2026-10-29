from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "services" / "qa_api" / "app" / "runtime.py"
SPEC = importlib.util.spec_from_file_location("tof_local_knowledge_qa_runtime", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
qa_runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa_runtime)

fallback_search_query = qa_runtime.fallback_search_query


def test_fallback_search_query_keeps_content_terms():
    assert fallback_search_query("What does the demo say about vacation policy?") == "demo vacation policy"


def test_fallback_search_query_keeps_negative_test_terms():
    assert fallback_search_query("What is the private customer contract number?") == "private customer contract number"


def test_contextual_followup_reuses_only_bounded_question_topics():
    from pydantic import ValidationError
    assert qa_runtime.contextual_followup_query(
        "Und welche Frist gilt dafür?",
        "Was steht im Mietvertrag zur Kündigung?",
    ) == "mietvertrag kündigung frist"
    assert qa_runtime.contextual_followup_query(
        "Welche Kosten entstehen?", "Was steht im Mietvertrag zur Kündigung?"
    ) is None
    assert qa_runtime.contextual_followup_query("Und wann?", None) is None
    try:
        qa_runtime.QaRequest(question="Und wann?", previous_question="x" * 501)
    except ValidationError:
        pass
    else:
        raise AssertionError("unbounded chat context accepted")


def test_contextual_qa_only_cites_live_scoped_search_hits(monkeypatch):
    queries = []
    class FakeClient:
        def __init__(self, timeout): self.timeout = timeout
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_search(client, query, payload):
        queries.append((query, payload.source_scope))
        if query == "mietvertrag kündigung frist":
            return {"hits": [{
                "document_id": "doc_1", "source_id": "space_a",
                "relative_path": "Mietvertrag.md", "segment_id": "segment_1",
                "citation_label": "Quelle 1", "preview_text": "Kündigungsfrist: 3 Monate.",
            }]}
        return {"hits": []}

    monkeypatch.setattr(qa_runtime.httpx, "Client", FakeClient)
    monkeypatch.setattr(qa_runtime, "run_search", fake_search)
    response = qa_runtime.answer(qa_runtime.QaRequest(
        question="Und welche Frist gilt dafür?",
        previous_question="Was steht im Mietvertrag zur Kündigung?",
        source_scope=["space_a"],
    ))
    assert queries == [("mietvertrag kündigung frist", ["space_a"])]
    assert response["citations"] == ["Quelle 1"]
    assert response["evidence_signal"]["search_strategy"] == "contextual_followup"
    assert "contextual_keyword_match_not_semantically_verified" in response["uncertainties"]


def test_contextual_qa_never_promotes_broad_or_hits_to_citations(monkeypatch):
    class FakeClient:
        def __init__(self, timeout): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_search(client, query, payload):
        if " OR " in query:
            return {"hits": [{"document_id": "unrelated"}]}
        return {"hits": []}

    monkeypatch.setattr(qa_runtime.httpx, "Client", FakeClient)
    monkeypatch.setattr(qa_runtime, "run_search", fake_search)
    response = qa_runtime.answer(qa_runtime.QaRequest(
        question="Und welche Frist gilt dafür?",
        previous_question="Was steht im Mietvertrag zur Kündigung?",
    ))
    assert response["citations"] == []
    assert response["used_documents"] == []
    assert response["evidence_refs"] == []
    assert response["confidence"] == 0
