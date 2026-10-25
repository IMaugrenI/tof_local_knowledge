from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

from _shared_db import db_conn

app = FastAPI(title='tof_local_knowledge_search_api', version='0.4.0')


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    source_scope: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)


@app.get('/health')
def health():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
    return {'status': 'ok', 'service': 'search_api'}


@app.get('/evidence/{segment_id}')
def evidence(segment_id: str = Path(min_length=1, max_length=128, pattern=r'^[a-zA-Z0-9_-]+
def search(payload: SearchRequest):
    sql = '''
    SELECT
      d.document_id,
      d.source_id,
      d.relative_path,
      s.segment_id,
      s.citation_label,
      s.text_content,
      ts_rank_cd(to_tsvector('simple', s.text_content), websearch_to_tsquery('simple', %s)) AS score
    FROM document_segments s
    JOIN documents d ON d.document_id = s.document_id
    JOIN sources source ON source.source_id = d.source_id
    WHERE d.extraction_status = 'done'
      AND source.enabled IS TRUE
      AND to_tsvector('simple', s.text_content) @@ websearch_to_tsquery('simple', %s)
    '''
    params = [payload.query, payload.query]
    if payload.source_scope:
        sql += ' AND d.source_id = ANY(%s) '
        params.append(payload.source_scope)
    sql += ' ORDER BY score DESC, d.relative_path ASC LIMIT %s '
    params.append(payload.limit)

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    hits = []
    for row in rows:
        snippet = row['text_content'][:400]
        hits.append(
            {
                'document_id': row['document_id'],
                'source_id': row['source_id'],
                'relative_path': row['relative_path'],
                'segment_id': row['segment_id'],
                'citation_label': row['citation_label'],
                'preview_text': snippet,
                'score': float(row['score']),
            }
        )

    return {
        'query': payload.query,
        'source_scope': payload.source_scope or [],
        'count': len(hits),
        'hits': hits,
    }
)):
    """Read-only exact excerpt, restricted to *current* indexed evidence.

    This endpoint is local single-user tooling, not an authorization system.
    Its visibility is bounded by the existing loopback-only Compose setup.
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT s.segment_id, s.document_id, d.source_id,
                       d.relative_path, s.citation_label, s.segment_kind,
                       s.page_no, s.ordinal, LEFT(s.text_content, 2000) AS excerpt
                FROM document_segments s
                JOIN documents d ON d.document_id = s.document_id
                JOIN sources source ON source.source_id = d.source_id
                WHERE s.segment_id = %s
                  AND d.extraction_status = 'done'
                  AND source.enabled IS TRUE
                LIMIT 1
                ''',
                (segment_id,),
            )
            row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='evidence_not_available')
    return {'evidence': row, 'truncated_to_chars': 2000,
            'scope': 'local_single_user_only'}


@app.post('/search')
def search(payload: SearchRequest):
    sql = '''
    SELECT
      d.document_id,
      d.source_id,
      d.relative_path,
      s.segment_id,
      s.citation_label,
      s.text_content,
      ts_rank_cd(to_tsvector('simple', s.text_content), websearch_to_tsquery('simple', %s)) AS score
    FROM document_segments s
    JOIN documents d ON d.document_id = s.document_id
    JOIN sources source ON source.source_id = d.source_id
    WHERE d.extraction_status = 'done'
      AND source.enabled IS TRUE
      AND to_tsvector('simple', s.text_content) @@ websearch_to_tsquery('simple', %s)
    '''
    params = [payload.query, payload.query]
    if payload.source_scope:
        sql += ' AND d.source_id = ANY(%s) '
        params.append(payload.source_scope)
    sql += ' ORDER BY score DESC, d.relative_path ASC LIMIT %s '
    params.append(payload.limit)

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    hits = []
    for row in rows:
        snippet = row['text_content'][:400]
        hits.append(
            {
                'document_id': row['document_id'],
                'source_id': row['source_id'],
                'relative_path': row['relative_path'],
                'segment_id': row['segment_id'],
                'citation_label': row['citation_label'],
                'preview_text': snippet,
                'score': float(row['score']),
            }
        )

    return {
        'query': payload.query,
        'source_scope': payload.source_scope or [],
        'count': len(hits),
        'hits': hits,
    }
