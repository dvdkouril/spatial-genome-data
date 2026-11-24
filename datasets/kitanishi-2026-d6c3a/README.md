# Kitanishi et al. single-cell RPR genome models

**Paper:** Yuki Kitanishi, Hiroki Sugishita, Yukiko Gotoh, and Yoshito Hirata, “Recurrence plot reconstruction reveals chromosomal reorganization before territory formation,” *NAR Genomics and Bioinformatics* 8(1), lqag023 (2026). DOI: [10.1093/nargab/lqag023](https://doi.org/10.1093/nargab/lqag023).

**Dataset:** <https://doi.org/10.5281/zenodo.18498172> (v1.0.0).

## Data

Mouse (*Mus musculus*) whole-genome, single-cell 3D models reconstructed from scHi-C with recurrence plot reconstruction (RPR). The paper specifies **mm10** and **1 Mb bins**.

- 632 F1-hybrid embryo models: 75 1-cell, 109 2-cell, 121 4-cell, 126 8-cell, and 201 64-cell. The paper reports 125 8-cell models; this conversion retains the additional archived `8cell/cell8_126.csv`.
- 15 female postnatal-day-0 cortical neuron models.
- Each CSV is one cell and includes homolog/haplotype copies 0 and 1, chromosome, 1 Mb-bin midpoint, and XYZ. Female cells have two X copies; males have one X and one Y.

The notebook downloads one **39,400,388-byte (39.4 MB) ZIP** into `data/`. This includes the 35.9 MB embryo tarball, 2.8 MB neuron tarball, MATLAB/Python analysis code, and a notebook. The coordinate tarballs are read directly inside the ZIP; three `.ipynb_checkpoints` CSV duplicates are skipped. Existing downloads are verified by size and MD5.

## Output

Running with `MAX_STRUCTURES = None` writes **647 Arrow IPC files** to `out/`, one per primary CSV, totaling about **167 MB**. Names include sample kind, developmental stage for embryos, and source model ID.

Each file contains:

- `x`, `y`, `z` (float64): source coordinates, unchanged;
- `chr` (string): `chr1`–`chr19`, `chrX`, or `chrY`;
- `coord` (int64): genomic **bin start** in bp, calculated as source midpoint minus 500,000;
- `copy_index` (int64): source homolog/haplotype index, retained so the two copies can be separated.

Model ID, sample kind, stage, sex, source member, mm10 assembly, resolution, and coordinate notes are stored in Arrow schema metadata. The 632 embryo files have 5,180–5,282 valid beads each; neuron files each have 5,282. The complete conversion has 3,393,935 beads. Embryo CSVs contain **136,409 trailing all-zero allocation rows**, which are removed; no neuron padding is present.

## Run

```sh
uvx marimo edit --sandbox notebook.py
# or perform the full conversion:
uv run notebook.py
```

Set `MAX_STRUCTURES` near the top to a small integer for a trial, or `None` for all structures. Downloads and outputs are located relative to `notebook.py`, not the shell's current directory.

## Caveats

- RPR coordinates describe relative spatial organization. The paper explicitly gives no absolute physical scale; the notebook does not normalize, recenter, or rescale XYZ.
- `copy_index` is preserved rather than relabeled. Consumers should use it to distinguish homologs that otherwise share `chr` and `coord` values.
- `8cell/cell8_126.csv` has no sex directory. Its sex is inferred as male from its single-X/Y-copy layout and marked as inferred in metadata.
- Some archive embryo models have fewer than the full complement of bins. No missing genomic bins are imputed.
