# Architecture

## Goal

Automatically discover published datasets of 3D genome structures (chromatin
models from physical simulations or single-cell Hi-C reconstructions), and
record where their data can be downloaded. Found datasets are candidates for
conversion into this repo's Arrow format.

## Pipeline stages

The agent works in stages. In each one, the LLM makes the judgment calls on
messy text; the code does the mechanical work and enforces hard rules.

| Stage | LLM decides | Code does |
|---|---|---|
| 1. Search | Which queries to run; how to rephrase when results are off-target | Calls the literature API (Europe PMC) |
| 2. Screen abstracts | Does the paper *produce* 3D structures, or only discuss genome organization? | Saves relevant papers, skips duplicates |
| 3. Examine the paper | Do the text and figures show actual coordinates (individual cells, ensembles, simulation snapshots)? | Fetches full text and figures |
| 4. Find the data | Where the data lives: data availability statements, supplement lists, GEO / Zenodo / GitHub links | Fetches the pages it points to |
| 5. Check downloads | Is this file structures or something else (e.g. raw contact matrices)? Which format? | Probes URLs, reads file headers |

Across stages, the LLM also decides when to go deeper on a paper, when to drop
it, and when the search has covered enough.

Guard rails belong in code, not in the prompt. For example, `save_paper` only
accepts DOIs that appeared in search results, so the model can't save an
invented DOI.

## How it runs

```
 GitHub repo (agent code + prompt)
        │  push
        ▼
 GitHub Actions ── builds image ──▶ Harbor (cerit.io/<user>/paper-scout:<commit>)
                                          │
 ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ CERIT Kubernetes ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
                                          ▼
   CronJob (on a schedule) ──starts──▶ Pod: one agent round, then exits
                                        │        │            │
                                        │        │            └─▶ Europe PMC (search)
                                        │        └─▶ LLM API (OpenAI-compatible)
                                        ▼
                            PersistentVolume (/data)
                              ├── agent.sqlite   ← pi-durable state + transcripts
                              └── papers.jsonl   ← results, one line per paper
```

- **Agent program.** A TypeScript program using
  [pi-durable](https://github.com/earendil-works/pi/tree/main/packages/durable).
  It has a fixed system prompt and task prompt, and a small set of tools. The
  prompt lives in the code; changing it means redeploying.
- **One round per run.** Each run submits the task, lets the agent loop (model →
  tool → model …) until the model is done, saves results, and exits. Each
  round starts a fresh conversation; `save_paper` deduplicates, so the model
  needs no memory of earlier rounds.
- **CronJob.** Kubernetes starts a round on a schedule.
  `concurrencyPolicy: Forbid` ensures only one round runs at a time.
- **Crash recovery.** If the pod dies mid-round, the Job starts a new one. It
  opens the same `agent.sqlite`, and `harness.resume()` continues from the last
  checkpoint. Each round is submitted with a fixed `requestId` (e.g.
  `round-2026-10-12`), so a restart doesn't start a second round.
- **PersistentVolume.** Holds the durable state and the results across runs.
  `agent.sqlite` also records every search and decision, which is useful for
  tuning the prompt.
- **LLM.** An OpenAI-compatible inference API, reached over HTTP and configured
  as a custom pi-ai provider (base URL, model id, API key).
- **Image build.** GitHub Actions builds the image and pushes it to Harbor
  using a Harbor robot account. Deploying is a manual `kubectl apply`.

## Constraints

- **pi-durable: one process per storage.** There is no cross-process locking.
  Never run two pods on the same `agent.sqlite`.
- **pi-durable is experimental.** Pin exact package versions. The README on
  GitHub `main` can be ahead of the npm release, so check the installed types.
- **CERIT pod requirements.** Pods are rejected without:
  - pod `securityContext`: `runAsNonRoot: true`,
    `seccompProfile: {type: RuntimeDefault}` (plus `runAsUser: 1000` for
    images that default to root, like `node`)
  - container `securityContext`: `allowPrivilegeEscalation: false`,
    `capabilities: {drop: ["ALL"]}`
  - resource requests/limits (CERIT fills in 1 CPU / 512 MB if missing)
- **No secrets in images.** All Harbor images can be pulled by anyone who
  knows the name. API keys go in a Kubernetes Secret.
- **Image architecture.** Build for `linux/amd64` (`docker build --platform
  linux/amd64`); Apple Silicon builds arm64 by default.
- **The LLM must support tool calling.** Everything depends on it.

## Left out on purpose (for now)

| Left out | Why it can wait |
|---|---|
| HTTP API, Service | Nothing needs to talk to the agent; the prompt is fixed |
| Subagents, multi-agent stages | Only worth it if one agent's results are poor |
| Stages 3–5 | First check that stage 1–2 finds the right papers |
| Egress NetworkPolicy | Low risk while tools only search and append to a file; add once the agent fetches arbitrary URLs |
| Database, dashboard | `papers.jsonl` is enough to start |

## Roadmap

Each increment ends with something that runs.

| # | Increment | Done when | Status |
|---|---|---|---|
| 0 | Hello-world container on CERIT, deployed by hand (Harbor, `kubectl`, manifest) | Pod logs show its output | todo |
| 1 | LLM check: a tiny script calling the LLM API with one fake tool | The model correctly asks for the tool | todo |
| 2 | Search agent, locally: fixed prompt, `search_papers` + `save_paper`, one round then exit | `papers.jsonl` contains sensible papers | todo |
| 3 | Deploy the search agent: image in Harbor, CronJob + PersistentVolume + Secret | Runs on schedule; results survive between rounds | todo |
| 4 | Automate the image build (GitHub Actions + Harbor robot account) | A push produces a new image | todo |
| later | Stages 3–5: examine papers, find data, check downloads | One stage at a time | — |
| later | Results somewhere visible (GitHub issues or commits) instead of a file | — | — |

## Open decisions

- **Schedule:** daily or weekly? New papers appear slowly.
- **Results:** `papers.jsonl` on the PersistentVolume to start (read with
  `kubectl cp`); later GitHub issues, commits, or the R2 bucket?
- **Model:** which model on the LLM API, and does it handle tool calling and
  relevance judgment well enough?
