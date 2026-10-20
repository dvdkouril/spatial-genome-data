#!/usr/bin/env bash
# Save judged papers from a JSON file into the database; papers already there are skipped.
#   save.sh batch.json
# batch.json is an array of objects with the fields:
#   doi, title, year, journal, query, verdict, reason, dataset_links
# found_at is set to today's date. The database is $PAPERS_DB.
set -euo pipefail

batch=${1:?usage: save.sh batch.json}
db=${PAPERS_DB:?set PAPERS_DB to the papers database}

# Check the batch first, so a mistake is reported instead of silently dropped.
problems=$(jq -r '
  if type != "array" then "the file must contain a JSON array" else
    .[] | select((.doi // "") == "" or (.title // "") == ""
                 or (.verdict | IN("relevant", "maybe", "irrelevant") | not))
        | "invalid entry (needs doi, title, and verdict relevant|maybe|irrelevant): \(tojson)"
  end' "$batch")
if [[ -n $problems ]]; then
  echo "$problems" >&2
  echo "Nothing saved. Fix the entries and run save.sh again." >&2
  exit 1
fi

sqlite3 "$db" <"$(dirname "$0")/../schema.sql"
before=$(sqlite3 "$db" "SELECT count(*) FROM papers")
file=${batch//\'/\'\'} # quote for SQL
sqlite3 "$db" "
  INSERT OR IGNORE INTO papers (doi, title, year, journal, query, verdict, reason, dataset_links, found_at)
  SELECT value->>'doi', value->>'title', value->>'year', value->>'journal', value->>'query',
         value->>'verdict', value->>'reason', coalesce(value->>'dataset_links', ''), date('now')
  FROM json_each(readfile('$file'));"
after=$(sqlite3 "$db" "SELECT count(*) FROM papers")

total=$(jq length "$batch")
echo "Saved $((after - before)) of $total papers ($((total - after + before)) were already in the database). Database now has $after papers."
