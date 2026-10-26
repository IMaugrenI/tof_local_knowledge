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

## K-08: Conservative evidence boundary (P1 correction)

A broad OR keyword retrieval matches any single term and is **not sufficient evidence to answer a question**. When only broad OR matches are found, QA returns the existing no-evidence response shape with `confidence = 0`, empty `citations`, `used_documents` and `evidence_refs`, and `evidence_signal.status = no_evidence`. `search_queries` and the optional `evidence_signal.unverified_candidates` count are diagnostics only; they are not evidence. The `uncertainties` field records `no_evidence` and `broad_keyword_search`.

Direct and stricter keyword hits retain their normal citation paths. **Limit:** keyword retrieval and excerpts alone cannot prove semantic entailment for every possible question. Positive results remain cited excerpts with explicit uncertainty, not independently verified factual assertions. No new model, cloud service or stack is added.

## K-09: Targeted demo retrieval fixes

The existing PostgreSQL full-text search now includes a tokenized **relative filename** together with the extracted segment text, so `resolved incident` can retrieve rows containing `resolved` from `incident_log_sample.csv`. Source-scope, extracted-only filtering and stable ranking remain enforced.

When strict QA keyword retrieval finds nothing, a **narrow lexical variant** (`publish` → `public`) is tried with all other content terms still mandatory (AND). Returned evidence signals use `search_strategy = keywords_variant` and include `lexical_variant_not_semantically_verified` in uncertainties. Broad OR results are still **diagnostic only** and must never be turned into answer citations. This is a scoped fix for the reproduced demo cases, not an independent semantic answer verification layer.
