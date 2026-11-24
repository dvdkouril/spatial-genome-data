# Bajpai & Safran chromosome-mixing structures

**Paper:** Gaurav Bajpai and Samuel Safran, “Mesoscale, long-time mixing of chromosomes and its connection to polymer dynamics,” *PLOS Computational Biology* 19(5), e1011142 (2023). DOI: [10.1371/journal.pcbi.1011142](https://doi.org/10.1371/journal.pcbi.1011142).

**Data:** [Zenodo record 7557330](https://zenodo.org/record/7557330), `Supporting_data.zip` (269,924,705 bytes; 257 MiB). The notebook checks the published MD5 and extracts only three LAMMPS configurations and their input scripts (about 28 MB). Videos are not extracted.

## Structures

These are coarse-grained LAMMPS bead-spring molecular-dynamics starting configurations, at **5 kb per chromatin bead**:

- `generic_homopolymer`: four equal synthetic chains, 8,810 beads each (35,240 total). The file header reports timestep 10,000.
- `block_copolymer_without_lamin`: *Drosophila* Chr2, Chr3, Chr4, and ChrX represented by 12,100, 13,760, 900, and 8,480 beads, respectively (35,240 total), with euchromatin/heterochromatin bead types.
- `block_copolymer_with_lamin`: the same four chromosomes plus 19,600 lamina particles. The lamina particles are excluded; LAD chromatin beads are retained.

The deposit has no output trajectories. Its three `.in` files are simulation controls, not additional structures.

## Output and interpretation

Run:

```sh
uv run notebook.py
```

or edit interactively with:

```sh
uvx marimo edit --sandbox notebook.py
```

The notebook downloads to `data/` and writes one Arrow IPC file per configuration to `out/`. Set `MAX_STRUCTURES` near the top of `notebook.py` to a small integer to limit a trial run; `None` converts all three. Existing downloads are reused.

Each output has `x`, `y`, `z` (float64), `chr` (string), and `coord` (int64), ordered along each chromosome by atom ID. There are 35,240 chromatin rows per file. The bond topology is checked before conversion.

**Caveats:** Coordinates are unchanged dimensionless LAMMPS `lj` values (the paper gives bead diameter σ = 30 nm), not physical distances. `coord` is a zero-based 5 kb model-bin start derived from atom order; no genome assembly or exact assembly alignment is supplied. Block-model chromosomes follow the paper's approximate whole-chromosome sizes and combine chromosome arms into single chains. Generic-model names `chr1`–`chr4` are synthetic labels, not the block model's biological chromosome identities.
