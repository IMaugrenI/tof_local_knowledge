from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from _shared_db import db_conn, make_id
from _shared_extract import extract_blocks, safe_resolve_under
from translator import ExtractionTranslator

app = FastAPI(title='tof_local_knowledge_extractor_api', version='0.2.0')
translator = ExtractionTranslator()
SOURCE_ROOT = Path('/sources').resolve()


class ExtractRequest(BaseModel):
    source_id: str
    root_path: str
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
            if not document_id:
                cur.execute(
                    'SELECT document_id FROM documents WHERE source_id = %s AND relative_path = %s',
                    (payload.source_id, relative_path),
                )
                row = cur.fetchone()
                document_id = row['document_id'] if row else make_id('doc')

            target = safe_resolve_under(root, root / relative_path)
            raw_blocks, warnings = extract_blocks(target)
            translated = translator.translate(document_id=document_id, raw_blocks=raw_blocks)
            translated['warnings'] = warnings + translated.get('warnings', [])

            if payload.persist:
                outcome = 'done' if translated['segment_count'] > 0 else 'failed'
                coverage = 1.0 if translated['read_status'] == 'fully_read' else 0.0

                cur.execute(
                    '''
                    INSERT INTO extractions (extraction_id, document_id, extractor_name, outcome, coverage, warnings)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    ''',
                    (make_id('extract'), document_id, 'runtime_extractor', outcome, coverage, str(translated['warnings']).replace("'", '"')),
                )
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
                        'done' if translated['segment_count'] > 0 else 'failed',
                    ),
                )
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
