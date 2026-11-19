-- The extraction agent's own database. It only reads inspections.db; links are matched by url.

-- Every dataset link the extraction agent has worked on, so it is never worked on twice.
CREATE TABLE IF NOT EXISTS extractions (
  url          TEXT PRIMARY KEY,               -- same url as in inspections.db
  doi          TEXT NOT NULL COLLATE NOCASE,   -- the paper the link comes from
  folder       TEXT NOT NULL,                  -- datasets/<folder> in the repository
  status       TEXT NOT NULL CHECK (status IN ('converted', 'not_converted', 'no_structures', 'failed')),
  extracted_at TEXT NOT NULL,                  -- YYYY-MM-DD
  note         TEXT,                           -- what the agent did, or why it stopped
  pr_url       TEXT                            -- the pull request with the notebook (none for no_structures)
);
