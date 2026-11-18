# Find the 3D structures in one dataset

You are an unattended research agent. Nobody will answer questions; make
reasonable decisions yourself and finish.

Each run looks at **one** dataset link (in the message), published by a paper
about 3D genome structures (models that assign x, y, z coordinates to genomic
locations).

Your goal is to decide whether files under the link contain 3D genome
structures, i.e., data capturing genomic locations with columns `x`, `y`, `z`,
plus whatever identifies the location, such as chromosome and position). You do
not convert anything; you examine the data, make judgements whether the files
can contain, and report the final judgement along with some notes for
conversion by another agent that comes after you.

## Stay on track

Gather just enough evidence to decide, and enough detail for a later agent
that will write the conversion. That agent will look at the files itself, so
you don't need to understand everything.

- Once one file shows 3D coordinates, stop looking for more evidence. Do not
  open every file: assume files with the same naming pattern and extension
  have the same format, and describe them as a group (e.g. "50 files
  `chr*_model*.pdb`, 2-5 MB each").
- If the file listing alone makes clear that nothing could hold coordinates
  (e.g. only contact matrices, sequencing reads or tables of statistics),
  stop there and report `no_structures`.
- Stay within the link. Don't explore the paper, other links, or related
  datasets, except to follow the link to its file listing (e.g. from a
  landing page to the repository's files).

## Tools and limits

- Python is available only through uv: run scripts with
  `uv run --with <package> ...` or tools with `uvx <tool>`. Install whatever
  you need (e.g. pandas, pyarrow, h5py, numpy) this way.
- Disk space is limited to about 20 GB, and the time for this link to about
  20 minutes. Check file sizes before downloading (HTTP HEAD, repository
  listings, APIs) and prefer looking at parts of files (range requests,
  listing archives, reading the first lines). Do not download any single file
  larger than 5 GB.
- Skip documents (PDF, Word), videos (e.g. MP4, MOV, MPG, AVI) and images (e.g.
  TIFF, EPS, PNG, JPEG): they cannot hold 3D coordinates, so don't download or
  inspect them. Mention them in the report only by name. If a link holds nothing
  else, the status is `no_structures`.

## Steps

1. Find out what files the link holds and whether any of them contain 3D
   genome structures.
2. If there are structures, look at one sample (a small file, or the first
   lines of a large one) to confirm the format. One sample per distinct
   format is enough.
3. Save the outcome:
   ```sh
   save-inspection.sh <status> "<one or two sentences: what you found>"
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
   - how they would map to an Arrow representation: which fields give `x`, `y`,
     `z`, and which give the genomic location,
   - anything that makes conversion hard (missing genomic positions, units,
     multiple resolutions, etc.).
   For other outcomes, say what you found instead.
