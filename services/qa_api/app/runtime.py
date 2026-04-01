import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title='tof_local_knowledge_qa_api', version='0.2.0')
SEARCH_API_URL = os.environ.get('SEARCH_API_URL', 'http://search_api:8105/search')


class QaRequest(BaseModel):
    question: str = Field(min_length=1)
    source_scope: list[str] | None = None
    limit: int = Field(default=5, ge=1, le=20)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'qa_api'}


@app.post('/answer')
def answer(payload: QaRequest):
    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            SEARCH_API_URL,
            json={
                'query': payload.question,
                'source_scope': payload.source_scope or [],
                'limit': payload.limit,
            },
        )
        response.raise_for_status()
        data = response.json()

    hits = data.get('hits', [])
    if not hits:
        return {
            'answer_text': 'Keine belastbare Antwort gefunden. Es wurden keine passenden Fundstellen im erlaubten Scope gefunden.',
            'confidence': 0.0,
            'citations': [],
            'used_documents': [],
            'uncertainties': ['no_evidence'],
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
    }
