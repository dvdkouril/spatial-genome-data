# Examples of spatial genome data

Gathering examples of 3D chromatin structures ("spatial genome" data) to be
visualized using [chromospace](https://github.com/dvdkouril/chromospace) and
[chromospyce](https://github.com/dvdkouril/chromospyce).

## Quickstart

Run the notebooks for data processing for any of the datasets in individual
subfolders, using [juv](https://github.com/manzt/juv). 

For example:
```sh
cd stevens-2017
juv run notebook.ipynb
```

## Why

One of the problems with visualization of 3D structures of chromatin is that
such data are very rarely published, and even when they are made available,
they often use sub-optimal data formats (such as text-based CSV, TSV, or even
PDB). The goal of this repository is to provide example structures for direct
consumption, primarily by the chromospace/chromospyce tool ecosystem.

We aim to keep track of the data sources, original publications, and processing
pipeline to go from the published data to the structures in Apache Arrow
format.

This repository starts with already existing 3D structures and essentially
"just" converts them from their original file formats (pdb, txt, xyz, tsv,
etc.) to a unified Apache Arrow format. This means that the repo does not
include code to run any of the software that actually creates those structures
(i.e., running simulations on Hi-C matrix data).

## Available Data

### Full-genome models

- Stevens et al. 2017: "3D structures of individual mammalian genomes studied
by single-cell Hi-C"
([https://doi.org/10.1038/nature21429](https://doi.org/10.1038/nature21429))
- Tan et al. 2018: "Three-dimensional genome structures of single diploid human cells" ([https://doi.org/10.1126/science.aat5641](https://doi.org/10.1126/science.aat5641))

### "Chunks"

- Sun et al. 2021: High-resolution single-cell 3D-models of chromatin ensembles
during Drosophila embryogenesis
([https://doi.org/10.1038/s41467-020-20490-9](https://doi.org/10.1038/s41467-020-20490-9))
