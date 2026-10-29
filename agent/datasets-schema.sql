-- The dataset agent's own database. It only reads papers.db; papers are linked by doi.

-- Every paper the dataset agent has looked at, so it is never looked at twice.
CREATE TABLE IF NOT EXISTS explorations (
  doi         TEXT PRIMARY KEY COLLATE NOCASE, -- same id as in papers.db
  status      TEXT NOT NULL CHECK (status IN ('data_found', 'no_data', 'no_fulltext', 'failed')),
  explored_at TEXT NOT NULL,                   -- YYYY-MM-DD
  note        TEXT                             -- one sentence, e.g. "data available on request"
);

-- Candidate data links found in a paper, zero or more per exploration.
CREATE TABLE IF NOT EXISTS datasets (
  doi      TEXT NOT NULL COLLATE NOCASE REFERENCES explorations (doi),
  url      TEXT NOT NULL,                      -- full URL; bare accessions and DOIs written as URLs
  role     TEXT NOT NULL CHECK (role IN ('produced', 'used', 'code')),
  reason   TEXT,                               -- one sentence: why this role
  evidence TEXT NOT NULL,                      -- the sentence of the paper the link comes from, verbatim
  PRIMARY KEY (doi, url)
);
