from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from _shared_db import db_conn, make_id
from _shared_extract import mime_type_for, safe_resolve_under, sha256_file

app = FastAPI(title='tof_local_knowledge_ingest_api', version='0.3.0')
SOURCE_ROOT = Path('/sources').resolve()


class ScanRequest(BaseModel):
    source_id: str = Field(min_length=1)
    root_path: str = Field(min_length=1)
    include_hidden: bool = False
    limit_files: int = Field(default=10000, ge=1, le=100000)


@app.get('/health')
def health():
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
            cur.fetchone()
    return {'status': 'ok', 'service': 'ingest_api'}


@app.post('/scan/run')
def run_scan(payload: ScanRequest):
    root = safe_resolve_under(SOURCE_ROOT, payload.root_path)
    if not root.exists() or not root.is_dir():
        return {'status': 'error', 'detail': 'invalid_root_path'}

    counters = {'new': 0, 'changed': 0, 'unchanged': 0, 'retry': 0, 'missing': 0}
    files_scanned = 0
    unreadable_count = 0
    truncated = False
    seen_paths: set[str] = set()
    sample_documents: list[dict] = []

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                '''
                INSERT INTO sources (source_id, display_name, mount_key, mount_path, enabled, scan_policy)
                VALUES (%s, %s, %s, %s, TRUE, %s)
                ON CONFLICT (source_id) DO UPDATE
                SET mount_path = EXCLUDED.mount_path,
                    scan_policy = EXCLUDED.scan_policy
                ''',
                (payload.source_id, payload.source_id, Path(payload.root_path).name, str(root), 'manual'),
            )

            for path in sorted(root.rglob('*')):
                # Never follow a symbolic link to files outside the mounted source.
                if path.is_symlink() or not path.is_file():
                    continue
                if not payload.include_hidden and any(part.startswith('.') for part in path.relative_to(root).parts):
                    continue
                if files_scanned >= payload.limit_files:
                    truncated = True
                    break
                files_scanned += 1

                rel_path = str(path.relative_to(root))
                seen_paths.add(rel_path)
                size_bytes = path.stat().st_size
                fingerprint = sha256_file(path)
                mime_type = mime_type_for(path)
                if mime_type == 'application/octet-stream':
                    unreadable_count += 1

                cur.execute(
                    '''
                    SELECT document_id, content_fingerprint, extraction_status
                    FROM documents WHERE source_id = %s AND relative_path = %s
                    ''',
                    (payload.source_id, rel_path),
                )
                row = cur.fetchone()
                document_id = row['document_id'] if row else make_id('doc')
                same_content = row is not None and row['content_fingerprint'] == fingerprint

                if not row:
                    change_status = 'new'
                elif not same_content:
                    change_status = 'changed'
                elif row['extraction_status'] == 'done':
                    change_status = 'unchanged'
                else:
                    change_status = 'retry'
                counters[change_status] += 1

                # Preserve a successful extraction on an unchanged file.
                # Pending/failed/missing documents stay eligible for a retry.
                if change_status not in {'unchanged'}:
                    cur.execute(
                        '''
                        INSERT INTO documents (
                          document_id, source_id, relative_path, file_name, mime_type, size_bytes,
                          content_fingerprint, read_status, extraction_status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_id, relative_path) DO UPDATE
                        SET file_name = EXCLUDED.file_name,
                            mime_type = EXCLUDED.mime_type,
                            size_bytes = EXCLUDED.size_bytes,
                            content_fingerprint = EXCLUDED.content_fingerprint,
                            read_status = EXCLUDED.read_status,
                            extraction_status = EXCLUDED.extraction_status
                        ''',
                        (
                            document_id, payload.source_id, rel_path, path.name, mime_type,
                            size_bytes, fingerprint, 'seen', 'pending',
                        ),
                    )

                if len(sample_documents) < 20:
                    sample_documents.append(
                        {
                            'document_id': document_id,
                            'relative_path': rel_path,
                            'mime_type': mime_type,
                            'size_bytes': size_bytes,
                            'scan_status': change_status,
                        }
                    )

            # Reconciliation is safe only after a complete scan. A scan stopped by
            # the configured limit must not mark unvisited documents as deleted.
            if not truncated:
                cur.execute(
                    'SELECT document_id, relative_path, extraction_status FROM documents WHERE source_id = %s',
                    (payload.source_id,),
                )
                for previous in cur.fetchall():
                    if previous['relative_path'] not in seen_paths and previous['extraction_status'] != 'missing':
                        cur.execute(
                            '''
                            UPDATE documents SET read_status = 'missing', extraction_status = 'missing'
                            WHERE document_id = %s
                            ''',
                            (previous['document_id'],),
                        )
                        counters['missing'] += 1

            manifest_id = make_id('manifest')
            cur.execute(
                '''
                INSERT INTO manifests (manifest_id, source_id, root_path, file_count, unreadable_count)
                VALUES (%s, %s, %s, %s, %s)
                ''',
                (manifest_id, payload.source_id, str(root), files_scanned, unreadable_count),
            )

    return {
        'status': 'ok',
        'manifest_id': manifest_id,
        'source_id': payload.source_id,
        'root_path': str(root),
        'files_scanned': files_scanned,
        'unreadable_count': unreadable_count,
        'scan_complete': not truncated,
        'counts': counters,
        'sample_documents': sample_documents,
    }
