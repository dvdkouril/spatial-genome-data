#!/usr/bin/env bash
# One pass of the inspection agent: look at dataset links a paper produced that
# are not in the inspections database yet, picked at random, one fresh Pi
# conversation per link.
#   inspect.sh [max links]
# Reads $DATASETS_DB (never writes it), writes $INSPECTIONS_DB. Each link gets
# its own work folder link-<id> in the current directory; it is deleted after
# the link (downloads can be large) unless KEEP_LINK_DIRS=1. Everything the
# agent does is printed as it happens, so it can be followed in the logs.
set -uo pipefail

datasets=${DATASETS_DB:?set DATASETS_DB to the datasets database}
db=${INSPECTIONS_DB:?set INSPECTIONS_DB to the inspections database}
# Absolute, because each link runs in its own folder (also for save-inspection.sh).
db=$(cd "$(dirname "$db")" && pwd)/$(basename "$db")
export INSPECTIONS_DB=$db
max=${1:-1000000}
per_link=${LINK_TIMEOUT:-20m}
here=$(cd "$(dirname "$0")/.." && pwd)
work=$(pwd)

sqlite3 "$db" <"$here/inspection-schema.sql"

# Work from a snapshot, so the dataset agent can keep writing datasets.db.
snapshot=$work/datasets-snapshot.db
rm -f "$snapshot"
sqlite3 "$datasets" ".backup '${snapshot//\'/\'\'}'"

# Links to documents, videos and images are skipped: they cannot hold 3D coordinates.
skip=(pdf doc docx  mp4 mov mpg avi  tif tiff eps png jpg jpeg gif)
not_skipped=""
for ext in "${skip[@]}"; do not_skipped+=" AND lower(url) NOT LIKE '%.$ext'"; done

# One line per link: id, doi and url, separated by tabs.
queue=()
while IFS= read -r line; do queue+=("$line"); done < <(sqlite3 -separator $'\t' "$db" "
  ATTACH '${snapshot//\'/\'\'}' AS d;
  SELECT rowid, doi, url FROM d.datasets
  WHERE role = 'produced'
    AND url NOT IN (SELECT url FROM inspections)
    $not_skipped
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
  # Every step the agent takes (thinking, commands and their output, its
  # answer) is printed as it happens, made readable from Pi's JSON events.
  # Pi runs without the R2 token; only publish.sh needs it.
  LINK_URL=$url PAPER_DOI=$doi ${limit[@]+"${limit[@]}"} \
    env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY \
    pi -p --mode json --no-session --model einfra/kimi-k3 \
      --append-system-prompt "$here/inspection-instructions.md" \
      "Look at the dataset $url from the paper $doi." 2>&1 </dev/null \
    | tee events.jsonl | jq --unbuffered -rR -f "$here/bin/readable-events.jq"
  code=${PIPESTATUS[0]}

  # The agent's last text message is its report: the handoff to the conversion agent.
  jq -rRs '[split("\n")[] | fromjson?
            | select(.type == "message_end" and .message.role == "assistant")
            | [.message.content[] | select(.type == "text") | .text] | join("\n")
            | select(length > 0)] | last // empty' events.jsonl >report.md

  q=${url//\'/\'\'}
  status=$(sqlite3 "$db" "SELECT status FROM inspections WHERE url = '$q'")
  if [[ -z $status ]]; then
    status=failed
    reason="agent did not save a result (exit code $code)"
    [[ $code == 124 ]] && reason="timed out after $per_link"
    sqlite3 "$db" "INSERT OR IGNORE INTO inspections (url, doi, status, inspected_at, note)
                   VALUES ('$q', '${doi//\'/\'\'}', 'failed', date('now'), '$reason')"
  fi
  sqlite3 "$db" "UPDATE inspections SET report = NULLIF(CAST(readfile('report.md') AS TEXT), '')
                 WHERE url = '$q'"
  echo "=== [$n/${#queue[@]}] $url: $status ==="
  cd "$work"
  [[ ${KEEP_LINK_DIRS:-} == 1 ]] || rm -rf "$dir"
  # Publish along the way, so a long pass shows up before it ends.
  if ((n % 10 == 0)); then "$here/bin/publish.sh" "$db" || echo "Publishing failed; continuing."; fi
done
rm -f "$snapshot"

echo
echo "Inspections so far:"
sqlite3 "$db" "SELECT '  ' || status || ': ' || count(*) FROM inspections GROUP BY status"

echo
"$here/bin/publish.sh" "$db"
