"""Optional local, bounded Ollama embeddings for existing pgvector(768) segments.

This helper intentionally cannot resolve user-provided network endpoints. Both
indexing and search continue to work normally when the feature is disabled
or the local model is missing, slow, incompatible, or returns malformed data.
"""
from __future__ import annotations

import math
import os
import re

import httpx

VECTOR_DIMENSIONS = 768
MAX_EMBED_BATCH = 12
MAX_TEXT_CHARS = 1200
EMBED_URL = "http://ollama:11434/api/embed"


def configured_model() -> str | None:
    if os.environ.get("ENABLE_OLLAMA", "").strip().lower() != "true":
        return None
    model = os.environ.get("KNOWLEDGE_EMBED_MODEL", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,96}", model) or "://" in model:
        return None
    return model


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Get exactly one finite 768-dimensional vector for each short text.

    No files, paths, history, credentials or arbitrary network destinations
    are sent. Returns None instead of propagating failures into indexing or
    evidence-backed lexical search.
    """
    model = configured_model()
    if not model or not 1 <= len(texts) <= MAX_EMBED_BATCH:
        return None
    if not all(isinstance(t, str) and t.strip() for t in texts):
        return None
    try:
        reply = httpx.post(
            EMBED_URL,
            json={"model": model, "input": [t[:MAX_TEXT_CHARS] for t in texts],
                  "truncate": True},
            timeout=7.0,
        )
        reply.raise_for_status()
        data = reply.json()
        vectors = data.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            return None
        validated: list[list[float]] = []
        for vector in vectors:
            if not isinstance(vector, list) or len(vector) != VECTOR_DIMENSIONS:
                return None
            if not all(type(v) in {float, int} and math.isfinite(v)
                       and abs(v) <= 1000 for v in vector):
                return None
            values = [float(v) for v in vector]
            if not any(v != 0 for v in values):
                return None
            validated.append(values)
        return validated
    except (httpx.HTTPError, ValueError, TypeError, AttributeError, KeyError):
        return None
