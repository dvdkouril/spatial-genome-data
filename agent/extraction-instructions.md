# Find the 3D structures in one dataset

You are an unattended research agent. Nobody will answer questions; make
reasonable decisions yourself and finish.

Each run looks at **one** dataset link (in the message), published by a paper
about 3D genome structures (models that assign x, y, z coordinates to genomic
locations).

Your goal is to decide whether files under the link contain 3D genome
structures, and if so, how they could be converted into the Apache Arrow
representation used by uchimata (one row per genomic location, columns `x`,
`y`, `z`, plus whatever identifies the location, such as chromosome and
position). You do not convert anything; you report.

## Tools and limits

- Python is available only through uv: run scripts with
  `uv run --with <package> ...` or tools with `uvx <tool>`. Install whatever
  you need (e.g. pandas, pyarrow, h5py, numpy) this way.
- Disk space is limited to about 20 GB, and the time for this link to about
  20 minutes. Check file sizes before downloading (HTTP HEAD, repository
  listings, APIs) and prefer looking at parts of files (range requests,
  listing archives, reading the first lines). Do not download any single file
  larger than 5 GB.

## Steps

1. Find out what files the link holds and whether any of them contain 3D
   genome structures.
2. If there are structures, look at a sample of one file to confirm the format.
3. Save the outcome:
   ```sh
   save-extraction.sh <status> "<one or two sentences: what you found>"
   ```
   status is one of:
   - `has_structures`: you saw 3D coordinates in at least one file.
   - `no_structures`: the files hold other kinds of data (say which).
   - `too_large`: the files that likely hold structures are too large to
     inspect within the limits (say which files and their sizes).
   - `unclear`: you could not tell, e.g. access restricted or unknown format
     (say why).
4. Finish with a short report, in plain text:
   - the files that hold structures (names, format, sizes, how many models),
   - what the columns or fields mean,
   - how they would map to Arrow: which fields give `x`, `y`, `z`, and which
     give the genomic location,
   - anything that makes conversion hard (missing genomic positions, units,
     multiple resolutions, etc.).
   For other outcomes, say what you found instead.
