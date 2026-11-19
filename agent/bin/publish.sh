#!/usr/bin/env bash
# Export database tables as CSV and upload them to the R2 bucket, one file per
# table (<table>.csv), replacing the previous upload.
#   publish.sh <database>[:<table>,<table>...] ...
# A database alone publishes all its tables; with a list, only those. E.g.
#   publish.sh $PAPERS_DB                       -> papers.csv
#   publish.sh $DATASETS_DB:datasets $INSPECTIONS_DB
# Bucket: $R2_ENDPOINT (https://<account id>.r2.cloudflarestorage.com) and
# $R2_BUCKET. The aws command reads the API token from $AWS_ACCESS_KEY_ID,
# $AWS_SECRET_ACCESS_KEY, and needs AWS_DEFAULT_REGION=auto for R2.
set -euo pipefail

endpoint=${R2_ENDPOINT:?set R2_ENDPOINT to https://<account id>.r2.cloudflarestorage.com}
bucket=${R2_BUCKET:?set R2_BUCKET to the bucket name}
[[ $# -gt 0 ]] || { echo "usage: publish.sh <database>[:<table>,<table>...] ..." >&2; exit 1; }

out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

for target in "$@"; do
  db=${target%%:*}
  [[ $target == *:* ]] && tables=${target#*:} || tables=""
  if [[ ! -f $db ]]; then
    echo "No database $db, skipped." >&2
    continue
  fi
  if [[ -z $tables ]]; then
    tables=$(sqlite3 "$db" "SELECT group_concat(name) FROM sqlite_master
                            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
  fi
  IFS=, read -ra list <<<"$tables"
  for table in "${list[@]}"; do
    # The header comes from the schema, so an empty table still has one.
    # Rows are sorted by the first columns, so two versions are easy to compare.
    sqlite3 "$db" "SELECT group_concat(name, ',') FROM pragma_table_info('$table')" >"$out/$table.csv"
    sqlite3 -csv "$db" "SELECT * FROM \"$table\" ORDER BY 1, 2" >>"$out/$table.csv"
    rows=$(sqlite3 "$db" "SELECT count(*) FROM \"$table\"")
    aws s3 cp "$out/$table.csv" "s3://$bucket/$table.csv" \
      --endpoint-url "$endpoint" --content-type "text/csv; charset=utf-8" --only-show-errors
    echo "Uploaded $table.csv ($rows rows) to $bucket."
  done
done
