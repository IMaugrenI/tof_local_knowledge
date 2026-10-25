"""Targeted source-index and evidence tests, without Docker or external files."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


class MemoryCursor:
    def __init__(self, db):
        self.db = db
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        norm = ' '.join(sql.lower().split())
        self.db.queries.append((norm, params))
        self.result = None
        if norm.startswith('select document_id, content_fingerprint, extraction_status'):
            self.result = self.db.documents.get((params[0], params[1]))
        elif norm.startswith('select document_id, relative_path, extraction_status'):
            self.result = [
                dict(item) for (source, _), item in self.db.documents.items() if source == params[0]
            ]
        elif norm.startswith('select document_id from documents where source_id'):
            self.result = self.db.documents.get((params[0], params[1]))
        elif norm.startswith('select relative_path from documents where document_id'):
            self.result = next(
                (item for (source, _), item in self.db.documents.items()
                 if source == params[1] and item['document_id'] == params[0]), None
            )
        elif norm.startswith('insert into documents'):
            if len(params) == 9:  # ingest
                document_id, source_id, relative, _, _, _, fingerprint, read, status = params
                self.db.documents[(source_id, relative)] = {
                    'document_id': document_id, 'relative_path': relative,
                    'content_fingerprint': fingerprint,
                    'read_status': read, 'extraction_status': status,
                }
            else:  # extractor
                document_id, source_id, relative, _, read, status = params
                existing = self.db.documents.get((source_id, relative), {})
                self.db.documents[(source_id, relative)] = {
                    **existing, 'document_id': document_id, 'relative_path': relative,
                    'read_status': read, 'extraction_status': status,
                }
        elif norm.startswith("update documents set read_status = 'missing'"):
            for item in self.db.documents.values():
                if item['document_id'] == params[0]:
                    item.update(read_status='missing', extraction_status='missing')
        elif norm.startswith('select d.document_id'):
            self.result = self.db.search_rows
        elif norm.startswith('select 1'):
            self.result = {'one': 1}

    def fetchone(self):
        return self.result

    def fetchall(self):
        return self.result or []


class MemoryDB:
    def __init__(self):
        self.documents = {}
        self.search_rows = []
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return MemoryCursor(self)


@pytest.fixture
def fake_services(monkeypatch):
    db = MemoryDB()
    db_module = types.ModuleType('_shared_db')
    db_module.db_conn = lambda: db
    counter = iter(range(1000))
    db_module.make_id = lambda prefix: f'{prefix}-{next(counter)}'
    monkeypatch.setitem(sys.modules, '_shared_db', db_module)

    extractor = types.ModuleType('_shared_extract')

    def safe_resolve_under(base, candidate):
        base_path = Path(base).resolve()
        target = Path(candidate).resolve()
        target.relative_to(base_path)
        return target

    extractor.safe_resolve_under = safe_resolve_under
    extractor.sha256_file = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    extractor.mime_type_for = lambda path: 'text/plain'
    extractor.extract_blocks = lambda path: ([], ['no_text'])
    monkeypatch.setitem(sys.modules, '_shared_extract', extractor)

    translator_module = types.ModuleType('translator')

    class DummyTranslator:
        def translate(self, **kwargs):
            return {
                'segment_count': 0, 'read_status': 'unreadable',
                'warnings': [], 'segments': [],
            }

    translator_module.ExtractionTranslator = DummyTranslator
    monkeypatch.setitem(sys.modules, 'translator', translator_module)

    def load(relative, name):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return db, load


def test_repeated_scan_preserves_success_and_tracks_changes(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ingest = load('services/ingest_api/app/runtime.py', 'k1_ingest')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    doc = source / 'demo.txt'
    doc.write_text('first', encoding='utf-8')
    monkeypatch.setattr(ingest, 'SOURCE_ROOT', root.resolve())
    request = ingest.ScanRequest(source_id='demo', root_path=str(source))

    first = ingest.run_scan(request)
    assert first['counts']['new'] == 1
    assert first['scan_complete'] is True
    db.documents[('demo', 'demo.txt')]['extraction_status'] = 'done'

    second = ingest.run_scan(request)
    assert second['counts']['unchanged'] == 1
    assert db.documents[('demo', 'demo.txt')]['extraction_status'] == 'done'

    doc.write_text('changed', encoding='utf-8')
    changed = ingest.run_scan(request)
    assert changed['counts']['changed'] == 1
    assert db.documents[('demo', 'demo.txt')]['extraction_status'] == 'pending'

    doc.unlink()
    missing = ingest.run_scan(request)
    assert missing['counts']['missing'] == 1
    assert db.documents[('demo', 'demo.txt')]['extraction_status'] == 'missing'


def test_hidden_exclusions_do_not_mark_indexed_file_missing(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ingest = load('services/ingest_api/app/runtime.py', 'k1_hidden')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    (source / '.hidden.txt').write_text('keep', encoding='utf-8')
    monkeypatch.setattr(ingest, 'SOURCE_ROOT', root.resolve())
    ingest.run_scan(ingest.ScanRequest(source_id='demo', root_path=str(source), include_hidden=True))
    db.documents[('demo', '.hidden.txt')]['extraction_status'] = 'done'

    result = ingest.run_scan(ingest.ScanRequest(source_id='demo', root_path=str(source)))
    assert result['counts']['missing'] == 0
    assert db.documents[('demo', '.hidden.txt')]['extraction_status'] == 'done'


def test_incomplete_scan_does_not_reconcile_missing_files(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ingest = load('services/ingest_api/app/runtime.py', 'k1_truncated')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    for name in ['a.txt', 'b.txt']:
        (source / name).write_text(name, encoding='utf-8')
    monkeypatch.setattr(ingest, 'SOURCE_ROOT', root.resolve())
    ingest.run_scan(ingest.ScanRequest(source_id='demo', root_path=str(source)))
    db.documents[('demo', 'b.txt')]['extraction_status'] = 'done'
    result = ingest.run_scan(ingest.ScanRequest(source_id='demo', root_path=str(source), limit_files=1))
    assert result['scan_complete'] is False
    assert result['counts']['missing'] == 0
    assert db.documents[('demo', 'b.txt')]['extraction_status'] == 'done'


def test_search_filters_disabled_and_outdated_documents(fake_services):
    db, load = fake_services
    search = load('services/search_api/app/runtime.py', 'k1_search')
    result = search.search(search.SearchRequest(query='demo'))
    assert result['hits'] == []
    sql = next(sql for sql, _ in db.queries if sql.startswith('select d.document_id'))
    assert "d.extraction_status = 'done'" in sql
    assert 'source.enabled is true' in sql


def test_failed_extraction_keeps_previous_segments_and_records_json(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ext = load('services/extractor_api/app/runtime.py', 'k1_extractor')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    (source / 'demo.txt').write_text('demo', encoding='utf-8')
    monkeypatch.setattr(ext, 'SOURCE_ROOT', root.resolve())
    db.documents[('demo', 'demo.txt')] = {
        'document_id': 'doc-1', 'relative_path': 'demo.txt',
        'read_status': 'fully_read', 'extraction_status': 'done',
    }
    response = ext.extract_file(ext.ExtractRequest(
        source_id='demo', root_path=str(source), relative_path='demo.txt',
    ))
    assert response['segment_count'] == 0
    assert db.documents[('demo', 'demo.txt')]['extraction_status'] == 'failed'
    assert not any(q.startswith('delete from document_segments') for q, _ in db.queries)
    record = next(params for sql, params in db.queries if sql.startswith('insert into extractions'))
    assert record[-1] == '["no_text"]'


def test_extraction_rejects_document_id_for_different_source(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ext = load('services/extractor_api/app/runtime.py', 'k1_mismatch')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    (source / 'demo.txt').write_text('demo', encoding='utf-8')
    monkeypatch.setattr(ext, 'SOURCE_ROOT', root.resolve())
    db.documents[('demo', 'demo.txt')] = {
        'document_id': 'doc-1', 'relative_path': 'demo.txt',
        'read_status': 'fully_read', 'extraction_status': 'done',
    }
    response = ext.extract_file(ext.ExtractRequest(
        source_id='demo', root_path=str(source), relative_path='demo.txt',
        document_id='doc-unrelated',
    ))
    assert response['detail'] == 'document_source_mismatch'
    assert not any(sql.startswith('insert into extractions') for sql, _ in db.queries)


def test_cursor_scan_reaches_files_beyond_limit_without_false_missing(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ingest = load('services/ingest_api/app/runtime.py', 'k5_ingest')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    for index in range(205):
        (source / f'file-{index:03d}.txt').write_text(str(index), encoding='utf-8')
    monkeypatch.setattr(ingest, 'SOURCE_ROOT', root.resolve())
    all_pages = []
    cursor = None
    for _ in range(4):
        result = ingest.run_scan(ingest.ScanRequest(
            source_id='demo', root_path=str(source), limit_files=100,
            start_after=cursor,
        ))
        all_pages.append(result)
        cursor = result['next_cursor']
        if cursor is None:
            break
    assert [p['files_scanned'] for p in all_pages] == [100, 100, 5]
    assert all_pages[0]['scan_complete'] is False
    assert all_pages[-1]['scan_complete'] is True
    assert all_pages[-1]['reconciliation_performed'] is False
    assert all(p['counts']['missing'] == 0 for p in all_pages)
    assert len(db.documents) == 205
    assert ('demo', 'file-204.txt') in db.documents


def test_completed_small_scan_still_reconciles_missing(fake_services, tmp_path, monkeypatch):
    db, load = fake_services
    ingest = load('services/ingest_api/app/runtime.py', 'k5_small')
    root = tmp_path / 'sources'
    source = root / 'source_1'
    source.mkdir(parents=True)
    doc = source / 'only.md'
    doc.write_text('text', encoding='utf-8')
    monkeypatch.setattr(ingest, 'SOURCE_ROOT', root.resolve())
    first = ingest.run_scan(ingest.ScanRequest(
        source_id='demo', root_path=str(source), limit_files=100,
    ))
    assert first['reconciliation_performed'] is True
    doc.unlink()
    second = ingest.run_scan(ingest.ScanRequest(
        source_id='demo', root_path=str(source), limit_files=100,
    ))
    assert second['counts']['missing'] == 1
