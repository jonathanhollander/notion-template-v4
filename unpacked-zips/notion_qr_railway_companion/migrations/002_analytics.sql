-- installs / sessions / events
CREATE TABLE IF NOT EXISTS installs (
  wid                UUID PRIMARY KEY,
  notion_workspace_id TEXT,
  notion_workspace_name TEXT,
  product_id         TEXT,
  audience_default   TEXT,
  country_code       TEXT,
  region             TEXT,
  city               TEXT,
  language_pref      TEXT,
  timezone           TEXT,
  device_type        TEXT,
  browser            TEXT,
  os                 TEXT,
  screen_w           INT,
  screen_h           INT,
  dpr                NUMERIC(3,2),
  a11y_reduced_motion BOOLEAN,
  a11y_contrast        TEXT,
  net_downlink       NUMERIC(4,1),
  net_effective_type TEXT,
  net_save_data      BOOLEAN,
  companion_enabled  BOOLEAN,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at       TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS sessions (
  id                 UUID PRIMARY KEY,
  wid                UUID REFERENCES installs(wid) ON DELETE CASCADE,
  referer_url        TEXT,
  section_hint       TEXT,
  load_ts            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  first_interaction_ts TIMESTAMPTZ,
  hidden_ts          TIMESTAMPTZ,
  unload_ts          TIMESTAMPTZ,
  render_ms          INT,
  error_name         TEXT,
  error_msg          TEXT,
  error_stack_hash   TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id                 BIGSERIAL PRIMARY KEY,
  ts                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  session_id         UUID REFERENCES sessions(id) ON DELETE CASCADE,
  wid                UUID NOT NULL,
  type               TEXT,
  name               TEXT,
  value              NUMERIC,
  extra              JSONB
);
CREATE INDEX IF NOT EXISTS idx_events_wid_ts ON events (wid, ts DESC);
