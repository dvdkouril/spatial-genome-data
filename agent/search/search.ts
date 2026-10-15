// Stage 1 (Search): the agent loop with a real search tool (Europe PMC).
// Talks to the OpenAI-compatible chat completions API directly, with plain fetch,
// so you can see what an agent library does for you.
//
// Settings come from agent/search/.env (git-ignored). Run:
//   deno task search

import { searchPapers } from "./europepmc.ts";

// A required setting from the environment; stop early with a clear message if it's missing.
function setting(name: string): string {
  const value = Deno.env.get(name);
  if (!value) throw new Error(`Missing ${name}; set it in agent/search/.env`);
  return value;
}

const BASE_URL = setting("LLM_BASE_URL"); // your LLM API, ending in /v1
const MODEL = setting("LLM_MODEL"); // a model id from GET $LLM_BASE_URL/models
const API_KEY = setting("LLM_API_KEY");

// The parts of the chat completions API we use.
interface ToolCall {
  id: string;
  type: "function";
  function: { name: string; arguments: string }; // arguments is a JSON string
}

type Message =
  | { role: "system" | "user"; content: string }
  | { role: "assistant"; content: string | null; tool_calls?: ToolCall[] }
  | { role: "tool"; tool_call_id: string; content: string };

// The tool, described to the model as a JSON schema. The model never runs it;
// it can only ask us to.
const tools = [
  {
    type: "function",
    function: {
      name: "search_papers",
      description:
        "Search Europe PMC (PubMed, PubMed Central, and preprints such as bioRxiv). " +
        "Returns the 10 best matches with title, authors, year, journal, DOI, and abstract.",
      parameters: {
        type: "object",
        properties: {
          query: {
            type: "string",
            description:
              "Europe PMC query. Combine terms with AND / OR, and put phrases in double quotes. " +
              'Always quote hyphenated terms ("Hi-C", "Dip-C"), or they are split into separate words. ' +
              "Add AND SRC:PPR to search only preprints.",
          },
        },
        required: ["query"],
      },
    },
  },
];

const messages: Message[] = [
  { role: "system", content: "You help find publications that contain 3D genome structure data." },
  { role: "user", content: "Find papers with 3D genome structures reconstructed from single-cell Hi-C." },
];

async function chat(): Promise<Extract<Message, { role: "assistant" }>> {
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
// Arguments come from the model, so they are untyped until checked.
const toolImplementations: Record<string, (args: Record<string, unknown>) => Promise<string>> = {
  search_papers: ({ query }) => searchPapers(String(query)),
};

// Run one tool call. Problems are returned as text, so the model can see them and retry.
async function runTool(call: ToolCall): Promise<string> {
  const implementation = toolImplementations[call.function.name];
  if (!implementation) return `Error: there is no tool called ${call.function.name}.`;
  let args;
  try {
    args = JSON.parse(call.function.arguments);
  } catch {
    return `Error: the arguments are not valid JSON: ${call.function.arguments}`;
  }
  try {
    return await implementation(args);
  } catch (error) {
    return `Error: ${call.function.name} failed: ${(error as Error).message}`;
  }
}

// The agent loop: ask the model, run the tools it asks for, repeat until it answers with text.
const MAX_STEPS = 5;

for (let step = 1; step <= MAX_STEPS; step++) {
  const reply = await chat();
  messages.push(reply); // the model must see its own tool calls in the next round

  if (!reply.tool_calls?.length) {
    console.log(`\n=== Step ${step}: final answer ===\n${reply.content}`);
    Deno.exit(0);
  }

  // A single reply may contain several tool calls; each gets its own result.
  for (const call of reply.tool_calls) {
    console.log(`Step ${step}: ${call.function.name}(${call.function.arguments})`);
    messages.push({ role: "tool", tool_call_id: call.id, content: await runTool(call) });
  }
}

console.log(`\nStopped after ${MAX_STEPS} steps without a final answer.`);
Deno.exit(1);
