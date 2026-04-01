# First Run

## 1. Copy `.env.example` to `.env`
The most important values are:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `LOCAL_SOURCE_ROOT_1`

## 2. Prepare directories
```bash
bash scripts/bootstrap_dev.sh
```

## 3. Start the runtime stack
```bash
bash scripts/start_full.sh
```

## 4. Check health
```bash
bash scripts/check_full.sh
```

## 5. Run a source scan
Example:
```bash
curl -X POST http://127.0.0.1:8103/scan/run \
  -H 'content-type: application/json' \
  -d '{"source_id":"source_local_1","root_path":"/sources/source_1"}'
```

## 6. Extract a single file
```bash
curl -X POST http://127.0.0.1:8104/extract/file \
  -H 'content-type: application/json' \
  -d '{"source_id":"source_local_1","root_path":"/sources/source_1","relative_path":"example.pdf","persist":true}'
```

## 7. Test search
```bash
curl -X POST http://127.0.0.1:8105/search \
  -H 'content-type: application/json' \
  -d '{"query":"notice period","source_scope":["source_local_1"],"limit":5}'
```

## 8. Test QA
```bash
curl -X POST http://127.0.0.1:8106/answer \
  -H 'content-type: application/json' \
  -d '{"question":"Which notice period applies?","source_scope":["source_local_1"],"limit":5}'
```
