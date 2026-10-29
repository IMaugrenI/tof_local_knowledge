from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

from _shared_db import db_conn
from _shared_embeddings import embed_texts
import json

app = FastAPI(title='tof_local_knowledge_search_api', version='0.4.0')


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    source_scope: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)
    semantic: bool = False


@app.get('/health')
def health():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
    return {'status': 'ok', 'service': 'search_api'}


@app.get('/evidence/{segment_id}')
def evidence(segment_id: str = Path(min_length=1, max_length=128)):
    """Read-only inspection of an indexed segment from an enabled source.

    This local single-user endpoint does not grant cross-user authorization.
    """
    if not segment_id.isascii() or not all(c.isalnum() or c in '_-' for c in segment_id):
        raise HTTPException(status_code=400, detail='invalid_segment_id')
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


def semantic_search(payload: SearchRequest) -> dict:
    """Read-only conservative pgvector retrieval, only on explicit request.

    Embedding generation is optional and uses the fixed local Ollama service.
    No embedding or model mismatch -> no semantic hits; lexical path unchanged.
    Similarity is a *relevance heuristic*, never proof of an assertion.
    """
    result = {
        'query': payload.query, 'source_scope': payload.source_scope or [],
        'count': 0, 'hits': [], 'search_strategy': 'semantic_similarity',
    }
    embeddings = embed_texts([payload.query])
    if embeddings is None:
        return result
    query_vector = json.dumps(embeddings[0])
    sql = """
    SELECT d.document_id, d.source_id, d.relative_path,
           s.segment_id, s.citation_label, s.page_no, s.segment_kind,
           s.ordinal, s.text_content,
           1 - (s.embedding <=> %s::vector) AS score
    FROM document_segments s
    JOIN documents d ON d.document_id = s.document_id
    JOIN sources source ON source.source_id = d.source_id
    WHERE d.extraction_status = 'done'
      AND source.enabled IS TRUE
      AND s.embedding IS NOT NULL
      AND (s.embedding <=> %s::vector) <= 0.25
    """
    params = [query_vector, query_vector]
    if payload.source_scope:
        sql += ' AND d.source_id = ANY(%s) '
        params.append(payload.source_scope)
    sql += """ ORDER BY s.embedding <=> %s::vector ASC,
              d.relative_path ASC, s.ordinal ASC, s.segment_id ASC LIMIT %s """
    params.extend([query_vector, min(payload.limit, 20)])
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    result['hits'] = [{
        'document_id': row['document_id'], 'source_id': row['source_id'],
        'relative_path': row['relative_path'], 'segment_id': row['segment_id'],
        'citation_label': row['citation_label'], 'page_no': row['page_no'],
        'segment_kind': row['segment_kind'], 'ordinal': row['ordinal'],
        'preview_text': row['text_content'][:400],
        'score': float(row['score']), 'match_kind': 'semantic_similarity',
    } for row in rows]
    result['count'] = len(result['hits'])
    return result


@app.post('/search')
def search(payload: SearchRequest):
    if payload.semantic:
        return semantic_search(payload)
    # Match the indexed segment together with tokenized relative filename.
    # A CSV row saying "resolved" can then match an "incident" query through
    # incident_log_sample.csv, without exposing absolute filesystem paths.
    searchable = (
        "to_tsvector('simple', s.text_content || ' ' || "
        "translate(d.relative_path, '_./-', '    '))"
    )
    sql = f'''
    SELECT
      d.document_id,
      d.source_id,
      d.relative_path,
      s.segment_id,
      s.citation_label,
      s.page_no,
      s.segment_kind,
      s.ordinal,
      s.text_content,
      ts_rank_cd({searchable}, websearch_to_tsquery('simple', %s)) AS score
    FROM document_segments s
    JOIN documents d ON d.document_id = s.document_id
    JOIN sources source ON source.source_id = d.source_id
    WHERE d.extraction_status = 'done'
      AND source.enabled IS TRUE
      AND {searchable} @@ websearch_to_tsquery('simple', %s)
    '''
    params = [payload.query, payload.query]
    if payload.source_scope:
        sql += ' AND d.source_id = ANY(%s) '
        params.append(payload.source_scope)
    sql += ' ORDER BY score DESC, d.relative_path ASC, s.ordinal ASC, s.segment_id ASC LIMIT %s '
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
                'page_no': row['page_no'],
                'segment_kind': row['segment_kind'],
                'ordinal': row['ordinal'],
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
