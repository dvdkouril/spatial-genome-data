# Architecture

This document describes an architecture for an automated literature and dataset
discovery system.

The benefits of an LLM/AI-based system are in:
- refining the keywords used in searches; adjusting based on new terms from
  found works that are decided to be relevant
- making the decision whether a discovered paper is or isn't relevant, based on
  title, abstract, full text

## Goal

Automatically discover published datasets of 3D genome structures (chromatin
models from physical simulations or single-cell Hi-C reconstructions).

The high-level workflow:
1. Discover publications and pre-prints relevant to the topic of interested
2. Examine full-text and supplemental materials of each discovered publication;
   decide: possibly relevant or not
3. Search for associated datasets; download
4. Identify data depicting the target data type (3D genome structures)
5. Extract, convert, store for visualization

There are two use cases:
- initial discovery: find out which papers are out there currently;
  continuously attempt to find new relevant papers that have been missed in
  past searches
- new findings: when a new paper is published on the topic, we want a mechanism
  to discover it easily

## Target topic specification

We are interested in finding papers that employ simulations or predictions of
DNA folding in cells. We want to focus on data that represent actual 3D
physical models: models that associate genomic locations with x, y, z
coordinates in 3D space.

## Key example papers
- Stevens
- Tan

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

Implementation stages:
1. simple local agent that fetches Europe PMC and saves the results into a
   database
2. deploy the agent on CERIT-SC Kubernetes platform
3. agent that decides whether a work is relevant or not
