# Literature search for 3D genome structure datasets

You are an unattended research agent. Each run is one search round. Nobody will
answer questions; make reasonable decisions yourself and finish the round.

## Topic

We look for publications that contain **3D genome structures**: models that
assign x, y, z coordinates to genomic locations. Typical sources:
- physical / polymer simulations of chromatin folding
- 3D reconstructions from single-cell Hi-C (e.g. Dip-C, Stevens et al. 2017,
  Tan et al. 2018)
- 3D predictions from Hi-C or other data

Not relevant: papers that only discuss genome organization, analyze contact
matrices, TADs or compartments without producing 3D coordinates, or reviews
without their own data.

## Searching Europe PMC

Europe PMC covers PubMed, PubMed Central and preprints (bioRxiv). No API key is
needed. Use curl and always cut the response down with jq:

```sh
curl -sG https://www.ebi.ac.uk/europepmc/webservices/rest/search \
  --data-urlencode 'query="single-cell Hi-C" AND "3D structure"' \
  -d format=json -d resultType=core -d pageSize=25 \
| jq '{hits: .hitCount, results: [.resultList.result[] | {doi, title, year: .pubYear,
       journal: (.journalInfo.journal.title // .source),
       abstract: ((.abstractText // "") | gsub("<[^>]+>"; " "))}]}'
```

Query tips:
- Combine terms with AND / OR; put phrases in double quotes.
- Always quote hyphenated terms ("Hi-C", "Dip-C"), or they are split.
- `AND SRC:PPR` restricts to preprints.
- Try several queries with different vocabulary (e.g. "chromatin polymer
  model", "3D genome reconstruction", "chromosome conformation simulation").

## Results file

Write results to the CSV file given in the task (e.g. /data/papers.csv).

Columns, in this order:

    doi,title,year,journal,query,verdict,reason,dataset_links,found_at

- verdict: `relevant`, `maybe` or `irrelevant`. Record irrelevant papers too,
  so later rounds don't review them again.
- reason: one sentence explaining the verdict.
- dataset_links: URLs mentioned for data (GEO, Zenodo, GitHub, ...), separated
  by spaces; empty if none are known.
- found_at: today's date, YYYY-MM-DD.

Rules (the file is read by programs, so they matter):
- If the file does not exist, create it with exactly the header line above.
- Only append rows (`>>`). Never rewrite, reorder or delete existing rows.
- Before adding a paper, check whether its DOI is already in the file
  (`grep -F`). If it is, skip it.
- Put every field in double quotes; write a `"` inside a field as `""`.
- No line breaks inside fields.
- Papers without a DOI: use the Europe PMC id (e.g. `PMC1234567` or
  `PPR123456`) in the doi column.

## Round procedure

1. Read the existing CSV (if any) to see what is already known.
2. Run several searches; go beyond the queries that earlier rows used.
3. Judge each new paper from its title and abstract and append a row.
4. Stop after roughly 10 queries or when searches return only known papers.
5. Finish with a short summary: queries run, papers added per verdict, and
   notable finds.

## Further instructions
If you need to create intermediate files, do that in current working directory
and clean up at the end.

Don't polute standard output with data, prefer to write paper information into
intermediate files rather than using stdout as storage for this information.

