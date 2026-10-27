#!/usr/bin/env bash
# Save the data links found in the paper being explored.
#   save-exploration.sh result.json
# result.json is an object:
#   {"note": "...", "datasets": [{"url", "role", "reason", "evidence"}, ...]}
# The paper is $PAPER_DOI, the database is $DATASETS_DB.
set -euo pipefail

result=${1:?usage: save-exploration.sh result.json}
db=${DATASETS_DB:?set DATASETS_DB to the datasets database}
doi=${PAPER_DOI:?set PAPER_DOI to the paper being explored}

# Check the result first, so a mistake is reported instead of silently dropped.
problems=$(jq -r '
  if (.datasets | type) != "array" then "the file must contain an object with a \"datasets\" array" else
    .datasets[] | select((.url // "") == "" or (.evidence // "") == ""
                         or (.role | IN("produced", "used", "code") | not))
                | "invalid entry (needs url, evidence, and role produced|used|code): \(tojson)"
  end' "$result")
if [[ -n $problems ]]; then
  echo "$problems" >&2
  echo "Nothing saved. Fix the entries and run save-exploration.sh again." >&2
  exit 1
fi

sqlite3 "$db" <"$(dirname "$0")/../datasets-schema.sql"
q=${doi//\'/\'\'}         # quote for SQL
file=${result//\'/\'\'}
if [[ $(sqlite3 "$db" "SELECT count(*) FROM explorations WHERE doi = '$q'") != 0 ]]; then
  echo "$doi is already saved; nothing changed."
  exit 0
fi

# The paper is data_found if it has at least one link to data it produced itself.
sqlite3 -bail "$db" "
  BEGIN;
  INSERT INTO datasets (doi, url, role, reason, evidence)
  SELECT '$q', value->>'url', value->>'role', value->>'reason', value->>'evidence'
  FROM json_each(readfile('$file'), '\$.datasets');
  INSERT INTO explorations (doi, status, explored_at, note)
  SELECT '$q',
         CASE WHEN EXISTS (SELECT 1 FROM datasets WHERE doi = '$q' AND role = 'produced')
              THEN 'data_found' ELSE 'no_data' END,
         date('now'), readfile('$file')->>'note';
  COMMIT;"

links=$(sqlite3 "$db" "SELECT count(*) FROM datasets WHERE doi = '$q'")
echo "Saved $doi with $links links."
