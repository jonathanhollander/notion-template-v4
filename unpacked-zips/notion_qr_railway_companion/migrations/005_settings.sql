-- app-level defaults
CREATE TABLE IF NOT EXISTS app_settings (
  key TEXT PRIMARY KEY,
  value JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO app_settings(key,value) VALUES
('companion_default', '{"enabled": true}')
ON CONFLICT (key) DO NOTHING;
