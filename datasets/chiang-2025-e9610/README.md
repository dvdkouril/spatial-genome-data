# Chiang et al. (2025) chromatin snapshots

**Paper:** Michael Chiang et al., “Bridging-Induced Phase Separation and Loop Extrusion Drive Noise in Chromatin Transcription,” *Physical Review Letters* 135, 158401 (2025). DOI: [10.1103/bjq4-xnsy](https://doi.org/10.1103/bjq4-xnsy).

**Data:** [Edinburgh DataShare, 10.7488/ds/7942](https://doi.org/10.7488/ds/7942).

The deposit contains coarse-grained polymer simulations of generic eukaryotic chromatin, with multivalent transcription-factor binding and cohesin-like loop extrusion; it is not tied to a particular organism or reference-genome locus. The convertible structures are eight single-timestep XYZ snapshots from Fig. 1 and Supplementary Figs. S1, S4, and S10. They contain 309–1,229 chromatin beads per snapshot, plus optional TF particles. A bead is a coarse-grained polymer monomer; no base-pair resolution is supplied.

## What the notebook does

- Downloads the deposit README and `fig1.tar.gz`, `sfig1.tar.gz`, `sfig4.tar.gz`, and `sfig10.tar.gz` into `data/`. The total is 143,917 bytes (about 141 KiB). Existing complete files are skipped. The much larger simulation-code archive and the movies are not downloaded.
- Finds every XYZ member in those archives, reads it directly from the tar file, and keeps the leading chromatin block. H, He, and B beads are retained; trailing Li/Be/C TF particles and patches are excluded.
- Writes eight `out/<snapshot-name>.arrow` files with `pyarrow.ipc.new_file`. Each has `x`, `y`, and `z` (float64, unchanged from the source), `bead_type` (the original H/He/B symbol), and zero-based `bead_index` (int64).
- Stores the source archive/member and model timestep in Arrow schema metadata, then reads every output back and validates its schema, row count, finite coordinates, and metadata.

`MAX_STRUCTURES` near the top defaults to `None` (all structures); set it to a small integer for a trial run.

## Run

```sh
uvx marimo edit --sandbox notebook.py
# or execute all cells without opening the editor:
uv run notebook.py
```

Python 3.12 or newer and `uv` are required. Marimo, NumPy, and PyArrow are declared inline in the notebook. Downloads and outputs remain in the git-ignored `data/` and `out/` directories beside the notebook.

## Caveats

`chr` and `coord` are intentionally absent: chromosome names, genomic positions, assembly, and bead-to-bp conversion are not available. `bead_index` is an ordering index, **not** a genomic coordinate. Coordinate units are unspecified in the deposit, so no unit conversion is attempted. The other figure archives contain plotting data rather than additional structures; the movies archive contains MP4 movies.
