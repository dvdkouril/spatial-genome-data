#!/usr/bin/env bash
# The weekly search round: one Pi run, then publish.sh. Publishes even if the
# run failed, since the papers saved before the failure are in the database.
#   search-round.sh
set -uo pipefail

# Pi runs without the R2 token; only publish.sh needs it.
env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY \
  pi -p --no-session --model einfra/kimi-k3 \
    --append-system-prompt "$(dirname "$0")/../instructions.md" \
    "Run today's search round."
code=$?

echo
"$(dirname "$0")/publish.sh" || exit
exit $code
