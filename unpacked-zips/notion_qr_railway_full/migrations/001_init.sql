CREATE TABLE IF NOT EXISTS products (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  price_id   TEXT NOT NULL,
  qr_set     TEXT NOT NULL,
  enabled    BOOLEAN NOT NULL DEFAULT TRUE,
  start_at   TIMESTAMPTZ,
  end_at     TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS visits (
  id           BIGSERIAL PRIMARY KEY,
  ts           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  page         TEXT NOT NULL,
  promo_id     TEXT,
  product_id   TEXT,
  ip_hash      TEXT,
  ua_hash      TEXT,
  referer_host TEXT,
  extra        JSONB
);

INSERT INTO products (id,name,price_id,qr_set,enabled)
VALUES ('top10','Top‑10 Essentials','price_live_TOP10','top10',true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO products (id,name,price_id,qr_set,enabled)
VALUES ('complete','Complete Pack','price_live_COMPLETE','complete',true)
ON CONFLICT (id) DO NOTHING;
