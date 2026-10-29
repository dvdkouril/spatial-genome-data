#!/usr/bin/env bash
# One pass of the dataset agent: explore every relevant or maybe paper that is
# not in the datasets database yet, one fresh Pi conversation per paper.
#   explore.sh [max papers]
# Reads $PAPERS_DB (never writes it), writes $DATASETS_DB. Work files go into
# the current directory.
set -uo pipefail

papers=${PAPERS_DB:?set PAPERS_DB to the papers database}
db=${DATASETS_DB:?set DATASETS_DB to the datasets database}
max=${1:-1000000}
per_paper=${PAPER_TIMEOUT:-15m}
here=$(cd "$(dirname "$0")/.." && pwd)
work=$(pwd)

sqlite3 "$db" <"$here/datasets-schema.sql"

# Work from a snapshot, so the search agent can keep writing papers.db.
snapshot=$work/papers-snapshot.db
rm -f "$snapshot"
sqlite3 "$papers" ".backup '${snapshot//\'/\'\'}'"

queue=()
while IFS= read -r doi; do queue+=("$doi"); done < <(sqlite3 "$db" "
  ATTACH '${snapshot//\'/\'\'}' AS p;
  SELECT doi FROM p.papers
  WHERE verdict IN ('relevant', 'maybe')
    AND doi NOT IN (SELECT doi FROM explorations)
  ORDER BY verdict = 'relevant' DESC, year DESC
  LIMIT $max")
echo "${#queue[@]} papers to explore."

# Time limit per paper; coreutils timeout is gtimeout on macOS.
limit=()
if command -v timeout >/dev/null; then limit=(timeout "$per_paper")
elif command -v gtimeout >/dev/null; then limit=(gtimeout "$per_paper")
else echo "No timeout command found; papers run without a time limit."
fi

# Record a paper the agent could not save itself.
record() { # doi status note
  local q=${1//\'/\'\'} note=${3//\'/\'\'}
  sqlite3 "$db" "INSERT OR IGNORE INTO explorations (doi, status, explored_at, note)
                 VALUES ('$q', '$2', date('now'), '$note')"
}

n=0
for doi in "${queue[@]}"; do
  n=$((n + 1))
  dir=$work/paper-$n
  rm -rf "$dir" && mkdir -p "$dir" && cd "$dir" || exit 1

  PAPER_DOI=$doi ${limit[@]+"${limit[@]}"} \
    pi -p --no-session --model einfra/kimi-k3 \
      --append-system-prompt "$here/datasets-instructions.md" \
      "Find the data links of the paper $doi." >answer.txt 2>&1 </dev/null
  code=$?

  q=${doi//\'/\'\'}
  status=$(sqlite3 "$db" "SELECT status FROM explorations WHERE doi = '$q'")
  if [[ -z $status ]]; then
    reason="agent did not save a result"
    [[ $code == 124 ]] && reason="timed out after $per_paper"
    record "$doi" failed "$reason (exit code $code)."
    echo "[$n/${#queue[@]}] $doi: failed ($reason)"
    tail -5 answer.txt | sed 's/^/    /'
  else
    links=$(sqlite3 "$db" "SELECT count(*) FROM datasets WHERE doi = '$q'")
    echo "[$n/${#queue[@]}] $doi: $status ($links links)"
  fi
  cd "$work" && rm -rf "$dir"
done
cd "$work" && rm -f "$snapshot"

echo
echo "Explorations so far:"
sqlite3 "$db" "SELECT '  ' || status || ': ' || count(*) FROM explorations GROUP BY status"
