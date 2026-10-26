#!/usr/bin/env bash
# Save the data links found in the paper being explored.
#   save-exploration.sh result.json
# result.json is an object:
#   {"note": "...", "datasets": [{"url", "role", "reason", "evidence"}, ...]}
# The paper is $PAPER_DOI, its text (as shown to the agent) is in $PAPER_TEXT,
# and the database is $DATASETS_DB. Every link must be backed by an evidence
# sentence copied verbatim from that text, and the link must appear in it.
set -euo pipefail

result=${1:?usage: save-exploration.sh result.json}
db=${DATASETS_DB:?set DATASETS_DB to the datasets database}
doi=${PAPER_DOI:?set PAPER_DOI to the paper being explored}
paper=${PAPER_TEXT:?set PAPER_TEXT to the file with the paper text}

problems=$(jq -r --rawfile paper "$paper" '
  def norm: gsub("\\s+"; " ") | ascii_downcase | ltrimstr(" ") | rtrimstr(" ");
  # $s occurs in the input as a whole token, not as part of a longer id or URL
  def has($s): test("(?<![a-z0-9])" + ($s | gsub("(?<c>[.*+?^${}()|\\[\\]\\\\/])"; "\\\(.c)")) + "(?![a-z0-9_-])");
  ($paper | norm) as $text
  | if type != "object" or (.datasets | type) != "array" then
      "the file must contain an object with a \"datasets\" array (empty if the paper has no data links)"
    else
      (.datasets | map(.url) | group_by(.) | map(select(length > 1) | "listed twice: \(.[0])") | .[]),
      (.datasets[] |
        (.url // "") as $url | ((.evidence // "") | norm) as $ev |
        ($url | ascii_downcase | sub("^https?://"; "") | sub("^www\\."; "") | sub("/+$"; "")) as $bare |
        [ ($url | ascii_downcase | capture("[?&]acc=(?<a>[^&]+)").a),
          ($url | ascii_downcase | capture("doi\\.org/(?<a>.+)").a),
          ($bare | split("/") | last | select(test("[0-9]") and length >= 5)) ] as $ids |
        if ($url | test("^https?://") | not) then "not a full URL: \(.url | tojson)"
        elif (.role | IN("produced", "used", "code") | not) then "role must be produced, used or code: \($url)"
        elif $ev == "" then "missing evidence: \($url)"
        elif ($text | contains($ev) | not) then "evidence is not a verbatim quote from the paper text: \($url)"
        elif ($ev | has($bare)) or any($ids[]; . as $id | $ev | has($id)) then empty
        else "the link does not appear in its evidence (check it is copied exactly): \($url)"
        end)
    end' "$result")
if [[ -n $problems ]]; then
  echo "$problems" >&2
  echo "Nothing saved. Fix the entries and run save-exploration.sh again." >&2
  exit 1
fi

sqlite3 "$db" <"$(dirname "$0")/../datasets-schema.sql"
q=${doi//\'/\'\'} # quote for SQL
file=${result//\'/\'\'}
if [[ $(sqlite3 "$db" "SELECT count(*) FROM explorations WHERE doi = '$q'") != 0 ]]; then
  echo "$doi is already saved; nothing changed."
  exit 0
fi
status=$(jq -r 'if any(.datasets[]; .role == "produced") then "data_found" else "no_data" end' "$result")
sqlite3 "$db" "
  BEGIN;
  INSERT INTO explorations (doi, status, explored_at, note)
  SELECT '$q', '$status', date('now'), readfile('$file')->>'note';
  INSERT INTO datasets (doi, url, role, reason, evidence)
  SELECT '$q', value->>'url', value->>'role', value->>'reason', value->>'evidence'
  FROM json_each(readfile('$file'), '\$.datasets');
  COMMIT;"
echo "Saved $doi as $status with $(jq '.datasets | length' "$result") links."
