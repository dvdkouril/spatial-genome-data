# Examples of spatial genome data

Gathering examples of 3D chromatin structures ("spatial genome" data) to be
visualized using [chromospace](https://github.com/dvdkouril/chromospace) and
[chromospyce](https://github.com/dvdkouril/chromospyce).

## Quickstart

Run the notebooks for data processing for any of the datasets in individual subfolders, using [juv](https://github.com/manzt/juv). For example:
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

## Available Data

Stevens et al. 2017: "3D structures of individual mammalian genomes studied by single-cell Hi-C"
- [https://doi.org/10.1038/nature21429](https://doi.org/10.1038/nature21429)
- GEO: [GSE80280](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE80280)
- Organism: Mus musculus
