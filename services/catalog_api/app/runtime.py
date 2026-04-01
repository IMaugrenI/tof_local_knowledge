from fastapi import FastAPI, Query
from pydantic import BaseModel

from _shared_db import db_conn, make_id

app = FastAPI(title='tof_local_knowledge_catalog_api', version='0.2.0')


class SourceUpsert(BaseModel):
    source_id: str
    display_name: str
    mount_key: str
    mount_path: str
    enabled: bool = True
    scan_policy: str = 'manual'


class DocumentUpsert(BaseModel):
    document_id: str
    source_id: str
    relative_path: str
    file_name: str
    mime_type: str | None = None
    size_bytes: int | None = None
    content_fingerprint: str | None = None
    read_status: str
    extraction_status: str


class SegmentItem(BaseModel):
    segment_id: str
    segment_kind: str
    ordinal: int
    page_no: int | None = None
    citation_label: str
    text: str


class SegmentReplace(BaseModel):
    document_id: str
    segments: list[SegmentItem]


@app.get('/health')
def health():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
    return {'status': 'ok', 'service': 'catalog_api'}


@app.get('/sources')
def list_sources():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM sources ORDER BY display_name, source_id')
            return {'sources': cur.fetchall()}


@app.post('/sources/upsert')
def upsert_source(payload: SourceUpsert):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO sources (source_id, display_name, mount_key, mount_path, enabled, scan_policy)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO UPDATE
                SET display_name = EXCLUDED.display_name,
                    mount_key = EXCLUDED.mount_key,
                    mount_path = EXCLUDED.mount_path,
                    enabled = EXCLUDED.enabled,
                    scan_policy = EXCLUDED.scan_policy
                ''',
                (
                    payload.source_id,
                    payload.display_name,
                    payload.mount_key,
                    payload.mount_path,
                    payload.enabled,
                    payload.scan_policy,
                ),
            )
    return {'status': 'ok', 'source_id': payload.source_id}


@app.get('/documents')
def list_documents(source_id: str | None = None, limit: int = Query(default=100, le=1000)):
    with db_conn() as conn:
        with conn.cursor() as cur:
            if source_id:
                cur.execute(
                    'SELECT * FROM documents WHERE source_id = %s ORDER BY relative_path LIMIT %s',
                    (source_id, limit),
                )
            else:
                cur.execute('SELECT * FROM documents ORDER BY created_at DESC LIMIT %s', (limit,))
            return {'documents': cur.fetchall()}


@app.post('/documents/upsert')
def upsert_document(payload: DocumentUpsert):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO documents (
                  document_id, source_id, relative_path, file_name, mime_type, size_bytes,
                  content_fingerprint, read_status, extraction_status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE
                SET mime_type = EXCLUDED.mime_type,
                    size_bytes = EXCLUDED.size_bytes,
                    content_fingerprint = EXCLUDED.content_fingerprint,
                    read_status = EXCLUDED.read_status,
                    extraction_status = EXCLUDED.extraction_status
                ''',
                (
                    payload.document_id,
                    payload.source_id,
                    payload.relative_path,
                    payload.file_name,
                    payload.mime_type,
                    payload.size_bytes,
                    payload.content_fingerprint,
                    payload.read_status,
                    payload.extraction_status,
                ),
            )
    return {'status': 'ok', 'document_id': payload.document_id}


@app.post('/segments/replace')
def replace_segments(payload: SegmentReplace):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM document_segments WHERE document_id = %s', (payload.document_id,))
            for segment in payload.segments:
                cur.execute(
                    '''
                    INSERT INTO document_segments (
                      segment_id, document_id, segment_kind, page_no, ordinal, citation_label, text_content
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''',
                    (
                        segment.segment_id or make_id('seg'),
                        payload.document_id,
                        segment.segment_kind,
                        segment.page_no,
                        segment.ordinal,
                        segment.citation_label,
                        segment.text,
                    ),
                )
    return {'status': 'ok', 'document_id': payload.document_id, 'segment_count': len(payload.segments)}


@app.get('/segments/{document_id}')
def get_segments(document_id: str):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT segment_id, document_id, segment_kind, page_no, ordinal, citation_label, text_content
                FROM document_segments
                WHERE document_id = %s
                ORDER BY ordinal
                ''',
                (document_id,),
            )
            return {'segments': cur.fetchall()}
