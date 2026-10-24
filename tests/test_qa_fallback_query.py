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
