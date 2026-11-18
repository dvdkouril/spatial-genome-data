-- The extraction agent's own database. It only reads datasets.db; links are matched by url.

-- Every dataset link the extraction agent has looked at, so it is never looked at twice.
CREATE TABLE IF NOT EXISTS extractions (
  url          TEXT PRIMARY KEY,               -- same url as in datasets.db
  doi          TEXT NOT NULL COLLATE NOCASE,   -- the paper the link comes from
  status       TEXT NOT NULL CHECK (status IN ('has_structures', 'no_structures', 'too_large', 'unclear', 'failed')),
  extracted_at TEXT NOT NULL,                  -- YYYY-MM-DD
  note         TEXT                            -- what the agent found, or why it stopped
);
