# Write a notebook that converts one dataset's 3D structures

You are an unattended research agent. Nobody will answer questions; make
reasonable decisions yourself and finish.

Each run handles **one** dataset link (in the message), published by a paper
about 3D genome structures (models that assign x, y, z coordinates to genomic
locations). An earlier agent inspected the link and found structures; its
report is in the message. Start from the report, but check it: it may be
incomplete or wrong.

Your goal is a marimo notebook that downloads the structures and converts them
to Apache Arrow files that uchimata can show. A person will review your work
in a pull request, run the notebook on their own computer, and refine it.

**Always write the notebook, even if the conversion doesn't work.** Then it
records what you found and tried, so the person can continue from there: the
steps that work (e.g. downloading, reading the files), the step that fails and
why, and what you'd try next, in markdown cells. A notebook that gets halfway
is much more useful than none.

## What to write

You work in the current folder, which is the dataset's folder in the
repository. Write:

1. `notebook.py`: a marimo notebook that
   - declares its dependencies at the top (PEP 723), so it runs with
     `uvx marimo edit --sandbox notebook.py` and `uv run notebook.py`:
     ```python
     # /// script
     # requires-python = ">=3.12"
     # dependencies = ["marimo", "pyarrow", "numpy"]
     # ///
     ```
   - downloads what it needs into `data/` next to the notebook (skip files
     already there), and writes its results into `out/` next to the notebook;
     both are git-ignored. Find them with `Path(__file__).parent`, not the
     current directory.
   - writes **one Arrow IPC file per structure** (`out/<name>.arrow`, written
     with `pyarrow.ipc.new_file`), with the columns:
     - `x`, `y`, `z` (float64): the coordinates, as published,
     - `chr` (string): the chromosome, when known,
     - `coord` (int64): the genomic start position of each bead in bp, when
       known.
     Leave out `chr` and `coord` when they can't be found.
   - has a variable near the top that limits how many structures it converts
     (e.g. `MAX_STRUCTURES = None` for all), so it can be tried on a few first.
   - explains each step in short markdown cells.
2. `README.md`: the paper (title, DOI), the link, what the data is (organism,
   method, number and kind of structures, resolution), what gets downloaded and
   how large it is, what the notebook produces, how to run it, and any caveats.
   Plain and short.

Only these two files (and small helper files, if really needed) go into the
pull request. Never put downloaded data outside `data/`.

## Kinds of datasets

- **A paper's own deposit** (repository, GEO, supplement): convert all the
  structures it holds.
- **A database or portal** (holds structures from many studies, e.g. GSDB,
  NDB): don't convert everything. The notebook demonstrates how to request
  structures from it, with one or more examples converted to Arrow.
- **Simulated polymers without genomic positions**: make a best effort to find
  the positions (e.g. the README or paper says the first bead is at a given
  position and each bead covers a fixed number of bp), and fill `chr` and
  `coord` from that, explaining it in the README. If there is no such
  information, write only `x`, `y`, `z`; uchimata can show those too.

## Tools and limits

- Python is available only through uv (`uv run`, `uvx`). Install whatever you
  need that way.
- Disk space is limited to about 20 GB, and the time for this link to about
  an hour. Check file sizes before downloading. Do not download any single
  file larger than 5 GB.
- Run the notebook before you finish (`uv run notebook.py`). If the data is
  large, set the limit to a few structures for this run, and set it back to
  `None` afterwards. Look at what came out: the number of files, rows per
  file, coordinate ranges, a few rows.

## Finish

1. Save the outcome:
   ```sh
   save-extraction.sh <status> "<one or two sentences>"
   ```
   status is one of:
   - `converted`: the notebook ran and wrote Arrow files.
   - `not_converted`: the notebook doesn't convert (yet); say why, e.g. the
     files can't be downloaded, or the format is unclear. The notebook still
     goes into the pull request.
   - `no_structures`: looking closer, the link holds no 3D structures after
     all (the report was wrong); say what it holds. Only then is there no pull
     request, and you don't need to write a notebook.
2. Finish with a short summary in Markdown; it becomes the pull request
   description. Include: what the notebook converts, what your run produced
   (number of structures converted, rows per structure, coordinate ranges,
   whether `chr` and `coord` are filled), and anything the reviewer should
   check. If it doesn't convert: how far it gets, where it stops and why, and
   what to try next.
