# Maytin et al. minimal-cell chromosome simulations

**Paper:** Andrew K. Maytin, Benjamin R. Gilbert, and Zaida Luthey-Schulten, “Chromosome segregation in a minimal bacterial cell driven by SMC protein complexes,” *Protein Science* 35(6), e70604 (2026). [DOI: 10.1002/pro.70604](https://doi.org/10.1002/pro.70604)  
**Data:** [Zenodo 10.5281/zenodo.19959420](https://doi.org/10.5281/zenodo.19959420), CC BY 4.0.

The deposit contains polymer-based 4D simulations of the 543-kbp circular chromosome of the minimal bacterium **JCVI-syn3A**, including replication, SMC loop extrusion, and segregation. The seven selected runs cover four SMC number/speed/dwell-time conditions, no cell swelling, delayed topoisomerase action, and no topoisomerase action. The drivers save chromosome snapshots once per simulated minute, normally minutes 0–90. A chromosome has 54,338 parental beads (**10 bp per bead**) and grows to 108,676 beads after replication. Coordinates are in the simulation's ångström length units.

## Download and output

`protein_science_zenodo.zip` is 22.85 GB and contains seven 3.08–3.71 GB run archives. The notebook does **not** save these archives. It uses HTTP ranges to stream only the nested tar members needed, caching selected chromosome binaries in `data/<run>/`; cached files are reused. The 213 MB container ZIP is not needed.

Each initial `x_chain_...bin` and time-series `dna_<run>_<minute>.bin` is little-endian, row-major float64 `(x,y,z)` data. Each becomes one `out/<run>_initial.arrow` or `out/<run>_minute_NNN.arrow` via `pyarrow.ipc.new_file`, with columns:

- `x`, `y`, `z`: float64, unchanged from the simulation;
- `chr`: string, `JCVI-syn3A`;
- `coord`: int64, 0-based reference-genome bead start in bp.

Parental bead `i` gets `coord = 10*i`. Replicated beads are appended around the replication midpoint in the order documented by the authors' `compute_partitioning.py`; they receive their parental copy's reference start. Consequently, duplicated loci intentionally have duplicate `coord` values. This conversion covers the explicit initial and per-minute chromosome configurations, not non-genomic ribosome coordinates or the much larger raw LAMMPS trajectory files.

## Run

```sh
uvx marimo edit --sandbox notebook.py
# or execute all cells:
uv run notebook.py
```

For a small test, set `MAX_STRUCTURES_PER_RUN = 2` near the top (the first two initial/time-series configurations stored in each archive), then run. Set it to `None` to discover and convert all these chromosome configurations in all seven runs. Tar members are not chronological, so a limited run does not necessarily select minute zero, or even an initial configuration. Full conversion can take substantial network time because gzip members must be read sequentially, but individual archives are never downloaded to disk. Cached results are reused on later runs, although scanning a remote gzip stream can still transfer skipped bytes.
