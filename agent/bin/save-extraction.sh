#!/usr/bin/env bash
# Save the outcome for the dataset link being converted.
#   save-extraction.sh <status> "<note>"
# status: converted, not_converted or no_structures.
# The link is $LINK_URL from the paper $PAPER_DOI, its folder $DATASET_FOLDER,
# the database is $EXTRACTIONS_DB.
set -euo pipefail

status=${1:?usage: save-extraction.sh <status> "<note>"}
note=${2:?usage: save-extraction.sh <status> "<note>"}
db=${EXTRACTIONS_DB:?set EXTRACTIONS_DB to the extractions database}
url=${LINK_URL:?set LINK_URL to the link being converted}
doi=${PAPER_DOI:?set PAPER_DOI to the paper of the link}
folder=${DATASET_FOLDER:?set DATASET_FOLDER to the dataset folder name}

case $status in
  converted | not_converted | no_structures) ;;
  *)
    echo "status must be converted, not_converted or no_structures. Nothing saved." >&2
    exit 1
    ;;
esac

sqlite3 "$db" <"$(dirname "$0")/../extraction-schema.sql"
u=${url//\'/\'\'} d=${doi//\'/\'\'} f=${folder//\'/\'\'} n=${note//\'/\'\'} # quote for SQL
sqlite3 "$db" "INSERT OR IGNORE INTO extractions (url, doi, folder, status, extracted_at, note)
               VALUES ('$u', '$d', '$f', '$status', date('now'), '$n')"
echo "Saved $url as $status."
