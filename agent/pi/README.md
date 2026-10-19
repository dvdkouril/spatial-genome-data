# Pi search agent

A plain [Pi](https://pi.dev) install does the literature search. It gets its
task from `instructions.md`, searches Europe PMC with `curl` and `jq`, and
appends what it finds to a CSV file.

Files:
- `models.json`: the e-INFRA LLM provider (`kimi-k3`). The API key is read
  from the `LLM_API_KEY` environment variable, so the file holds no secret.
- `instructions.md`: topic, how to search, CSV format, round procedure.
  Change the agent's behavior here.
- `data/`: local test output (git-ignored).

## Run locally

Requires `pi`, `curl` and `jq`. Commands are for fish, run from the repo root.

Once per terminal session:
```fish
set -x PI_CODING_AGENT_DIR (pwd)/agent/pi   # use this folder as Pi's config, not ~/.pi/agent
set -x LLM_API_KEY (grep '^LLM_API_KEY=' agent/search/.env | cut -d= -f2-)   # key from the existing .env
mkdir -p agent/pi/data
```

Run a round and watch every step (interactive):
```fish
pi --no-session \
   --model einfra/kimi-k3 \
   --append-system-prompt agent/pi/instructions.md \
   "Run today's search round. Results file: agent/pi/data/papers.csv"
```

Add `-p` to run it unattended: it prints only the final summary and exits.
This is how it will run on Kubernetes.

## Check the results

Every row should have 9 fields:
```fish
python3 -c "import csv; [print(len(r)) for r in csv.reader(open('agent/pi/data/papers.csv'))]"
```
