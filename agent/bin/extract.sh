#!/usr/bin/env bash
# One pass of the extraction agent: for dataset links the inspection agent found
# structures in, and that have no extraction yet (picked at random), one fresh
# Pi conversation writes a marimo notebook into datasets/<folder>/ of a clone
# of the repository; the folder is pushed to its own branch and a pull request
# is opened, also when the conversion did not work (as a draft), so the notebook
# can be refined by hand. Only "no structures after all" gets no pull request.
#   extract.sh [max links]
# Reads $INSPECTIONS_DB (never writes it), writes $EXTRACTIONS_DB. Pushes to
# $GITHUB_REPO (owner/name) with $GITHUB_TOKEN (contents and pull requests:
# write); Pi never sees the token. Work files go into the current directory.
set -uo pipefail

inspections=${INSPECTIONS_DB:?set INSPECTIONS_DB to the inspections database}
db=${EXTRACTIONS_DB:?set EXTRACTIONS_DB to the extractions database}
repo=${GITHUB_REPO:?set GITHUB_REPO to owner/name of the repository}
: "${GITHUB_TOKEN:?set GITHUB_TOKEN to a token that can push and open pull requests}"
max=${1:-1000000}
per_link=${LINK_TIMEOUT:-60m}
here=$(cd "$(dirname "$0")/.." && pwd)
work=$(pwd)
# Absolute, because each link runs in its own folder (also for save-extraction.sh).
db=$(cd "$(dirname "$db")" && pwd)/$(basename "$db")
export EXTRACTIONS_DB=$db

sqlite3 "$db" <"$here/extraction-schema.sql"

# Work from a snapshot, so the inspection agent can keep writing inspections.db.
snapshot=$work/inspections-snapshot.db
rm -f "$snapshot"
sqlite3 "$inspections" ".backup '${snapshot//\'/\'\'}'"

