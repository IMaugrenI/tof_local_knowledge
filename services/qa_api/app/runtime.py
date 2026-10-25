import os
import re

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title='tof_local_knowledge_qa_api', version='0.4.0')
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
    # German question / function words, but not content-bearing domain terms.
    'ab', 'alle', 'als', 'am', 'an', 'auf', 'aus', 'bei', 'bin',
    'das', 'dass', 'dem', 'den', 'der', 'des', 'die', 'dies',
    'diese', 'dieser', 'ein', 'eine', 'einen', 'einer', 'eines',
    'er', 'es', 'für', 'hat', 'haben', 'ich', 'im', 'in', 'ist',
    'kann', 'können', 'man', 'mit', 'mir', 'nach', 'nicht',
    'noch', 'oder', 'sich', 'sie', 'sind', 'über', 'um', 'und',
    'uns', 'von', 'vor', 'war', 'was', 'welche', 'welcher',
    'welches', 'wenn', 'wer', 'wie', 'wieso', 'wird', 'wo',
    'wobei', 'womit', 'wurde', 'wurden', 'zu', 'zum', 'zur',
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

    # Unicode word matching preserves umlauts, accents and compound terms.
    tokens = re.findall(r"[^\\W_]+(?:_[^\\W_]+)*", question.casefold(), flags=re.UNICODE)
    unique = dict.fromkeys(
        token for token in tokens
        if token not in QUESTION_STOPWORDS and len(token) > 1
    )
    return ' '.join(list(unique)[:8])


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


def evidence_signal(hits: list[dict], strategy: str) -> dict[str, object]:
    """Describe retrieval coverage, not factual correctness."""
    documents = len({hit['document_id'] for hit in hits})
    if not hits:
        status = 'no_evidence'
    elif strategy == 'broad':
        status = 'broad_keyword_matches'
    elif documents >= 2:
        status = 'multiple_document_matches'
    else:
        status = 'single_document_matches'
    return {
        'status': status,
        'matching_segments': len(hits),
        'distinct_documents': documents,
        'search_strategy': strategy,
        'calibrated': False,
    }


@app.post('/answer')
def answer(payload: QaRequest):
    attempted_queries = [payload.question]
    strategy = 'original_question'

    with httpx.Client(timeout=20.0) as client:
        data = run_search(client, payload.question, payload)
        hits = data.get('hits', [])

        fallback_query = fallback_search_query(payload.question)
        if not hits and fallback_query and fallback_query != payload.question.lower().strip():
            attempted_queries.append(fallback_query)
            data = run_search(client, fallback_query, payload)
            hits = data.get('hits', [])
            if hits:
                strategy = 'keywords'
        if not hits and fallback_query:
            terms = fallback_query.split()
            if len(terms) >= 2:
                # PostgreSQL websearch_to_tsquery interprets OR as disjunction.
                # Only try this broad last resort if stricter queries failed.
                broad_query = ' OR '.join(terms[:6])
                attempted_queries.append(broad_query)
                data = run_search(client, broad_query, payload)
                hits = data.get('hits', [])
                if hits:
                    strategy = 'broad'

    if not hits:
        return {
            'answer_text': 'Keine belastbare Antwort gefunden. Es wurden keine passenden Fundstellen im erlaubten Scope gefunden.',
            'confidence': 0.0,
            'citations': [],
            'used_documents': [],
            'evidence_refs': [],
            'uncertainties': ['no_evidence'],
            'search_queries': attempted_queries,
            'evidence_signal': evidence_signal([], 'none'),
        }

    primary = hits[0]
    citations = [hit['citation_label'] for hit in hits]
    used_documents = sorted({hit['document_id'] for hit in hits})
    evidence_refs = [{'segment_id': hit['segment_id'], 'document_id': hit['document_id'], 'source_id': hit['source_id'], 'relative_path': hit['relative_path'], 'citation_label': hit['citation_label']} for hit in hits]
    evidence_lines = [
        f"- [{hit['citation_label']}] {hit['preview_text']}" for hit in hits
    ]

    if strategy == 'broad':
        uncertainties = ['broad_keyword_search', 'confidence_uncalibrated']
    else:
        uncertainties = ['confidence_uncalibrated']
    # Confidence remains a compatibility-only heuristic, never a calibrated
    # probability of factual correctness.
    if len({hit['document_id'] for hit in hits}) < 2:
        uncertainties.append('limited_independent_sources')
    answer_text = (
        'Belegbasierte Kurzantwort (Quellenauszüge, keine unabhängige Verifikation):\n'
        f"Stärkster Treffer aus {primary['relative_path']}: {primary['preview_text']}\n\n"
        'Verwendete Fundstellen:\n' + '\n'.join(evidence_lines)
    )

    return {
        'answer_text': answer_text,
        'confidence': min(0.95, 0.35 + 0.1 * len(hits)),
        'citations': citations,
        'used_documents': used_documents,
        'evidence_refs': evidence_refs,
        'uncertainties': uncertainties,
        'search_queries': attempted_queries,
        'evidence_signal': evidence_signal(hits, strategy),
    }
