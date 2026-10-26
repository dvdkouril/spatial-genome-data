#!/usr/bin/env bash
# Write the datasets database as CSV backups (sorted, so diffs show only new rows).
#   export-datasets.sh [output folder]   (default: agent/data)
# The database is $DATASETS_DB.
set -euo pipefail

db=${DATASETS_DB:?set DATASETS_DB to the datasets database}
out=${1:-$(dirname "$0")/../data}

sqlite3 -header -csv "$db" "SELECT * FROM explorations ORDER BY doi" >"$out/explorations.csv"
sqlite3 -header -csv "$db" "SELECT * FROM datasets ORDER BY doi, url" >"$out/datasets.csv"
echo "Exported $(sqlite3 "$db" "SELECT count(*) FROM explorations") explorations and" \
  "$(sqlite3 "$db" "SELECT count(*) FROM datasets") data links to $out"
