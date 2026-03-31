CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  mount_key TEXT NOT NULL UNIQUE,
  mount_path TEXT,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  scan_policy TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
  document_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  relative_path TEXT NOT NULL,
  file_name TEXT NOT NULL,
  mime_type TEXT,
  size_bytes BIGINT,
  content_fingerprint TEXT,
  read_status TEXT NOT NULL,
  extraction_status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS extractions (
  extraction_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES documents(document_id),
  extractor_name TEXT NOT NULL,
  outcome TEXT NOT NULL,
  coverage DOUBLE PRECISION,
  warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
