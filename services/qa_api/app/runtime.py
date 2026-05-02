import os
import re

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title='tof_local_knowledge_qa_api', version='0.2.0')
SEARCH_API_URL = os.environ.get('SEARCH_API_URL', 'http://search_api:8105/search')

QUESTION_STOPWORDS = {
    'a',
    'an',
    'about',
    'and',
    'are',
    'as',
    'does',
    'do',
    'for',
    'from',
    'how',
    'is',
    'it',
    'me',
    'of',
    'on',
    'or',
    'say',
    'says',
    'tell',
    'the',
    'to',
    'was',
    'what',
    'when',
    'where',
    'which',
    'who',
    'why',
    'with',
}


class QaRequest(BaseModel):
    question: str = Field(min_length=1)
    source_scope: list[str] | None = None
    limit: int = Field(default=5, ge=1, le=20)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'qa_api'}


def fallback_search_query(question: str) -> str:
    """Create a simple keyword query for local FTS fallback.

    The search API uses Postgres websearch_to_tsquery. A full natural-language
    question can become too restrictive because many question words are kept as
    required terms. The fallback keeps content-bearing terms only.
    """

    tokens = re.findall(r"[A-Za-z0-9_]+", question.lower())
    keywords = [token for token in tokens if token not in QUESTION_STOPWORDS and len(token) > 1]
    return ' '.join(keywords).strip()


def run_search(client: httpx.Client, query: str, payload: QaRequest) -> dict:
    response = client.post(
        SEARCH_API_URL,
        json={
            'query': query,
            'source_scope': payload.source_scope or [],
            'limit': payload.limit,
        },
    )
    response.raise_for_status()
    return response.json()


@app.post('/answer')
def answer(payload: QaRequest):
    attempted_queries = [payload.question]

    with httpx.Client(timeout=20.0) as client:
        data = run_search(client, payload.question, payload)
        hits = data.get('hits', [])

        fallback_query = fallback_search_query(payload.question)
        if not hits and fallback_query and fallback_query != payload.question.lower().strip():
            attempted_queries.append(fallback_query)
            data = run_search(client, fallback_query, payload)
            hits = data.get('hits', [])

    if not hits:
        return {
            'answer_text': 'Keine belastbare Antwort gefunden. Es wurden keine passenden Fundstellen im erlaubten Scope gefunden.',
            'confidence': 0.0,
            'citations': [],
            'used_documents': [],
            'uncertainties': ['no_evidence'],
            'search_queries': attempted_queries,
        }

    primary = hits[0]
    citations = [hit['citation_label'] for hit in hits]
    used_documents = sorted({hit['document_id'] for hit in hits})
    evidence_lines = [
        f"- [{hit['citation_label']}] {hit['preview_text']}" for hit in hits
    ]

    uncertainties = [] if len(hits) >= 2 else ['limited_evidence']
    answer_text = (
        'Belegbasierte Kurzantwort:\n'
        f"Stärkster Treffer aus {primary['relative_path']}: {primary['preview_text']}\n\n"
        'Verwendete Fundstellen:\n' + '\n'.join(evidence_lines)
    )

    return {
        'answer_text': answer_text,
        'confidence': min(0.95, 0.35 + 0.1 * len(hits)),
        'citations': citations,
        'used_documents': used_documents,
        'uncertainties': uncertainties,
        'search_queries': attempted_queries,
    }
