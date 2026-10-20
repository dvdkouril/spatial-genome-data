-- Every paper the agent has judged, relevant or not, so it is never judged twice.
CREATE TABLE IF NOT EXISTS papers (
  doi           TEXT PRIMARY KEY COLLATE NOCASE, -- DOI, or the PMC / Europe PMC id when there is none
  title         TEXT NOT NULL,
  year          TEXT,
  journal       TEXT,
  query         TEXT,          -- the search that found it
  verdict       TEXT NOT NULL CHECK (verdict IN ('relevant', 'maybe', 'irrelevant')),
  reason        TEXT,          -- one sentence
  dataset_links TEXT,          -- URLs separated by spaces
  found_at      TEXT           -- YYYY-MM-DD
);
