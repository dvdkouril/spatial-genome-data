# Agent for finding spatial genome datasets

Key ideas:
- search for possible sources of datasets that contain 3D genome models, i.e.,
  physical simulations of DNA folded in cells
- start with looking for publications on the topic
- examine potentially relevant papers: look at content and figures
- identify data in supplemental materials
- see if it is possible to download the data

Ultimate goals / ideas:
- interactive database / explorer for available datasets:
    - zoomable scatterplot of some form of embedding

## How it works

A plain [Pi](https://pi.dev) install does the literature search. It gets its
task from `instructions.md`, searches Europe PMC with `bin/search.sh`, and
saves its verdicts with `bin/save.sh` into a SQLite database of papers.

Files:
- `models.json`: the e-INFRA LLM provider (`kimi-k3`). The API key is read
  from the `LLM_API_KEY` environment variable, so the file holds no secret.
- `instructions.md`: topic, how to search and save, round procedure.
  Change the agent's behavior here.
- `bin/search.sh '<query>'`: searches Europe PMC and prints only papers that
  are not in the database yet, in a compact form.
- `bin/save.sh batch.json`: checks a JSON array of judged papers and inserts
  the new ones.
- `bin/export.sh`: writes the database to `data/papers.csv`, the backup.
- `schema.sql`: the `papers` table. `save.sh` creates it if needed.
- `data/papers.db`: the database (git-ignored).
- `data/papers.csv`: backup of the database, committed to git.
- `docs/`: architecture and deployment notes; `hello/`: Kubernetes example.

Both scripts use the database at `$PAPERS_DB`. You can run them yourself too.

## Run locally

Requires `pi`, `curl`, `jq` and `sqlite3`. Commands are for fish, run from the
repo root.

Once per terminal session:
```fish
set -x PI_CODING_AGENT_DIR (pwd)/agent   # use this folder as Pi's config, not ~/.pi/agent
set -x LLM_API_KEY (grep '^LLM_API_KEY=' agent/.env | cut -d= -f2-)   # key from agent/.env (git-ignored)
set -x PAPERS_DB (pwd)/agent/data/papers.db
set -x PATH (pwd)/agent/bin $PATH        # so the agent finds search.sh and save.sh
mkdir -p agent/data
```

Run a round from the empty folder `agent/work/` (git-ignored), so the agent
has nothing else to explore and its temporary files stay out of the repo
(interactive, shows every step):
```fish
rm -rf agent/work; mkdir agent/work   # start empty; the last run's leftovers stay until here
cd agent/work
pi --no-session \
   --model einfra/kimi-k3 \
   --append-system-prompt $PI_CODING_AGENT_DIR/instructions.md \
   "Run today's search round."
cd -
```

Add `-p` to run it unattended: it prints only the final summary and exits.
This is how it will run on Kubernetes.

## Look at the results

```fish
sqlite3 $PAPERS_DB "SELECT verdict, count(*) FROM papers GROUP BY verdict"
```
For a spreadsheet, open `agent/data/papers.csv` after an export (see below).

## Back up and restore

The database lives only in `data/`. After each run, export it to
`agent/data/papers.csv` (committed, sorted, so the diff shows what the round added)
and push:
```fish
agent/bin/export.sh
jj commit -m "papers: round YYYY-MM-DD"   # then push
```

To rebuild the database from that CSV (e.g. on a new machine):
```fish
sqlite3 $PAPERS_DB < agent/schema.sql
sqlite3 $PAPERS_DB ".import --csv --skip 1 agent/data/papers.csv papers"
```
