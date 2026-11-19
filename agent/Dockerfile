# The paper agents (literature search, dataset links, structure inspection and extraction): Pi plus the tools their scripts need.
#   docker build --platform linux/amd64 -t paper-agent agent
FROM node:24-bookworm-slim

# Tools used by the scripts in bin/
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl jq sqlite3 python3 awscli git gh \
 && rm -rf /var/lib/apt/lists/*

# uv: the inspection and extraction agents' only way to Python; it installs packages as needed.
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /usr/local/bin/

# Same Pi version as the local install.
RUN npm install -g @earendil-works/pi-coding-agent@1.1.0

# The agent's config, copied file by file so secrets (.env, auth.json) never get in.
# Owned by user 1000, because Pi writes its runtime files into this folder.
COPY --chown=1000:1000 models.json instructions.md schema.sql \
     datasets-instructions.md datasets-schema.sql \
     inspection-instructions.md inspection-schema.sql \
     extraction-instructions.md extraction-schema.sql /app/agent/
COPY --chown=1000:1000 bin/ /app/agent/bin/

ENV PI_CODING_AGENT_DIR=/app/agent \
    PAPERS_DB=/data/papers.db \
    DATASETS_DB=/data/datasets.db \
    INSPECTIONS_DB=/data/inspections.db \
    EXTRACTIONS_DB=/data/extractions.db \
    UV_CACHE_DIR=/work/.uv-cache \
    UV_PYTHON_INSTALL_DIR=/work/.uv-python \
    PATH=/app/agent/bin:$PATH

# User 1000 is "node" in this image; numeric, so Kubernetes can check it isn't root.
USER 1000
WORKDIR /work

# The search round; the other agents' CronJobs run explore.sh / inspect.sh / extract.sh instead.
CMD ["search-round.sh"]
