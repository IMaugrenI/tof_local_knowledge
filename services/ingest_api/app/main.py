from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='tof_local_knowledge_ingest_api', version='0.1.0')


class ScanRequest(BaseModel):
    source_id: str
    root_path: str


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'ingest_api'}


@app.post('/scan/plan')
def plan_scan(payload: ScanRequest):
    return {
        'status': 'accepted',
        'source_id': payload.source_id,
        'root_path': payload.root_path,
        'next_step': 'extract_and_translate',
    }
