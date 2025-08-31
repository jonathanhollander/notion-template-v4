CREATE TABLE IF NOT EXISTS metrics_snapshots (
  id                       BIGSERIAL PRIMARY KEY,
  wid                      UUID NOT NULL REFERENCES installs(wid) ON DELETE CASCADE,
  ts                       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  section_key              TEXT NOT NULL,
  notion_db_id             TEXT NOT NULL,
  total_rows               INT NOT NULL,
  completed_rows           INT NOT NULL,
  percent_complete         NUMERIC(5,2) NOT NULL,
  last_item_created_at     TIMESTAMPTZ,
  last_item_edited_at      TIMESTAMPTZ,
  overdue_rows             INT,
  has_files_count          INT,
  has_relation_count       INT
);

CREATE INDEX IF NOT EXISTS idx_metrics_latest ON metrics_snapshots (wid, section_key, ts DESC);
