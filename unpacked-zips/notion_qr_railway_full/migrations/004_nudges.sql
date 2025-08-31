CREATE TABLE IF NOT EXISTS nudges (
  id SERIAL PRIMARY KEY,
  audience TEXT NOT NULL CHECK (audience IN ('family','executor')),
  text TEXT NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO nudges (audience, text, enabled) VALUES
('family','Would you like to add a photo that warms your heart—just one is enough?', true),
('family','Is there a small memory you want to capture today—even a line matters?', true),
('family','Would you like to write a gentle note to someone—only a sentence is fine?', true),
('executor','Next step: upload the insurance policy—this prevents delays.', true),
('executor','Quick win: add one subscription to cancel—reduces costs immediately.', true),
('executor','Review the First 72 Hours checklist—one item today keeps momentum.', true)
ON CONFLICT DO NOTHING;
