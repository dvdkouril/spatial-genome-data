#!/usr/bin/env bash
# Print the parts of a paper's open-access full text that can point to data.
#   fulltext.sh <id>   (a DOI, PMC id or Europe PMC id, as stored in the papers table)
# Exit codes: 0 printed, 3 no open-access full text in Europe PMC, other = error.
set -euo pipefail

id=${1:?usage: fulltext.sh <id>}
api=https://www.ebi.ac.uk/europepmc/webservices/rest

case $id in
  PMC* | PPR*) key=$id ;;
  *)
    key=$(curl -sfG "$api/search" --data-urlencode "query=DOI:\"$id\"" -d format=json -d pageSize=1 |
      jq -r '.resultList.result[0].pmcid // empty')
    ;;
esac
if [[ -z $key ]]; then
  echo "No open-access full text in Europe PMC for $id." >&2
  exit 3
fi

xml=$(mktemp)
trap 'rm -f "$xml"' EXIT
code=$(curl -s -o "$xml" -w '%{http_code}' "$api/$key/fullTextXML")
case $code in
  200) ;;
  404 | 500) # Europe PMC answers 500 for articles it has no full text for
    echo "No open-access full text in Europe PMC for $id ($key)." >&2
    exit 3 ;;
  *)
    echo "Europe PMC returned HTTP $code for $key." >&2
    exit 1 ;;
esac

python3 -I "$(dirname "$0")/jats-extract.py" "$key" <"$xml"
