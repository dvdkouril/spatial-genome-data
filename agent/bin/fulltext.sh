#!/usr/bin/env bash
# Print a paper's open-access full text from Europe PMC as plain text.
#   fulltext.sh <id> > paper.txt   (a DOI, PMC id or Europe PMC id, as stored in the papers table)
# Exit codes: 0 printed, 3 no open-access full text in Europe PMC, other = error.
set -euo pipefail

id=${1:?usage: fulltext.sh <id>}
api=https://www.ebi.ac.uk/europepmc/webservices/rest
attempts=6 # waits 2, 4, ... 32 s in between: about a minute in all

# Europe PMC is sometimes "temporarily unavailable", answering with an error
# object (even with HTTP status 200); try again after a pause before giving up.
pause() { sleep $((2 ** $1)); }

case $id in
  PMC* | PPR*) key=$id ;;
  *)
    for ((i = 1; ; i++)); do
      result=$(curl -sG "$api/search" --data-urlencode "query=DOI:\"$id\"" -d format=json -d pageSize=1 || true)
      jq -e '.hitCount' >/dev/null 2>&1 <<<"$result" && break
      if ((i == attempts)); then
        echo "Europe PMC search failed: $(head -c 200 <<<"$result")" >&2
        exit 1
      fi
      pause "$i"
    done
    key=$(jq -r '.resultList.result[0].pmcid // empty' <<<"$result")
    ;;
esac
if [[ -z $key ]]; then
  echo "No open-access full text in Europe PMC for $id." >&2
  exit 3
fi

xml=$(mktemp)
trap 'rm -f "$xml"' EXIT
for ((i = 1; ; i++)); do
  code=$(curl -s -o "$xml" -w '%{http_code}' "$api/$key/fullTextXML" || true)
  [[ $code == 200 ]] && break
  if [[ $code == 404 ]] || { [[ $code == 500 ]] && ! grep -q '"errCode":503' "$xml"; } && ((i >= 2)); then
    # Europe PMC answers 404 or 500 for articles it has no full text for;
    # a second try rules out a passing hiccup.
    echo "No open-access full text in Europe PMC for $id ($key)." >&2
    exit 3
  fi
  if ((i == attempts)); then
    echo "Europe PMC returned HTTP $code for $key: $(head -c 200 "$xml")" >&2
    exit 1
  fi
  pause "$i"
done

python3 -I "$(dirname "$0")/jats-to-text.py" "$key" <"$xml"
