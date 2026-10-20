#!/usr/bin/env bash
# Search Europe PMC and print only papers that are not in the database yet.
#   search.sh '<query>' [cursor]
# The database is $PAPERS_DB. Papers are identified by DOI, else PMC id, else Europe PMC id.
set -euo pipefail

query=${1:?usage: search.sh '<query>' [cursor]}
cursor=${2:-*}
db=${PAPERS_DB:?set PAPERS_DB to the papers database}

known=$(mktemp)
trap 'rm -f "$known"' EXIT
if [[ -f $db ]]; then
  sqlite3 "$db" "SELECT lower(doi) FROM papers" >"$known"
fi

curl -sfG https://www.ebi.ac.uk/europepmc/webservices/rest/search \
  --data-urlencode "query=$query" \
  --data-urlencode "cursorMark=$cursor" \
  -d format=json -d resultType=core -d pageSize=25 |
  jq -r --rawfile known "$known" --arg query "$query" '
    ($known | split("\n") | map(select(. != "")) | map({(.): true}) | add // {}) as $seen
    | [.resultList.result[] | . + {key: (.doi // .pmcid // .id)}] as $page
    | [$page[] | select($seen[.key | ascii_downcase] | not)] as $new
    | "\(.hitCount) results in total. This page: \($page | length), already known: \(($page | length) - ($new | length)), new: \($new | length).",
      "",
      ($new[] |
        "- \(.key) | \(.pubYear) | \(.journalInfo.journal.title // .source)",
        "  \(.title)",
        "  Type: \(.pubTypeList.pubType // [] | map(ascii_downcase | select(startswith("research support") | not)) | unique | join(", "))"
          + ((.tmAccessionTypeList.accessionType // [] | map(select(. != "doi"))) as $acc
             | if $acc | length > 0 then " | Accession numbers in text: \($acc | join(", "))" else "" end),
        "  \((.abstractText // "no abstract") | gsub("<[^>]+>"; " ") | gsub("\\s+"; " "))",
        ""),
      (if .nextCursorMark and .nextCursorMark != .request.cursorMark and ($page | length) > 0
       then "Next page: search.sh \($query | @sh) \(.nextCursorMark | @sh)" else "No more pages." end)
  '
