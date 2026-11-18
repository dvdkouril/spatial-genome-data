#!/usr/bin/env bash
# One pass of the extraction agent: look at dataset links a paper produced that
# are not in the extractions database yet, picked at random, one fresh Pi
# conversation per link.
#   extract.sh [max links]
# Reads $DATASETS_DB (never writes it), writes $EXTRACTIONS_DB. Each link gets
# its own work folder link-<id> in the current directory; it is deleted after
# the link (downloads can be large) unless KEEP_LINK_DIRS=1. The agent's report
# for every link is printed, so it can be read in the logs.
set -uo pipefail

datasets=${DATASETS_DB:?set DATASETS_DB to the datasets database}
db=${EXTRACTIONS_DB:?set EXTRACTIONS_DB to the extractions database}
max=${1:-1000000}
per_link=${LINK_TIMEOUT:-20m}
here=$(cd "$(dirname "$0")/.." && pwd)
work=$(pwd)

sqlite3 "$db" <"$here/extraction-schema.sql"

# Work from a snapshot, so the dataset agent can keep writing datasets.db.
snapshot=$work/datasets-snapshot.db
rm -f "$snapshot"
sqlite3 "$datasets" ".backup '${snapshot//\'/\'\'}'"

# One line per link: id, doi and url, separated by tabs.
queue=()
while IFS= read -r line; do queue+=("$line"); done < <(sqlite3 -separator $'\t' "$db" "
  ATTACH '${snapshot//\'/\'\'}' AS d;
  SELECT rowid, doi, url FROM d.datasets
  WHERE role = 'produced'
    AND url NOT IN (SELECT url FROM extractions)
  ORDER BY random()
  LIMIT $max")
echo "${#queue[@]} links to look at."

# Time limit per link; coreutils timeout is gtimeout on macOS.
limit=()
if command -v timeout >/dev/null; then limit=(timeout "$per_link")
elif command -v gtimeout >/dev/null; then limit=(gtimeout "$per_link")
else echo "No timeout command found; links run without a time limit."
fi

n=0
for line in "${queue[@]}"; do
  n=$((n + 1))
  IFS=$'\t' read -r id doi url <<<"$line"
  dir=$work/link-$id
  rm -rf "$dir" && mkdir -p "$dir" && cd "$dir" || exit 1

  echo
  echo "=== [$n/${#queue[@]}] $url (paper $doi) ==="
  LINK_URL=$url PAPER_DOI=$doi ${limit[@]+"${limit[@]}"} \
    pi -p --no-session --model einfra/kimi-k3 \
      --append-system-prompt "$here/extraction-instructions.md" \
      "Look at the dataset $url from the paper $doi." >answer.txt 2>&1 </dev/null
  code=$?
  cat answer.txt

  q=${url//\'/\'\'}
  status=$(sqlite3 "$db" "SELECT status FROM extractions WHERE url = '$q'")
  if [[ -z $status ]]; then
    status=failed
    reason="agent did not save a result (exit code $code)"
    [[ $code == 124 ]] && reason="timed out after $per_link"
    sqlite3 "$db" "INSERT OR IGNORE INTO extractions (url, doi, status, extracted_at, note)
                   VALUES ('$q', '${doi//\'/\'\'}', 'failed', date('now'), '$reason')"
  fi
  echo "=== [$n/${#queue[@]}] $url: $status ==="
  cd "$work"
  [[ ${KEEP_LINK_DIRS:-} == 1 ]] || rm -rf "$dir"
done
rm -f "$snapshot"

echo
echo "Extractions so far:"
sqlite3 "$db" "SELECT '  ' || status || ': ' || count(*) FROM extractions GROUP BY status"
