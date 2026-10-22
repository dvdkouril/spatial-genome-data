# The literature search agent: Pi plus the tools its scripts need.
#   docker build --platform linux/amd64 -t paper-agent agent
FROM node:24-bookworm-slim

# Tools used by bin/search.sh and bin/save.sh.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl jq sqlite3 \
 && rm -rf /var/lib/apt/lists/*

# Same Pi version as the local install.
RUN npm install -g @earendil-works/pi-coding-agent@1.1.0

# The agent's config, copied file by file so secrets (.env, auth.json) never get in.
# Owned by user 1000, because Pi writes its runtime files into this folder.
COPY --chown=1000:1000 models.json instructions.md schema.sql /app/agent/
COPY --chown=1000:1000 bin/ /app/agent/bin/

ENV PI_CODING_AGENT_DIR=/app/agent \
    PAPERS_DB=/data/papers.db \
    PATH=/app/agent/bin:$PATH

# User 1000 is "node" in this image; numeric, so Kubernetes can check it isn't root.
USER 1000
WORKDIR /work

CMD ["pi", "-p", "--no-session", "--model", "einfra/kimi-k3", \
     "--append-system-prompt", "/app/agent/instructions.md", \
     "Run today's search round."]
