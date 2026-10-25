import json
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from _shared_db import db_conn, make_id
from _shared_extract import extract_blocks, safe_resolve_under
from translator import ExtractionTranslator

app = FastAPI(title='tof_local_knowledge_extractor_api', version='0.3.0')
translator = ExtractionTranslator()
SOURCE_ROOT = Path('/sources').resolve()


class ExtractRequest(BaseModel):
    source_id: str = Field(min_length=1)
    root_path: str = Field(min_length=1)
    relative_path: str | None = None
    document_id: str | None = None
    persist: bool = True


@app.get('/health')
def health():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
    return {'status': 'ok', 'service': 'extractor_api'}


@app.post('/extract/file')
def extract_file(payload: ExtractRequest):
    root = safe_resolve_under(SOURCE_ROOT, payload.root_path)
    with db_conn() as conn:
        with conn.cursor() as cur:
            document_id = payload.document_id
            relative_path = payload.relative_path
            if not relative_path and document_id:
                cur.execute(
                    'SELECT relative_path FROM documents WHERE document_id = %s AND source_id = %s',
                    (document_id, payload.source_id),
                )
                row = cur.fetchone()
                if not row:
                    return {'status': 'error', 'detail': 'unknown_document'}
                relative_path = row['relative_path']
            if not relative_path:
                return {'status': 'error', 'detail': 'relative_path_required'}

            cur.execute(
                'SELECT document_id FROM documents WHERE source_id = %s AND relative_path = %s',
                (payload.source_id, relative_path),
            )
            existing = cur.fetchone()
            if document_id and (not existing or existing['document_id'] != document_id):
                return {'status': 'error', 'detail': 'document_source_mismatch'}
            document_id = existing['document_id'] if existing else make_id('doc')

            target = safe_resolve_under(root, root / relative_path)
            if not target.is_file():
                return {'status': 'error', 'detail': 'file_not_found'}
            raw_blocks, warnings = extract_blocks(target)
            translated = translator.translate(document_id=document_id, raw_blocks=raw_blocks)
            translated['warnings'] = warnings + translated.get('warnings', [])

            if payload.persist:
                completed = translated['segment_count'] > 0
                outcome = 'done' if completed else 'failed'
                coverage = 1.0 if translated['read_status'] == 'fully_read' else 0.0

                # Persist document metadata before its extraction event so a
                # first-time direct extraction also satisfies the foreign key.
                cur.execute(
                    '''
                    INSERT INTO documents (
                      document_id, source_id, relative_path, file_name, read_status, extraction_status
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_id, relative_path) DO UPDATE
                    SET read_status = EXCLUDED.read_status,
                        extraction_status = EXCLUDED.extraction_status
                    ''',
                    (
                        document_id,
                        payload.source_id,
                        relative_path,
                        Path(relative_path).name,
                        translated['read_status'],
                        outcome,
                    ),
                )
                cur.execute(
                    '''
                    INSERT INTO extractions (extraction_id, document_id, extractor_name, outcome, coverage, warnings)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    ''',
                    (make_id('extract'), document_id, 'runtime_extractor', outcome,
                     coverage, json.dumps(translated['warnings'], ensure_ascii=False)),
                )
                if completed:
                    # Failed attempts preserve earlier segments for recovery.
                    # Search only exposes segments whose document status is done.
                    cur.execute('DELETE FROM document_segments WHERE document_id = %s', (document_id,))
                    for segment in translated['segments']:
                        cur.execute(
                            '''
                            INSERT INTO document_segments (
                              segment_id, document_id, segment_kind, page_no, ordinal, citation_label, text_content
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ''',
                            (
                                segment['segment_id'],
                                document_id,
                                segment['segment_kind'],
                                segment['page_no'],
                                segment['ordinal'],
                                segment['citation_label'],
                                segment['text'],
                            ),
                        )

    return {
        'status': 'ok',
        'document_id': document_id,
        'relative_path': relative_path,
        'raw_block_count': len(raw_blocks),
        'segment_count': translated['segment_count'],
        'read_status': translated['read_status'],
        'warnings': translated['warnings'],
        'segments': translated['segments'],
    }
