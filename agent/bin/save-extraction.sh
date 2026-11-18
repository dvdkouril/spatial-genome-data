#!/usr/bin/env bash
# Save the outcome for the dataset link being looked at.
#   save-extraction.sh <status> "<note>"
# status: has_structures, no_structures, too_large or unclear.
# The link is $LINK_URL from the paper $PAPER_DOI, the database is $EXTRACTIONS_DB.
set -euo pipefail

status=${1:?usage: save-extraction.sh <status> "<note>"}
note=${2:?usage: save-extraction.sh <status> "<note>"}
db=${EXTRACTIONS_DB:?set EXTRACTIONS_DB to the extractions database}
url=${LINK_URL:?set LINK_URL to the link being looked at}
doi=${PAPER_DOI:?set PAPER_DOI to the paper of the link}

case $status in
  has_structures | no_structures | too_large | unclear) ;;
  *)
    echo "status must be has_structures, no_structures, too_large or unclear. Nothing saved." >&2
    exit 1
    ;;
esac

sqlite3 "$db" <"$(dirname "$0")/../extraction-schema.sql"
u=${url//\'/\'\'} d=${doi//\'/\'\'} n=${note//\'/\'\'} # quote for SQL
sqlite3 "$db" "INSERT OR IGNORE INTO extractions (url, doi, status, extracted_at, note)
               VALUES ('$u', '$d', '$status', date('now'), '$n')"
echo "Saved $url as $status."
