CREATE TABLE IF NOT EXISTS installs (
  wid UUID PRIMARY KEY,
  companion_enabled BOOLEAN,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO app_settings(key,value) VALUES('companion_default','{"enabled":true}') ON CONFLICT (key) DO NOTHING;
