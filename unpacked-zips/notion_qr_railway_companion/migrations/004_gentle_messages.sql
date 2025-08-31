-- empathetic message bank
CREATE TABLE IF NOT EXISTS gentle_messages (
  id SERIAL PRIMARY KEY,
  audience TEXT NOT NULL CHECK (audience IN ('family','executor')),
  text TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  include_in_rotation BOOLEAN NOT NULL DEFAULT TRUE
);
INSERT INTO gentle_messages (audience, text, enabled, include_in_rotation) VALUES
('family','A tiny step is enough—would adding one loving note feel okay today?', true, true),
('family','Is there a photo that quietly brings comfort—would you like to place it here?', true, true),
('family','Would a single-kind sentence to someone help today? Only a few words are needed.', true, true),
('executor','One simple action: open the Subscriptions list—checking one item helps.', true, true),
('executor','A small win: add the insurer’s contact—this prevents delays later.', true, true),
('executor','Glance at the First 72 Hours card—one check today keeps momentum.', true, true)
ON CONFLICT DO NOTHING;
