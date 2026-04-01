from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='tof_local_knowledge_search_api', version='0.1.0')


class SearchRequest(BaseModel):
    query: str
    source_scope: list[str] | None = None


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'search_api'}


@app.post('/search')
def search(payload: SearchRequest):
    return {
        'query': payload.query,
        'source_scope': payload.source_scope or [],
        'hits': [],
        'note': 'FTS wiring pending; contract is fixed.',
    }
