CREATE TABLE IF NOT EXISTS manifests (
  manifest_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  root_path TEXT NOT NULL,
  file_count INTEGER NOT NULL,
  unreadable_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app_users (
  user_id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  display_name TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_source_grants (
  grant_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES app_users(user_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  role_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_source_relpath
  ON documents(source_id, relative_path);
