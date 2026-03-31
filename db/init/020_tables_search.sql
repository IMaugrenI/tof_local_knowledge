CREATE TABLE IF NOT EXISTS document_segments (
  segment_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(document_id),
  segment_kind TEXT NOT NULL,
  page_no INTEGER,
  ordinal INTEGER NOT NULL,
  citation_label TEXT NOT NULL,
  text_content TEXT NOT NULL,
  embedding VECTOR(768),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_segments_document_id ON document_segments(document_id);
CREATE INDEX IF NOT EXISTS idx_document_segments_text_fts ON document_segments USING GIN (to_tsvector('simple', text_content));