# One line per link: id, doi and url, separated by tabs.
queue=()
while IFS= read -r line; do queue+=("$line"); done < <(sqlite3 -separator $'\t' "$db" "
  ATTACH '${snapshot//\'/\'\'}' AS i;
  SELECT rowid, doi, url FROM i.inspections
  WHERE status = 'has_structures'
    AND url NOT IN (SELECT url FROM extractions)
  ORDER BY random()
  LIMIT $max")
echo "${#queue[@]} links to convert."
[[ ${#queue[@]} == 0 ]] && exit 0

# A fresh clone of the repository (public, so no token needed to read it).
clone=$work/repo
rm -rf "$clone"
git clone --quiet --depth 1 "https://github.com/$repo.git" "$clone" || exit 1
git -C "$clone" config user.name "extraction-agent"
git -C "$clone" config user.email "extraction-agent@users.noreply.github.com"
# The token is handed to git only when pushing; it is never written to disk.
push() {
  git -C "$clone" -c credential.helper= \
    -c credential.helper='!f() { echo username=x-access-token; echo "password=$GITHUB_TOKEN"; }; f' \
    push --quiet --force origin "$1"
}

# Time limit per link; coreutils timeout is gtimeout on macOS.
limit=()
if command -v timeout >/dev/null; then limit=(timeout "$per_link")
elif command -v gtimeout >/dev/null; then limit=(gtimeout "$per_link")
else echo "No timeout command found; links run without a time limit."
fi

# <first author>-<year>-<5 characters of the url's hash>, e.g. tan-2018-3f9a1.
folder_name() { # doi url
  local meta author year hash
  meta=$(curl -sf -m 30 -A "spatial-genome-data-agent" "https://api.crossref.org/works/$1")
  author=$(jq -r '.message.author[0].family // empty' <<<"$meta" 2>/dev/null |
    iconv -f utf-8 -t ascii//TRANSLIT 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z')
  year=$(jq -r '.message.issued."date-parts"[0][0] // empty' <<<"$meta" 2>/dev/null)
  hash=$(printf %s "$2" | { sha1sum 2>/dev/null || shasum; } | cut -c1-5)
  echo "${author:-unknown}-${year:-0000}-$hash"
}

n=0
for line in "${queue[@]}"; do
  n=$((n + 1))
  IFS=$'\t' read -r id doi url <<<"$line"
  q=${url//\'/\'\'}
  folder=$(folder_name "$doi" "$url")
  branch=extraction/$folder
  dir=$work/link-$id          # Pi's events and the PR text, outside the repository
  rm -rf "$dir" && mkdir -p "$dir"

  # Start from the current main, with only this dataset's folder.
  git -C "$clone" fetch --quiet --depth 1 origin main &&
    git -C "$clone" checkout --quiet --force -B "$branch" FETCH_HEAD &&
    git -C "$clone" clean --quiet -fdx || exit 1
  mkdir -p "$clone/datasets/$folder" && cd "$clone/datasets/$folder" || exit 1

  report=$(sqlite3 "$snapshot" "SELECT coalesce(report, note) FROM inspections WHERE url = '$q'")

  echo
  echo "=== [$n/${#queue[@]}] $url (paper $doi) -> datasets/$folder ==="
  # Every step the agent takes is printed as it happens; Pi runs without the
  # GitHub token, the wrapper pushes.
  LINK_URL=$url PAPER_DOI=$doi DATASET_FOLDER=$folder ${limit[@]+"${limit[@]}"} \
    env -u GITHUB_TOKEN -u GH_TOKEN \
    pi -p --mode json --no-session --model einfra/kimi-k3 \
      --append-system-prompt "$here/extraction-instructions.md" \
      "Convert the dataset $url from the paper $doi. You are in its folder datasets/$folder.

The inspection agent's report:

$report" 2>&1 </dev/null \
    | tee "$dir/events.jsonl" | jq --unbuffered -rR -f "$here/bin/readable-events.jq"
  code=${PIPESTATUS[0]}
  cd "$work"

  # The agent's last text message is the pull request description.
  jq -rRs '[split("\n")[] | fromjson?
            | select(.type == "message_end" and .message.role == "assistant")
            | [.message.content[] | select(.type == "text") | .text] | join("\n")
            | select(length > 0)] | last // empty' "$dir/events.jsonl" >"$dir/pr.md"

  status=$(sqlite3 "$db" "SELECT status FROM extractions WHERE url = '$q'")
  if [[ -z $status ]]; then
    status=failed
    reason="agent did not save a result (exit code $code)"
    [[ $code == 124 ]] && reason="timed out after $per_link"
    sqlite3 "$db" "INSERT OR IGNORE INTO extractions (url, doi, folder, status, extracted_at, note)
                   VALUES ('$q', '${doi//\'/\'\'}', '$folder', 'failed', date('now'), '$reason')"
  fi

  # A pull request for every outcome except "no structures after all", so the
  # notebook shows what the agent tried, whether or not it converted.
  if [[ $status != no_structures && -f $clone/datasets/$folder/notebook.py ]]; then
    # Only the dataset's folder, without downloads, outputs and marimo's cache;
    # files over 1 MB are left out and listed in the description.
    git -C "$clone" add -- "datasets/$folder" ":!datasets/$folder/data" \
      ":!datasets/$folder/out" ":!datasets/$folder/*__marimo__*"
    big=()
    while IFS= read -r -d '' f; do
      [[ -f $clone/$f && $(wc -c <"$clone/$f") -gt 1048576 ]] && big+=("$f")
    done < <(git -C "$clone" diff --cached --name-only -z)
    [[ ${#big[@]} -gt 0 ]] && git -C "$clone" reset --quiet -- "${big[@]}"

    case $status in
      converted) title="Dataset: $folder"; draft=() ;;
      not_converted) title="Dataset (not converted): $folder"; draft=(--draft) ;;
      *) title="Dataset (agent failed): $folder"; draft=(--draft) ;;
    esac
    note=$(sqlite3 "$db" "SELECT note FROM extractions WHERE url = '$q'")
    {
      echo "Dataset link: $url"
      echo "Paper: https://doi.org/$doi"
      echo "Outcome: **$status**: $note"
      [[ ${#big[@]} -gt 0 ]] && echo "Left out, over 1 MB: ${big[*]}"
      echo
      cat "$dir/pr.md"
    } >"$dir/pr-body.md"

    if git -C "$clone" commit --quiet -m "datasets: $folder" -m "From $url (paper $doi)." &&
      push "$branch"; then
      pr=$(GH_TOKEN=$GITHUB_TOKEN gh pr create --repo "$repo" --base main --head "$branch" \
             --title "$title" --body-file "$dir/pr-body.md" ${draft[@]+"${draft[@]}"} 2>&1 | tail -1)
      # Already open from an earlier attempt: the push updated it.
      [[ $pr == https://* ]] || pr=$(GH_TOKEN=$GITHUB_TOKEN gh pr view --repo "$repo" "$branch" --json url -q .url)
      sqlite3 "$db" "UPDATE extractions SET pr_url = '${pr//\'/\'\'}' WHERE url = '$q'"
      echo "Pull request: $pr"
    else
      sqlite3 "$db" "UPDATE extractions SET note = coalesce(note, '') || ' (pull request not opened: commit or push failed)'
                     WHERE url = '$q'"
      echo "Pull request not opened: commit or push failed."
    fi
  fi
  echo "=== [$n/${#queue[@]}] $url: $status ==="
done
rm -f "$snapshot"

echo
echo "Extractions so far:"
sqlite3 "$db" "SELECT '  ' || status || ': ' || count(*) FROM extractions GROUP BY status"
