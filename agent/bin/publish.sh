#!/usr/bin/env bash
# Export both databases as CSV and upload them to the R2 bucket, replacing the
# previous upload: papers.csv, datasets.csv, explorations.csv.
#   publish.sh
# Databases: $PAPERS_DB, $DATASETS_DB. Bucket: $R2_ENDPOINT
# (https://<account id>.r2.cloudflarestorage.com) and $R2_BUCKET. The aws
# command reads the API token from $AWS_ACCESS_KEY_ID, $AWS_SECRET_ACCESS_KEY,
# and needs AWS_DEFAULT_REGION=auto for R2.
set -euo pipefail

papers=${PAPERS_DB:?set PAPERS_DB to the papers database}
datasets=${DATASETS_DB:?set DATASETS_DB to the datasets database}
endpoint=${R2_ENDPOINT:?set R2_ENDPOINT to https://<account id>.r2.cloudflarestorage.com}
bucket=${R2_BUCKET:?set R2_BUCKET to the bucket name}

out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

# Sorted, like export.sh, so two versions are easy to compare.
sqlite3 -header -csv "$papers" "SELECT * FROM papers ORDER BY doi" >"$out/papers.csv"
# The tables are created empty if the dataset agent has not run yet.
sqlite3 "$datasets" <"$(dirname "$0")/../datasets-schema.sql"
sqlite3 -header -csv "$datasets" "SELECT * FROM datasets ORDER BY doi, url" >"$out/datasets.csv"
sqlite3 -header -csv "$datasets" "SELECT * FROM explorations ORDER BY doi" >"$out/explorations.csv"

for name in papers datasets explorations; do
  aws s3 cp "$out/$name.csv" "s3://$bucket/$name.csv" \
    --endpoint-url "$endpoint" --content-type "text/csv; charset=utf-8" --only-show-errors
  echo "Uploaded $name.csv to $bucket."
done
