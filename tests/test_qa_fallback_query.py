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


def test_four_turn_context_keeps_original_grounded_topic():
    assert qa_runtime.contextual_thread_query(
        "Und welche Ausnahmen gelten?",
        ["Was steht im Mietvertrag zur Kündigung?",
         "Und welche Frist gilt dafür?"],
    ) == "mietvertrag kündigung ausnahmen"
    # An unrelated fresh question must never be polluted by prior topics.
    assert qa_runtime.contextual_thread_query(
        "Welche Kosten entstehen?", ["Was steht im Mietvertrag zur Kündigung?"],
    ) is None
    assert qa_runtime.contextual_thread_query("Und was?", [
        "Was steht im Mietvertrag zur Kündigung?"
    ]) is None


def test_bounded_chat_history_rejects_oversize_blank_and_excess_turns():
    import pytest
    from pydantic import ValidationError

    qa_runtime.QaRequest(question="Und wie?", recent_questions=[
        "Vertrag", "Frist", "Ausnahmen", "Weitere Angaben",
    ])
    for history in [
        ["a"] * 5,
        ["a" * 501],
        ["  "],
    ]:
        with pytest.raises(ValidationError):
            qa_runtime.QaRequest(question="Und wie?", recent_questions=history)


def test_multiturn_context_must_use_live_scope_and_never_answer_from_history(monkeypatch):
    queries = []
    class FakeClient:
        def __init__(self, timeout): self.timeout = timeout
        def __enter__(self): return self
        def __exit__(self, *args): return False

    def fake_search(client, query, payload):
        queries.append((query, payload.source_scope))
        if query == "mietvertrag kündigung ausnahmen":
            return {"hits": [{
                "document_id": "doc_2", "source_id": "space_a",
                "relative_path": "Mietvertrag.md", "segment_id": "segment_2",
                "citation_label": "Quelle 2", "preview_text": "Ausnahme: Urlaub.",
            }]}
        return {"hits": []}

    monkeypatch.setattr(qa_runtime.httpx, "Client", FakeClient)
    monkeypatch.setattr(qa_runtime, "run_search", fake_search)
    request = qa_runtime.QaRequest(
        question="Und welche Ausnahmen gelten?",
        recent_questions=["Was steht im Mietvertrag zur Kündigung?",
                          "Und welche Frist gilt dafür?"],
        source_scope=["space_a"],
    )
    response = qa_runtime.answer(request)
    assert queries == [("mietvertrag kündigung ausnahmen", ["space_a"])]
    assert response["citations"] == ["Quelle 2"]
    assert response["evidence_signal"]["search_strategy"] == "contextual_followup"
    assert "contextual_keyword_match_not_semantically_verified" in response["uncertainties"]

    queries.clear()
    unrelated = qa_runtime.answer(qa_runtime.QaRequest(
        question="Welche Kosten entstehen?",
        recent_questions=request.recent_questions, source_scope=["space_a"],
    ))
    assert queries[0] == ("Welche Kosten entstehen?", ["space_a"])
    assert unrelated["citations"] == []


def test_legacy_single_previous_question_still_supported():
    assert qa_runtime.contextual_thread_query(
        "Und welche Frist gilt dafür?", []
    ) is None
    assert qa_runtime.contextual_followup_query(
        "Und welche Frist gilt dafür?", "Was steht im Mietvertrag zur Kündigung?"
    ) == "mietvertrag kündigung frist"


def test_new_subject_does_not_reuse_previous_chat_topic():
    assert qa_runtime.contextual_followup_query(
        "Und was steht im neuen Vertrag?",
        "Was steht im Mietvertrag zur Kündigung?",
    ) is None
    assert qa_runtime.contextual_followup_query(
        "And what does another agreement say about damages?",
        "What does the rental policy say?",
    ) is None
    assert qa_runtime.contextual_followup_query(
        "Und welche Frist gilt dafür?",
        "Was steht im Mietvertrag zur Kündigung?",
    ) == "mietvertrag kündigung frist"


def test_rank_evidence_prefers_text_match_and_preserves_stable_ties():
    items = [
        {"relative_path": "fristen_regeln.md", "preview_text": "Allgemeine Information", "document_id": "a"},
        {"relative_path": "handbuch.md", "preview_text": "Frist und Kündigung", "document_id": "b"},
        {"relative_path": "handbuch_2.md", "preview_text": "Frist und Kündigung", "document_id": "c"},
    ]
    ranked = qa_runtime.rank_evidence_hits(items, "Welche Frist gilt für Kündigung?")
    assert [hit["document_id"] for hit in ranked] == ["b", "c", "a"]
    assert items[0]["document_id"] == "a"  # incoming ranking stays intact


def test_answer_excerpts_are_bounded_and_cover_distinct_documents():
    hits = [
        {"document_id": "doc1", "relative_path": "A.md", "citation_label": "A:1",
         "preview_text": "   First   finding  "},
        {"document_id": "doc1", "relative_path": "A.md", "citation_label": "A:2",
         "preview_text": "Duplicate document"},
        {"document_id": "doc2", "relative_path": "B.md", "citation_label": "B:1",
         "preview_text": "Other finding"},
        {"document_id": "doc3", "relative_path": "C.md", "citation_label": "C:1",
         "preview_text": "Third finding"},
        {"document_id": "doc4", "relative_path": "D.md", "citation_label": "D:1",
         "preview_text": "Fourth finding"},
    ]
    summary = qa_runtime.answer_excerpts(hits)
    assert "A:1" in summary and "B:1" in summary and "C:1" in summary
    assert "A:2" not in summary and "D:1" not in summary
    assert "First finding" in summary
    assert len(summary) < 500


def test_qa_returns_excerpts_with_origins_but_no_new_claims(monkeypatch):
    calls = []
    hits = [
        {"document_id": "one", "relative_path": "one.md",
         "citation_label": "one:1", "segment_id": "one_seg",
         "source_id": "space_a", "preview_text": "Kündigungsfrist: drei Monate."},
        {"document_id": "two", "relative_path": "two.md",
         "citation_label": "two:1", "segment_id": "two_seg",
         "source_id": "space_a", "preview_text": "Ausnahme bei Sonderkündigung."},
    ]
    class FakeClient:
        def __init__(self, timeout): self.timeout = timeout
        def __enter__(self): return self
        def __exit__(self, *args): return False
    def fake_search(client, query, payload):
        calls.append((query, payload.source_scope))
        return {"hits": hits}
    monkeypatch.setattr(qa_runtime.httpx, "Client", FakeClient)
    monkeypatch.setattr(qa_runtime, "run_search", fake_search)
    result = qa_runtime.answer(qa_runtime.QaRequest(
        question="Kündigungsfrist", source_scope=["space_a"]))
    assert calls == [("Kündigungsfrist", ["space_a"])]
    assert "Gefundene Textstellen:" in result["answer_text"]
    assert "Kündigungsfrist: drei Monate." in result["answer_text"]
    assert "Ausnahme bei Sonderkündigung." in result["answer_text"]
    assert result["citations"] == ["one:1", "two:1"]
    assert result["evidence_signal"]["calibrated"] is False
