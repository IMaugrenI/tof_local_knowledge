"""Focused safety checks for optional local model ranking, not factual synthesis."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from httpx import ConnectError

MODULE = Path(__file__).resolve().parents[1] / "services/qa_api/app/runtime.py"
spec = importlib.util.spec_from_file_location("qa_k23_model_rank", MODULE)
assert spec is not None and spec.loader is not None
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def test_ollama_opt_in_only_accepts_local_restricted_endpoint(monkeypatch):
    monkeypatch.delenv("ENABLE_OLLAMA", raising=False)
    monkeypatch.setenv("QA_OLLAMA_MODEL", "nomic-embed-text:latest")
    assert qa._local_ollama_target() is None

    monkeypatch.setenv("ENABLE_OLLAMA", "true")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://external.example:11434")
    assert qa._local_ollama_target() is None
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:not-a-port")
    assert qa._local_ollama_target() is None
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434/path")
    assert qa._local_ollama_target() is None
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    assert qa._local_ollama_target() == (
        "http://ollama:11434/api/generate", "nomic-embed-text:latest"
    )


def _hits():
    return [
        {"document_id": "d1", "relative_path": "one.md", "citation_label": "a",
         "preview_text": "Shipping policy: two days.", "source_id": "s1"},
        {"document_id": "d2", "relative_path": "two.md", "citation_label": "b",
         "preview_text": "Vacation policy: 30 days.", "source_id": "s1"},
    ]


def test_local_model_proposes_only_a_valid_permutation(monkeypatch):
    monkeypatch.setenv("ENABLE_OLLAMA", "true")
    monkeypatch.setenv("QA_OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")
    sent = []

    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return {"response": json.dumps({"order": ["hit_1", "hit_0"]})}

    def fake_post(url, json, timeout):
        sent.append((url, json, timeout))
        return FakeResponse()

    monkeypatch.setattr(qa.httpx, "post", fake_post)
    original = _hits()
    ordered, success = qa.optional_model_rerank(original, "Vacation policy?")
    assert success is True
    assert [h["citation_label"] for h in ordered] == ["b", "a"]
    assert [h["citation_label"] for h in original] == ["a", "b"]
    assert sent[0][0] == "http://ollama:11434/api/generate"
    assert sent[0][1]["stream"] is False
    assert sent[0][2] == 6.0
    assert "Do not answer the question" in sent[0][1]["prompt"]


def test_untrusted_model_output_and_outage_never_create_or_remove_evidence(monkeypatch):
    monkeypatch.setenv("ENABLE_OLLAMA", "true")
    monkeypatch.setenv("QA_OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama:11434")

    class FakeResponse:
        def __init__(self, text): self.text = text
        def raise_for_status(self): pass
        def json(self): return {"response": self.text}

    original = _hits()
    for reply in [
        '{"order":["hit_0","foreign"]}',
        '{"order":["hit_0","hit_0"]}',
        '{"answer":"A fabricated answer"}',
        'not-json',
    ]:
        monkeypatch.setattr(qa.httpx, "post", lambda *a, **kw: FakeResponse(reply))
        ranked, used = qa.optional_model_rerank(original, "Vacation policy?")
        assert ranked is original and used is False

    def unavailable(*args, **kwargs):
        raise ConnectError("model unavailable")
    monkeypatch.setattr(qa.httpx, "post", unavailable)
    ranked, used = qa.optional_model_rerank(original, "Vacation policy?")
    assert ranked is original and used is False
