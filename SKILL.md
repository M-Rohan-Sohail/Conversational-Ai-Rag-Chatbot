---
name: langfuse-implementation
description: Implement Langfuse observability (tracing) in an LLM application's code. Use when adding Langfuse to a project, instrumenting LLM calls, setting up traces/spans/generations, attaching user_id/session_id/tags/scores, or auditing existing Langfuse instrumentation. Covers Python SDK v4 and JS/TS SDK v5, framework integrations (OpenAI, LangChain, LlamaIndex, Vercel AI SDK, LiteLLM), and common mistakes.
---

# Implementing Langfuse in Code

This skill guides you through adding Langfuse tracing to an LLM application correctly and to current standards.

## Core Principles

1. **Docs first, never from memory.** Langfuse changes often. Before writing any integration code, fetch the current docs for the exact framework being used. Use your native web-fetch tool; the URLs below all serve clean markdown when you append `.md`.
2. **Prefer framework integrations over manual instrumentation.** Integrations auto-capture model name, token usage, and observation type with far less code.
3. **Use the latest SDK** unless the user pins a version: Python SDK **v4**, JS/TS SDK **v5**.

## Documentation Access

```bash
# Full index of every doc page (titles + URLs)
curl -s https://langfuse.com/llms.txt

# Any page as markdown — just append .md
curl -s "https://langfuse.com/docs/observability/overview.md"

# Search docs + GitHub issues/discussions when you don't know the page
curl -s "https://langfuse.com/api/search-docs?query=trace+LangGraph+agents"
```

Workflow: scan `llms.txt` → fetch the specific page → fall back to search when unclear.

## Implementation Workflow

### Step 1 — Assess the codebase

Determine before writing anything:
- Is the Langfuse SDK already installed? Any existing instrumentation?
- Which LLM framework is used? (OpenAI SDK, LangChain, LlamaIndex, Vercel AI SDK, LiteLLM, raw HTTP)
- Is this a script, a long-running server, or a serverless function? (Affects flushing.)

If integration exists, audit it against the baseline table in Step 3 instead of rebuilding.

### Step 2 — Install and configure credentials

Set these as environment variables (a `.env` file or shell), never hardcoded:

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com   # EU cloud; US = https://us.cloud.langfuse.com; or self-hosted URL
```

Keys come from the Langfuse UI → Settings → API Keys. **Do not ask the user to paste keys into chat.** If they're missing, ask the user to put them in their `.env` or shell.

Install:
```bash
pip install langfuse        # Python (v4)
npm install langfuse        # JS/TS (v5)
```

### Step 3 — Verify baseline requirements

Every trace should satisfy these. Framework integrations handle the first three automatically.

| Requirement | Check |
| --- | --- |
| Model name captured | Enables model comparison/filtering |
| Token usage captured | Enables automatic cost calculation |
| Correct observation types | LLM calls marked as generations |
| Descriptive trace names | `chat-response`, not `trace-1` |
| Proper span hierarchy | Multi-step ops nested so you can see which step is slow/failing |
| Sensitive data masked | PII/secrets excluded or masked |
| Meaningful, scoped input/output | Set input explicitly to the relevant data (e.g. the user message), not all function args |

### Step 4 — Pick the integration

Prefer these drop-in integrations; fetch the linked doc as `.md` before coding:

| Framework | Integration | Docs |
| --- | --- | --- |
| OpenAI SDK | Drop-in replacement import | https://langfuse.com/docs/integrations/openai |
| LangChain | Callback handler | https://langfuse.com/docs/integrations/langchain |
| LlamaIndex | Callback handler | https://langfuse.com/docs/integrations/llama-index |
| Vercel AI SDK | OpenTelemetry exporter | https://langfuse.com/docs/integrations/vercel-ai-sdk |
| LiteLLM | Callback or proxy | https://langfuse.com/docs/integrations/litellm |

Full list: https://langfuse.com/docs/integrations

For custom code with no integration, instrument manually with the decorator/wrapper (below).

### Step 5 — Add context that fits the app

Infer from the code; only ask the user when it's not obvious.

| If the code shows... | Add | Docs |
| --- | --- | --- |
| Chat history / message arrays / multi-turn | `session_id` | /docs/tracing-features/sessions |
| Auth / `user_id` variables | `user_id` on traces | /docs/tracing-features/users |
| Multiple distinct features/endpoints | `feature` tag | /docs/tracing-features/tags |
| Customer/tenant identifiers or tiers | `customer_id` / tier tag | /docs/tracing-features/tags |
| Ratings / thumbs / feedback | Capture as **scores** | /docs/scores/overview |

These are optional enhancements, not baseline. Always explain the benefit when suggesting one.

### Step 6 — Verify

Run the app, confirm traces appear in the Langfuse UI (Traces view; Sessions view if `session_id` was added), and tell the user to inspect a few traces to decide what else is worth capturing.

## Manual Instrumentation (current SDK syntax)

**Python (v4)** — decorator approach; set input explicitly to avoid leaking all args:

```python
from langfuse import observe, get_client

