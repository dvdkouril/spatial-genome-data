#!/usr/bin/env bash
# Write the whole database as a CSV backup (sorted, so diffs show only new papers).
#   export.sh [output.csv]   (default: agent/data/papers.csv)
# The database is $PAPERS_DB.
set -euo pipefail

db=${PAPERS_DB:?set PAPERS_DB to the papers database}
out=${1:-$(dirname "$0")/../data/papers.csv}

sqlite3 -header -csv "$db" "SELECT * FROM papers ORDER BY doi" >"$out"
echo "Exported $(sqlite3 "$db" "SELECT count(*) FROM papers") papers to $out"
