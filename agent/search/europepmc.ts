// search_papers backed by Europe PMC (PubMed, PubMed Central, and preprints like bioRxiv).
// No API key needed. Docs: https://europepmc.org/RestfulWebService
//
// Try it on its own, without the LLM:
//   deno task europepmc '"single-cell Hi-C" AND "3D structure"'

const SEARCH_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search";
const PAGE_SIZE = 10;

// The fields of a Europe PMC result that we use (the API returns many more).
interface Paper {
  title: string;
  authorString?: string;
  pubYear: string;
  source: string; // "MED" for PubMed, "PPR" for preprints, ...
  doi?: string;
  isOpenAccess: "Y" | "N";
  abstractText?: string;
  journalInfo?: { journal?: { title?: string } };
}

interface SearchResponse {
  hitCount: number;
  resultList: { result: Paper[] };
}

// Abstracts come with HTML section headings (<h4>Background</h4>...); the model only needs the text.
function stripHtml(html: string): string {
  return html
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

// One paper as a compact text block: only the fields the model needs to judge relevance.
function formatPaper(paper: Paper, index: number): string {
  const journal = paper.journalInfo?.journal?.title ?? (paper.source === "PPR" ? "preprint" : "unknown journal");
  const lines = [
    `${index + 1}. ${paper.title}`,
    `   ${paper.authorString ?? "unknown authors"} (${paper.pubYear}), ${journal}`,
    `   DOI: ${paper.doi ?? "none"} | open access: ${paper.isOpenAccess === "Y" ? "yes" : "no"}`,
    `   Abstract: ${paper.abstractText ? stripHtml(paper.abstractText) : "not available"}`,
  ];
  return lines.join("\n");
}

// Run a search and return the results as text, ready to hand to the model as a tool result.
export async function searchPapers(query: string): Promise<string> {
  const params = new URLSearchParams({ query, format: "json", resultType: "core", pageSize: String(PAGE_SIZE) });
  const response = await fetch(`${SEARCH_URL}?${params}`);
  if (!response.ok) throw new Error(`Europe PMC ${response.status}: ${await response.text()}`);
  const body: SearchResponse = await response.json();

  const papers = body.resultList.result;
  if (papers.length === 0) return `No papers found for: ${query}`;
  const header = `${body.hitCount} papers match "${query}"; showing the first ${papers.length}.`;
  return [header, ...papers.map(formatPaper)].join("\n\n");
}

// Run directly (not imported): search for the query given on the command line.
if (import.meta.main) {
  const query = Deno.args[0];
  if (!query) {
    console.error("Usage: deno run --allow-net europepmc.ts '<query>'");
    Deno.exit(1);
  }
  console.log(await searchPapers(query));
}