langfuse = get_client()

@observe()
def handle_request(user_message: str, api_key: str):
    # Only the relevant input, not every arg:
    langfuse.update_current_span(input={"user_message": user_message})
    ...
    langfuse.update_current_span(output=result)
    return result
```

Nest a generation/observation explicitly:
```python
with langfuse.start_as_current_observation(name="llm-call", as_type="generation") as gen:
    ...
```

Correlating attributes use `propagate_attributes()` (replaces the old `update_current_trace()`):
```python
with langfuse.propagate_attributes(user_id="u-123", session_id="s-456", tags=["chat"]):
    handle_request(...)
```

**JS/TS (v5)** — set scoped I/O on the active observation:
```ts
import { updateActiveObservation, propagateAttributes } from "langfuse";

updateActiveObservation({ input: { userMessage } });
// ...
updateActiveObservation({ output: result });
```

## Flushing (critical)

- **Scripts / serverless / short-lived processes:** call `langfuse.flush()` (Python) / `await langfuse.flushAsync()` (JS/TS) before exit, or traces are silently lost.
- Long-running servers flush in the background; still flush on graceful shutdown.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| No flush in scripts → traces never sent | Call `flush()` before exit |
| Flat traces → can't see which step failed | Nest distinct steps as spans |
| Generic trace names | Use descriptive names (`chat-response`) |
| Logging PII/secrets | Mask before tracing |
| Not setting input with `@observe` → all args (keys, configs) captured | Set input explicitly to the relevant field only |
| Manual instrumentation when an integration exists | Use the framework integration |
| Importing Langfuse before env vars are loaded | Import/initialize Langfuse **after** `load_dotenv()` |
| Importing Langfuse after the OpenAI client | Import and set up Langfuse **before** the OpenAI client so it can patch it |

## SDK Version Notes (v4 Python / v5 JS-TS)

If you encounter an older codebase, key changes to apply:
- Non-LLM spans (HTTP/DB/queue) no longer export by default — add a `should_export_span` / `shouldExportSpan` filter if needed.
- `update_current_trace()` / `updateActiveTrace()` is split into `propagate_attributes()` (for `user_id`/`session_id`/`tags`/`metadata`/`trace_name`) + setting I/O on the root observation + a public-flag call.
- Python: `start_span()`/`start_generation()` → `start_observation(as_type=...)`; `start_as_current_*` → `start_as_current_observation()`.
- `release`/`environment` move from code params to env vars (`LANGFUSE_RELEASE`, `LANGFUSE_TRACING_ENVIRONMENT`).
- Metadata must be string-valued, values ≤200 chars.

Migration guides (fetch before upgrading):
- https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4.md
- https://langfuse.com/docs/observability/sdk/upgrade-path/js-v4-to-v5.md
