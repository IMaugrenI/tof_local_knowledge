"""Optional semantic indexing + retrieval uses only existing local pgvector.

These isolated tests never start Ollama, PostgreSQL or a second Compose stack.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import _shared_embeddings as embeddings

ROOT = Path(__file__).resolve().parents[1]


def test_embeddings_explicit_opt_in_and_fixed_local_endpoint(monkeypatch):
    monkeypatch.delenv("ENABLE_OLLAMA", raising=False)
    monkeypatch.setenv("KNOWLEDGE_EMBED_MODEL", "nomic-embed-text")
    assert embeddings.embed_texts(["demo"]) is None
    monkeypatch.setenv("ENABLE_OLLAMA", "true")
    monkeypatch.setenv("KNOWLEDGE_EMBED_MODEL", "https://external.example/x")
    assert embeddings.configured_model() is None
    monkeypatch.setenv("KNOWLEDGE_EMBED_MODEL", "nomic-embed-text")
    observed = []

    class Response:
        def raise_for_status(self): pass
        def json(self): return {"embeddings": [[0.5] * 768]}

    def fake_post(url, json, timeout):
        observed.append((url, json, timeout))
        return Response()

    monkeypatch.setattr(embeddings.httpx, "post", fake_post)
    result = embeddings.embed_texts(["example"])
    assert result == [[0.5] * 768]
    assert observed[0][0] == "http://ollama:11434/api/embed"
    assert observed[0][1]["input"] == ["example"]
    assert observed[0][2] == 7.0


def test_embedding_malformed_dimensions_nan_and_outages_fail_closed(monkeypatch):
    monkeypatch.setenv("ENABLE_OLLAMA", "true")
    monkeypatch.setenv("KNOWLEDGE_EMBED_MODEL", "nomic-embed-text")
    class Response:
        def __init__(self, value): self.value = value
        def raise_for_status(self): pass
        def json(self): return {"embeddings": [self.value]}
    for value in ([[0.1] * 767], [[0.1] * 767 + [float("nan")]],
                  [[0.0] * 768], [[0.1] * 767 + [True]]):
        monkeypatch.setattr(embeddings.httpx, "post",
                            lambda *args, **kwargs: Response(value[0]))
        assert embeddings.embed_texts(["demo"]) is None
    def down(*args, **kwargs):
        raise embeddings.httpx.ConnectError("unavailable")
    monkeypatch.setattr(embeddings.httpx, "post", down)
    assert embeddings.embed_texts(["demo"]) is None
    assert embeddings.embed_texts(["x"] * 13) is None


def test_semantic_search_enforces_status_scope_threshold_and_bounded_limit(monkeypatch):
    queries = []
    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, sql, params): queries.append((sql, params))
        def fetchall(self): return [{
            "document_id":"doc1","source_id":"space-a",
            "relative_path":"guide.md","segment_id":"seg1",
            "citation_label":"guide#1","page_no":1,
            "segment_kind":"paragraph","ordinal":0,
            "text_content":"Text on this source.", "score":0.82,
        }]
    class Conn:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def cursor(self): return Cursor()

    shared = types.ModuleType("_shared_db")
    shared.db_conn = lambda: Conn()
    monkeypatch.setitem(sys.modules, "_shared_db", shared)
    spec = importlib.util.spec_from_file_location(
        "semantic_search_test", ROOT / "services/search_api/app/runtime.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "embed_texts", lambda texts: [[0.1]*768])
    result = mod.search(mod.SearchRequest(
        query="synonym", source_scope=["space-a"], semantic=True, limit=100
    ))
    sql, params = queries[0]
    assert "d.extraction_status = 'done'" in sql
    assert "source.enabled IS TRUE" in sql
    assert "s.embedding IS NOT NULL" in sql
    assert "<= 0.25" in sql
    assert "d.source_id = ANY(%s)" in sql
    assert params[2] == ["space-a"]
    assert params[-1] == 20
    assert result["count"] == 1
    assert result["hits"][0]["match_kind"] == "semantic_similarity"
    assert result["hits"][0]["preview_text"] == "Text on this source."
    monkeypatch.setattr(mod, "embed_texts", lambda texts: None)
    assert mod.search(mod.SearchRequest(query="synonym", semantic=True))["hits"] == []
    assert len(queries) == 1


def test_qa_only_uses_semantic_after_strict_retrieval_and_attributes_quotes(monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "qa_semantic_test", ROOT / "services/qa_api/app/runtime.py"
    )
    assert spec and spec.loader
    qa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qa)
    monkeypatch.setenv("ENABLE_OLLAMA", "true")
    monkeypatch.setenv("KNOWLEDGE_EMBED_MODEL", "nomic-embed-text")
    monkeypatch.delenv("QA_OLLAMA_MODEL", raising=False)
    requests = []
    class Client:
        def __init__(self, timeout): pass
        def __enter__(self): return self
        def __exit__(self, *args): return False
    monkeypatch.setattr(qa.httpx, "Client", Client)

    def fake_search(client, query, payload, *, semantic=False):
        requests.append((query, semantic, payload.source_scope))
        if semantic:
            return {"hits":[{
                "document_id":"doc1","source_id":"space-a",
                "relative_path":"manual.md","segment_id":"seg1",
                "citation_label":"manual#1","preview_text":"Eine Kündigung ist möglich.",
            }]}
        return {"hits":[]}
    monkeypatch.setattr(qa, "run_search", fake_search)
    outcome = qa.answer(qa.QaRequest(
        question="Kann man einen Vertrag beenden?", source_scope=["space-a"]))
    assert requests[-1][1] is True
    assert all(x[2] == ["space-a"] for x in requests)
    assert outcome["evidence_signal"]["search_strategy"] == "semantic_similarity"
    assert "semantic_similarity_not_factual_verification" in outcome["uncertainties"]
    assert outcome["citations"] == ["manual#1"]
    assert "Eine Kündigung ist möglich." in outcome["answer_text"]

    requests.clear()
    monkeypatch.setenv("ENABLE_OLLAMA", "false")
    outcome = qa.answer(qa.QaRequest(question="Unbekannter Sachverhalt?"))
    assert not any(semantic for _, semantic, _ in requests)
    assert outcome["citations"] == []
    assert outcome["evidence_refs"] == []
