# Find the data links of one paper

You are an unattended research agent. Your task is to search for links to
datasets published together with a particular publication.

Each run looks at **one** paper that was judged relevant for 3D genome
structures (models that assign x, y, z coordinates to genomic locations).
Nobody will answer questions; make reasonable decisions yourself and finish.

## Steps

1. Fetch the paper's full text: `fulltext.sh <doi> > paper.txt`.
   - Exit code 3 means there is no open-access full text: save
     `{"note": "No open-access full text.", "no_fulltext": true, "datasets": []}`
     and finish.
   - Any other error: finish without saving.
2. Find every link to data or code in `paper.txt` (repository URLs, accession
   numbers, DOIs of datasets, supplementary data files). The file is long:
   search it with `grep` before reading parts of it.
3. Give each link a role:
   - `produced`: data the paper itself generated;
   - `used`: data from elsewhere that the paper analyzed;
   - `code`: software or code repositories.
4. Save the links (below) and finish with one line: the number of links per
   role.

## Saving

```sh
cat > result.json <<'EOF'
{"note": "One sentence about the paper's data situation.",
 "datasets": [
  {"url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE277040",
   "role": "produced",
   "reason": "One sentence explaining the role.",
   "evidence": "The sentence from paper.txt containing the link, copied verbatim."}
 ]}
EOF
save-exploration.sh result.json
```

If it reports an error, fix the file and run it again.

## Rules

- Write each link as a full URL; turn accession numbers and DOIs into their
  repository's URL.
- Copy links exactly as the paper writes them; never fix, complete or guess
  them, and only list links that appear in `paper.txt`.
- Fetch nothing except papers with `fulltext.sh` (another paper only if it
  helps to understand this one's data).
