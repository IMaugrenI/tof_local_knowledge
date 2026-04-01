from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title='tof_local_knowledge_catalog_api', version='0.1.0')


class DocumentUpsert(BaseModel):
    document_id: str
    source_id: str
    relative_path: str
    file_name: str
    read_status: str
    extraction_status: str


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'catalog_api'}


@app.post('/documents/upsert')
def upsert_document(payload: DocumentUpsert):
    return {'status': 'accepted', 'document': payload.model_dump()}
