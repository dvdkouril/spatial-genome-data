// Increment 2, step 1: the agent loop, still with one fake tool.
// Talks to the OpenAI-compatible chat completions API directly, with plain fetch,
// so you can see what an agent library does for you.
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

// The code behind each tool, looked up by the name the model asks for.
// Still fake: every search returns the same two papers.
const toolImplementations = {
  search_papers: ({ query }) =>
    `Results for "${query}":\n` +
    "- 3D structures of individual mammalian genomes studied by single-cell Hi-C (2017) doi:10.1038/nature21429\n" +
    "- Three-dimensional genome structures of single diploid human cells (2018) doi:10.1126/science.aat5641",
};

// Run one tool call. Problems are returned as text, so the model can see them and retry.
function runTool(call) {
  const implementation = toolImplementations[call.function.name];
  if (!implementation) return `Error: there is no tool called ${call.function.name}.`;
  let args;
  try {
    args = JSON.parse(call.function.arguments);
  } catch {
    return `Error: the arguments are not valid JSON: ${call.function.arguments}`;
  }
  return implementation(args);
}

// The agent loop: ask the model, run the tools it asks for, repeat until it answers with text.
const MAX_STEPS = 5;

for (let step = 1; step <= MAX_STEPS; step++) {
  const reply = await chat();
  messages.push(reply); // the model must see its own tool calls in the next round

  if (!reply.tool_calls?.length) {
    console.log(`\n=== Step ${step}: final answer ===\n${reply.content}`);
    process.exit(0);
  }

  // A single reply may contain several tool calls; each gets its own result.
  for (const call of reply.tool_calls) {
    console.log(`Step ${step}: ${call.function.name}(${call.function.arguments})`);
    messages.push({ role: "tool", tool_call_id: call.id, content: runTool(call) });
  }
}

console.log(`\nStopped after ${MAX_STEPS} steps without a final answer.`);
process.exit(1);
