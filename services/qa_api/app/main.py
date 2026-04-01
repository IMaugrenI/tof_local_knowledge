from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='tof_local_knowledge_qa_api', version='0.1.0')


class QaRequest(BaseModel):
    question: str
    citations: list[str] = []


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'qa_api'}


@app.post('/answer')
def answer(payload: QaRequest):
    if not payload.citations:
        return {
            'answer_text': 'Keine belastbare Antwort ohne Fundstellen.',
            'confidence': 0.0,
            'citations': [],
            'uncertainties': ['no_evidence'],
        }
    return {
        'answer_text': 'Antwort auf Basis der übergebenen Fundstellen erstellt.',
        'confidence': 0.6,
        'citations': payload.citations,
        'uncertainties': [],
    }
