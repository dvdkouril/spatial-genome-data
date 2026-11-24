# Wu et al. 2025 single-cell Micro-C structures

- **Paper:** Honggui Wu et al., “Single-cell Micro-C profiles 3D genome structures at high resolution and characterizes multi-enhancer hubs,” *Nature Genetics* 57, 1777–1786 (2025). [doi:10.1038/s41588-025-02247-6](https://doi.org/10.1038/s41588-025-02247-6)
- **Data:** [GEO GSE192759](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE192759)
- **Organism and method:** human GM12878 lymphoblastoid cells, single-cell Micro-C, hg38. GEO has 352 cell samples. The supplement holds replicated, haplotype-resolved single-cell coordinate models at 5, 10, and 20 kb, including separately published `.clean` variants. The total number of models was not enumerated because the archive must be read sequentially.

## Download and output

The only structure supplement is `GSE192759_5kb_10kb_20kb_3dg_files.tar.gz`: **102,110,011,821 bytes (95.1 GiB)**. It is a gzip-compressed tar containing individually gzipped `.3dg.txt` files. For a limited run, the notebook streams the archive over HTTPS and stops after the requested models rather than downloading all 95.1 GiB. Selected inner files are cached in `data/members/`; existing downloads and outputs are skipped. If the full archive is placed at `data/GSE192759_5kb_10kb_20kb_3dg_files.tar.gz`, it is used instead.

Each model becomes `out/<member-name>.arrow` (with `.3dg.txt.gz` removed), written with `pyarrow.ipc.new_file`. Columns are `x`, `y`, `z` (`float64`), `chr` (`string`), and `coord` (`int64`, the published 0-based genomic bin start in bp). Coordinates are not rescaled.

## Run

```sh
uvx marimo edit --sandbox notebook.py
# or execute non-interactively:
uv run notebook.py
```

Start by setting `MAX_STRUCTURES = 2` near the top. The committed setting is `None` (all models). A full remote run transfers 95.1 GiB and needs substantial output storage; use a local archive for a full conversion whenever possible.

## Caveats

- Uncleaned files use names such as `chr1a`/`chr1b` and usually have `#chromosome` and `#unit` headers. The inspected `.clean` file instead uses `chr1(mat)`/`chr1(pat)`, has no headers, omits about 10.6% of the uncleaned model's bins, and uses a different coordinate scale. The notebook preserves both the original chromosome labels and all published rows, does not impute omitted bins, and retains `#unit`, chromosome lengths, and resolution as Arrow schema metadata when available.
- Keeping the haplotype label in `chr` prevents maternal and paternal homologs from collapsing onto the same genomic bins. There is no separate canonical-chromosome or haplotype column.
- Only the opening two 10 kb models (one uncleaned and one `.clean`) were exercised here. The 5 and 20 kb members use the advertised same format, but a reviewer running the full archive should watch for later format variations.
