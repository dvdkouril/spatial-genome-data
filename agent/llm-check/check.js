// Increment 1: does the LLM do tool calling?
// Talks to the OpenAI-compatible chat completions API directly, with plain fetch,
// and prints the raw JSON so you can see what an agent library does for you.
//
// Settings come from agent/llm-check/.env (git-ignored). Run:
//   node --env-file=agent/llm-check/.env agent/llm-check/check.js

const BASE_URL = process.env.LLM_BASE_URL; // your LLM API, ending in /v1
const MODEL = process.env.LLM_MODEL; // a model id from GET $LLM_BASE_URL/models
const API_KEY = process.env.LLM_API_KEY;

// The tool, described to the model as a JSON schema. The model never runs it;
// it can only ask us to.
const tools = [
  {
    type: "function",
    function: {
      name: "search_papers",
      description: "Search for scientific publications. Returns titles and DOIs.",
      parameters: {
        type: "object",
        properties: { query: { type: "string", description: "Search query" } },
        required: ["query"],
      },
    },
  },
];

const messages = [
  { role: "system", content: "You help find publications that contain 3D genome structure data." },
  { role: "user", content: "Find papers with 3D genome structures reconstructed from single-cell Hi-C." },
];

async function chat() {
  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${API_KEY}` },
    body: JSON.stringify({ model: MODEL, messages, tools }),
  });
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  const body = await response.json();
  return body.choices[0].message;
}

// Round 1: the model should answer with a tool call, not text.
const first = await chat();
console.log("=== Round 1: model's reply ===\n", JSON.stringify(first, null, 2));

const call = first.tool_calls?.[0];
if (!call) {
  console.log("\nNo tool call: the model answered with plain text.");
  process.exit(1);
}

// We "run" the tool: a fake result instead of a real search.
console.log(`\nModel asked for ${call.function.name} with arguments ${call.function.arguments}`);
const fakeResult =
  "- 3D structures of individual mammalian genomes studied by single-cell Hi-C (2017) doi:10.1038/nature21429\n" +
  "- Three-dimensional genome structures of single diploid human cells (2018) doi:10.1126/science.aat5641";

// Round 2: send the model its own tool call plus our result, and let it answer.
messages.push(first);
messages.push({ role: "tool", tool_call_id: call.id, content: fakeResult });
const second = await chat();
console.log("\n=== Round 2: model's reply ===\n", JSON.stringify(second, null, 2));
