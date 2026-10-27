# Find the data links of one paper

You are an unattended research agent. Your task is to search for links to
datasets published together with a particular publication.

Each run looks at **one** paper that was judged relevant for 3D genome
structures (models that assign x, y, z coordinates to genomic locations).
Nobody will answer questions; make reasonable decisions yourself and finish.

## Task

The paper's full text is in the file `paper.txt` in the current directory,
converted from the publisher's XML to plain text: section titles are lines
starting with `#`, each paragraph, table row and reference is one line, link
targets are written in `<...>` next to their link text, and supplementary
files are lines starting with `Supplementary file:` with their full URL.

Find every link to data or code in it, and decide for each one its **role**:

- `produced`: data this paper itself generated and deposited ("we deposited",
  "generated in this study", "are available at" for the paper's own results,
  supplementary data files with the paper's results).
- `used`: data from elsewhere that the paper analyzed ("downloaded from",
  "obtained from", "previously published", "public data from").
- `code`: software or code repositories (including Zenodo archives of code),
  whether the paper's own or third-party tools.

You only find and label links. Do not judge what a dataset contains, and do not
visit any link.

Papers are long, so search before you read. For example:
- `grep -n '^#' paper.txt` for the outline;
- `grep -n -i -A3 'availab' paper.txt` for data and code availability
  statements;
- `grep -n -i -E 'GSE[0-9]|PRJ|zenodo|figshare|github|accession|deposited' paper.txt`
  for links elsewhere (methods, tables, references);
- `grep -n '^Supplementary file:' paper.txt` for supplementary files.
Then read the relevant sections whole (e.g. with `sed -n '120,140p' paper.txt`)
to decide the roles. Read more of the paper whenever the context is unclear.

What counts as a link:
- URLs to repositories and archives (GEO, SRA/BioProject, ArrayExpress, ENA,
  GSA, 4DN, ENCODE, Zenodo, figshare, Dryad, OSF, Mendeley Data, GitHub,
  GitLab, lab or project websites with data).
- Accession numbers and DOIs, even without a URL.
- Supplementary files that hold data (e.g. "Supplementary Data 1", tables,
  archives, model files). Skip the supplementary information PDF, peer review
  file, reporting summary and similar documents.
- Not: tools' documentation pages, general websites (e.g. a viewer's
  homepage), or references to other papers.

## Writing links

Write every link as a full URL:
- a URL from the text: copy it exactly as written.
- a GEO accession (GSE…, GSM…): `https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=<accession>`
- a BioProject (PRJNA…): `https://www.ncbi.nlm.nih.gov/bioproject/<accession>`
- an SRA accession (SRP…, SRR…, SRX…): `https://www.ncbi.nlm.nih.gov/sra/<accession>`
- an ArrayExpress accession (E-MTAB-…): `https://www.ebi.ac.uk/biostudies/arrayexpress/studies/<accession>`
- a GSA accession (CRA…): `https://ngdc.cncb.ac.cn/gsa/browse/<accession>`
- a 4DN accession (4DN…): `https://data.4dnucleome.org/<accession>`
- an ENCODE accession (ENC…): `https://www.encodeproject.org/<accession>`
- a DOI (Zenodo, figshare, Dryad, …): `https://doi.org/<doi>`
- a supplementary file: the URL on its `Supplementary file:` line.

Never fix, complete or guess an accession or URL, even if it looks like a typo:
record it as the paper writes it. Only list links that appear in
`paper.txt`; do not add ones you know from elsewhere.

## Saving

Write a JSON object to a file and pass it to `save-exploration.sh` (it is on
your PATH):

```sh
cat > result.json <<'EOF'
{"note": "Single-cell 3D structures deposited in GEO as mmCIF files.",
 "datasets": [
  {"url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE277040",
   "role": "produced",
   "reason": "Deposited by the authors as data generated in this study.",
   "evidence": "The single-cell Hi-C and GAM data generated in this study have been deposited in Gene Expression Omnibus (GEO) under accession code GSE277040"},
  {"url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE63525",
   "role": "used",
   "reason": "Public Hi-C data the paper downloaded.",
   "evidence": "GM12878 in situ Hi-C data were downloaded from GSE63525"}
 ]}
EOF
save-exploration.sh result.json
```

- note: one sentence about the paper's data situation, e.g. where its own data
  is, or "data available on request only", or "no data links in the text".
- datasets: one entry per link; an empty array if the paper has none.
- reason: one sentence explaining the role.
- evidence: the sentence (or the part of it) from `paper.txt` that contains
  the link, **copied verbatim**. The link's URL or accession must appear in it.
  For a supplementary file, copy its `Supplementary file:` line.

If `save-exploration.sh` reports an error, fix the entries and run it again.

## Scope

- Read `paper.txt` with any shell commands you like, and save with
  `save-exploration.sh`. Do not fetch anything (no curl, no web pages), even
  if the text seems incomplete; mention gaps in the note instead.
- Create result.json in the current working directory.
- Finish with one line: the number of links per role.
