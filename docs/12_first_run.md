# First Run

## 1. `.env.example` nach `.env` kopieren
Wichtig ist vor allem:
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `LOCAL_SOURCE_ROOT_1`

## 2. Verzeichnisse vorbereiten
```bash
bash scripts/bootstrap_dev.sh
```

## 3. Runtime-Stack starten
```bash
bash scripts/start_full.sh
```

## 4. Health prüfen
```bash
bash scripts/check_full.sh
```

## 5. Quelle scannen
Beispiel:
```bash
curl -X POST http://127.0.0.1:8103/scan/run \
  -H 'content-type: application/json' \
  -d '{"source_id":"source_local_1","root_path":"/sources/source_1"}'
```

## 6. Einzelne Datei extrahieren
```bash
curl -X POST http://127.0.0.1:8104/extract/file \
  -H 'content-type: application/json' \
  -d '{"source_id":"source_local_1","root_path":"/sources/source_1","relative_path":"example.pdf","persist":true}'
```

## 7. Suche testen
```bash
curl -X POST http://127.0.0.1:8105/search \
  -H 'content-type: application/json' \
  -d '{"query":"Kündigungsfrist","source_scope":["source_local_1"],"limit":5}'
```

## 8. QA testen
```bash
curl -X POST http://127.0.0.1:8106/answer \
  -H 'content-type: application/json' \
  -d '{"question":"Welche Kündigungsfrist gilt?","source_scope":["source_local_1"],"limit":5}'
```
