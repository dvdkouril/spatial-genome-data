# Technical details regarding the agentic architecture
*This file is mostly LLM-generated.*

## How it runs

- **Agent program.** A TypeScript program using
  [pi-durable](https://github.com/earendil-works/pi/tree/main/packages/durable).
  It has a fixed system prompt and task prompt, and a small set of tools. The
  prompt lives in the code; changing it means redeploying.
- **One round per run.** Each run submits the task, lets the agent loop (model →
  tool → model …) until the model is done, saves results, and exits. Each
  round starts a fresh conversation; `save_paper` deduplicates, so the model
  needs no memory of earlier rounds.
- **CronJob.** Kubernetes starts a round on a schedule.
  `concurrencyPolicy: Forbid` ensures only one round runs at a time.
- **Crash recovery.** If the pod dies mid-round, the Job starts a new one. It
  opens the same `agent.sqlite`, and `harness.resume()` continues from the last
  checkpoint. Each round is submitted with a fixed `requestId` (e.g.
  `round-2026-10-12`), so a restart doesn't start a second round.
- **PersistentVolume.** Holds the durable state and the results across runs.
  `agent.sqlite` also records every search and decision, which is useful for
  tuning the prompt.
- **LLM.** An OpenAI-compatible inference API, reached over HTTP and configured
  as a custom pi-ai provider (base URL, model id, API key).
- **Image build.** GitHub Actions builds the image and pushes it to Harbor
  using a Harbor robot account. Deploying is a manual `kubectl apply`.

## Constraints

- **pi-durable: one process per storage.** There is no cross-process locking.
  Never run two pods on the same `agent.sqlite`.
- **pi-durable is experimental.** Pin exact package versions. The README on
  GitHub `main` can be ahead of the npm release, so check the installed types.
- **CERIT pod requirements.** Pods are rejected without:
  - pod `securityContext`: `runAsNonRoot: true`,
    `seccompProfile: {type: RuntimeDefault}` (plus `runAsUser: 1000` for
    images that default to root, like `node`)
  - container `securityContext`: `allowPrivilegeEscalation: false`,
    `capabilities: {drop: ["ALL"]}`
  - resource requests/limits (CERIT fills in 1 CPU / 512 MB if missing)
- **No secrets in images.** All Harbor images can be pulled by anyone who
  knows the name. API keys go in a Kubernetes Secret.
- **Image architecture.** Build for `linux/amd64` (`docker build --platform
  linux/amd64`); Apple Silicon builds arm64 by default.
- **The LLM must support tool calling.** Everything depends on it.
