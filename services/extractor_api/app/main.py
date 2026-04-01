from fastapi import FastAPI
from pydantic import BaseModel

from translator import ExtractionTranslator

app = FastAPI(title='tof_local_knowledge_extractor_api', version='0.1.0')
translator = ExtractionTranslator()


class RawBlock(BaseModel):
    kind: str = 'text_block'
    page_no: int | None = None
    text: str = ''


class TranslateRequest(BaseModel):
    document_id: str
    raw_blocks: list[RawBlock]


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'extractor_api'}


@app.post('/translate/extraction')
def translate_extraction(payload: TranslateRequest):
    data = translator.translate(
        document_id=payload.document_id,
        raw_blocks=[block.model_dump() for block in payload.raw_blocks],
    )
    return data
