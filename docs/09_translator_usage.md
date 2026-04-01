# Übersetzer-Nutzung

## Zweck
Der Übersetzer wandelt rohe Extraktionsblöcke in kanonische, zitierbare Segmente um.

## Endpoint
`POST /translate/extraction`

## Beispielrequest
```json
{
  "document_id": "doc_contract_001",
  "raw_blocks": [
    {"kind": "paragraph", "page_no": 1, "text": "Die Kündigungsfrist beträgt 3 Monate."},
    {"kind": "paragraph", "page_no": 2, "text": "Nebenabreden bedürfen der Schriftform."}
  ]
}
```

## Beispielantwort
```json
{
  "document_id": "doc_contract_001",
  "segment_count": 2,
  "read_status": "fully_read",
  "warnings": [],
  "segments": [
    {
      "segment_id": "...",
      "segment_kind": "paragraph",
      "ordinal": 1,
      "page_no": 1,
      "citation_label": "doc_contract_001#seg-1",
      "text": "Die Kündigungsfrist beträgt 3 Monate."
    }
  ]
}
```
