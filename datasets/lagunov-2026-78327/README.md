# Lagunov et al. lampbrush chromosome models

**Paper:** Timofey Lagunov et al., “The 3D genomics of lampbrush chromosomes highlights the role of active transcription in chromatin organization,” *Nucleic Acids Research* (2026). DOI: [10.1093/nar/gkag316](https://doi.org/10.1093/nar/gkag316).

**Source:** <https://genedev.bionet.nsc.ru/ftp/by_User/tlagunov/LBCs/htmls/>

## Data

Chicken (*Gallus gallus*) chromosome 1, 55–64 Mb, modeled with coarse-grained Polychrom molecular dynamics. The four standalone Plotly HTML files contain two stages (LBC and post-LBC, `_late`) in native 3D (`Spatial`) and after simulated flattening (`Flat`). Flattening mimics chromosome preparation for microscopy; it is not an independent biological replicate.

Each HTML file has one `3D structure` trace containing two sister-chromatid chains. The LBC models have 20,374 points (10,187 per chain), and the post-LBC models have 8,504 points (4,252 per chain). Genomic spacing is variable, 450–2,303 bp between adjacent labels. The paper uses chicken T2T assembly ASM2420605v2. Model lengths are described in nm in the supplementary methods.

The notebook downloads all four files into `data/`, totaling **161,207,458 bytes (153.7 MiB)**. Existing files with the expected sizes are skipped. No single file exceeds 53 MiB.

## Output

`out/` contains one Arrow IPC file per selected HTML file, named after it. Each has `x`, `y`, `z` (float64), `chr` (string), and `coord` (int64, genomic start in bp), taken directly from the Plotly coordinate arrays and hover labels. Coordinates are not rescaled.

Both sister chromatids and their original order are preserved. The first half follows increasing genomic position and the second half follows it in reverse, so locus labels intentionally occur twice. Styling-only DAPI/BAC/mRNA copies and non-genomic SMC/RNA-polymerase overlays are not exported.

## Run

```sh
uvx marimo edit --sandbox notebook.py
# or execute the complete conversion:
uv run notebook.py
```

Set `MAX_STRUCTURES` near the top of `notebook.py` to a small integer for a trial; `None` converts all four. Downloads and Arrow output are resolved relative to the notebook, not the current directory.

## Caveats

- The HTML does not identify a numbered simulation replica or explicitly state its genome assembly/coordinate units; the assembly and nm units above come from the paper and supplementary methods.
- Bead sizes are variable, so these models do not have one fixed genomic resolution.
- Split at the halfway row if separate chromatids are needed; no deduplication should be performed by `coord`.
