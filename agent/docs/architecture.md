# Architecture

## Goal

Automatically discover published datasets of 3D genome structures (chromatin
models from physical simulations or single-cell Hi-C reconstructions).

## Pipeline stages

The agentic workflow has a couple of stages. The role of an LLM is to mainly
make decisions regarding relevancy of found research artifacts.

| Stage | What happens | LLM decides | Code does |
|---|---|---|---|
| 1. Search | Make queries across a number of possible repositories (journals, aggregators, bioRxiv, arXiv) | Which queries to run; how to rephrase when results are off-target | Calls the repositories' search APIs |
| 2. Screen titles + abstracts | Does the paper actually use 3D structures? | Does the paper use 3D structures, or only discuss genome organization? | Saves relevant papers, skips duplicates |
| 3. Examine the full text | Confirm that physical 3D models are featured; extract relevant figures; extract links to datasets | Do the text and figures show actual 3D models? Which figures are relevant? Which links point to datasets? | Fetches full text and figures; stores the extracted figures and links |
| 4. Find and download the data | Follow the dataset links and get the files | Which link and which files are the dataset | Follows links, downloads files |
| 5. Extract 3D structure data | Keep only 3D structure data; note file formats | Which files are 3D structures and which are something else (e.g. raw contact matrices); which format each is | Unpacks archives, reads file headers, records formats |
| 6. Convert | Convert into a unified representation: Arrow format suitable for use in uchimata | How the source format maps onto the unified representation | Converts and writes Arrow files |

Across stages, the LLM also decides when to go deeper on a paper, when to drop
it, and when the search has covered enough.

## Roadmap

Essentially, the stages above each correspond to an agent responsible for the
tasks in that stage. We will build the whole pipeline incrementally, starting
with the functionality to search for papers within a topic.

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
