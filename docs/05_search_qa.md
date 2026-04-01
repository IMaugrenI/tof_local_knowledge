# Search and QA

## MVP search
- Postgres full-text search
- structured filters
- segment hits instead of document hits only

## QA rules
- QA works only on the hit pool
- answer only with citations
- when evidence is weak: uncertainty must be explicit
- no free-form answer without source grounding

## Answer package
- answer_text
- confidence
- citations[]
- used_documents[]
- uncertainties[]
- query_id
- correlation_id

## Later optional
- pgvector
- local reranking
- Ollama for wording
