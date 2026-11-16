# Find and convert the 3D structures in one dataset

You are an unattended research agent. Nobody will answer questions; make
reasonable decisions yourself and finish.

Each run looks at **one** dataset link (in the message), published by a paper
about 3D genome structures (models that assign x, y, z coordinates to genomic
locations).

Your overarching goal is to decide whether files under the link contain 3D
genome structures. If yes, you will attempt to convert these structures into
the Arrow representation used by uchimata. If not, you will write down what
types of data you find instead.

## Steps

1. Find out what files the link holds and whether any of them contain 3D
   genome structures. Use any tools you like; check file sizes before
   downloading, and prefer looking at parts of files.
2. If there are structures, write a marimo notebook `notebook.py` in the
   current folder that converts them to Apache Arrow files (columns `x`, `y`,
   `z`), and run it.
3. Save the outcome and finish with one line:
   ```sh
   save-extraction.sh <status> "<one or two sentences: what you found>"
   ```
   status is `converted`, `no_structures`, or `not_converted` (structures
   found but not converted; say why).
