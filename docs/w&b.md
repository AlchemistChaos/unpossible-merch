# Using Weights & Biases Weave for LLM & Agent Observability in a Hackathon

## Executive summary

Weights & Biases (W&B) Weave is W&B’s LLM- and agent-focused tracing, evaluation, and observability layer, designed to give visibility into every LLM call, prompt, and output, as well as systematic evaluation and feedback collection. For an agentic hackathon project, Weave is a better fit than classic `wandb` experiment tracking, which is optimized for logging training runs, metrics, and artifacts rather than fine-grained traces of live LLM applications.[1][2][3][4][5]

Weave can automatically trace calls from common LLM providers and frameworks (OpenAI, Anthropic, Cohere, Mistral, LangChain), capture prompts and responses, and build a tree of nested operations and tools; additional metadata, feedback, and business events can be attached via decorators, context managers, or OpenTelemetry (OTEL) integration. For a same‑day hackathon, the fastest high‑value path is:[6][7][8][9][10][11]

- Initialize Weave once with `weave.init("team/project")`.
- Let Weave’s automatic LLM and LangChain/OpenAI Agents integrations trace most calls.
- Decorate a small number of key functions (top‑level request handler, each agent, important tools) with `@weave.op()` and/or the OpenAI Agents Weave tracing processor so the trace tree clearly shows agent handoffs and tool usage.[12][8][9]
- Use a minimal set of custom attributes (session id, user id, business event name, cost budget) via `weave.attributes` or OTEL span attributes.[7][9]

This yields a compelling live demo in the Weave UI: judges can see an end‑to‑end trace per user request, expand nodes to inspect prompts and outputs, visualize nested multi‑agent flows, and reason about latency and cost. Classic `wandb` runs remain optional for logging aggregate metrics but are not necessary for the core observability story.[13][14][5]

## Recommended use case definition

For this hackathon, the target use case for Weave is:

> **End‑to‑end observability for a multi‑agent, tool‑using LLM application**, focused on per‑request traces rather than model training.

Concretely, the system should:

- Treat each end‑user interaction (e.g., “design and publish a landing page”) as a **single trace/session** containing all underlying LLM calls, agent steps, and tools.[8][15]
- Support **multi‑agent flows** (e.g., planner → researcher → writer → publisher), where each agent’s logic appears as a child call under the parent trace.[9][12]
- Log **LLM prompts, responses, model parameters, token usage, latency, and cost** for every important call.[16][15][5][1][13]
- Capture **tool calls** (e.g., web search, browser automation, “publish page”) and associate them with the agent step that requested them.[17][12][9]
- Record **business events** and **feedback/evaluation scores** (e.g., “user accepted design = true”, “judge rating = 4/5”) as attributes or evaluation results on the same trace.[5][1][16]

This scope is narrow enough to implement in a day but rich enough to show real observability value.

## W&B product choice: Weave vs classic wandb

### Classic wandb experiment tracking

Classic `wandb` focuses on **runs**, **metrics**, **hyperparameters**, **artifacts**, and **sweeps** for training and offline experimentation.[18][2][19][3]

- A **run** represents a single unit of computation such as a training job; users log metrics over time and attach artifacts like datasets and model checkpoints.[2][3][18]
- Artifacts provide data and model versioning; sweeps orchestrate hyperparameter search.[19][18]

This is ideal for model training and offline evaluation but not optimized for high‑cardinality, per‑request traces or deep inspection of nested LLM/agent calls.

### Weave: LLM and agent observability

Weave is described by W&B as a toolkit specifically for LLM applications providing:

- **Visibility** into every LLM call, input, and output in an application.
- **Systematic evaluation**, **version tracking of prompts/models/data**, **experimentation**, **feedback collection**, and **monitoring with guardrails and scorers**.[4][1][16][5]
- **Tracing and monitoring** of LLM calls and application logic, with a central trace database and UI for debugging and analysis.[20][8][4][5]

Key contrasts for this hackathon:

| Aspect | Classic wandb (runs) | Weave (traces, prompts, evals) |
| --- | --- | --- |
| Primary unit | Run (training job) | Trace / call graph for LLM app execution |
| Best for | Training metrics, dataset/model versioning, sweeps | LLM app observability, prompts, tool calls, evaluations |
| Data model | Time‑series metrics + artifacts per run | Trees of calls with inputs/outputs, prompts, metadata, usage, and scores |
| Built‑in UI | Metrics charts, run comparisons, sweeps dashboards | Trace tree, chat transcripts, cost/latency summaries, comparison of traces and evaluations[13][14][5] |

For an agentic app demo, **Weave is the correct product**; classic wandb runs are optional icing if there is time to log aggregate metrics.

## Capability matrix

The table below summarizes what Weave can capture and how, based on official docs and examples.

### High‑level capabilities

Weave’s core features include:

- Automatic **visibility into LLM calls, inputs, and outputs**.[21][1][6][8]
- Storage and management of **prompts** via `StringPrompt` and `MessagesPrompt` objects.[11]
- **Tracing** of application logic and nested calls via `@weave.op` and framework integrations.[22][8][9][20]
- **Evaluation** with scorers, judges, datasets, and detailed trace‑linked results.[16]
- **Usage and cost tracking** for LLM API calls.[15][13][16]
- **OpenTelemetry ingestion** for arbitrary spans from agent frameworks like Google ADK.[10][7][17]

### Detailed capability table

| Capability | Supported directly by Weave | Via official integrations | Via custom instrumentation |
| --- | --- | --- | --- |
| **Prompts (single string)** | `weave.StringPrompt` can log and publish standalone string prompts; these appear in the Prompts page.[11] | LangChain integration logs prompt templates used in chains.[9] | For arbitrary prompts, add them as inputs/attributes on OTEL spans or `weave.op` calls.[7][15] |
| **Multi‑turn prompts / conversations** | `weave.MessagesPrompt` stores arrays of chat messages representing full conversations.[11] | LangChain chat chains and agents traced by Weave include prompts and intermediate messages.[9] | OTEL traces can include serialized message lists as span attributes (e.g., `input.value`).[7][10] |
| **Model responses** | Automatic tracing of supported LLM libraries captures outputs; Weave’s service API shows `output.choices` structure that builds chat UI.[8][15] | OpenAI integration and monitoring example logs API responses and derives dashboards for usage and outputs.[13] | For other services, store responses in span attributes or as outputs in manual Weave calls.[7][15] |
| **Nested calls / call tree** | `@weave.op()` decorated functions create Calls, and nested invocations become a tree of child calls visible in the trace.[8][22][20] | LangChain integration automatically traces chains, tools, and agent steps as nested nodes.[9] OpenAI Agents WeaveTracingProcessor collects agent execution traces.[12] | OTEL spans support parent/child relationships; sending them to Weave preserves nested structure in the trace UI.[7][10][17] |
| **Tools / functions** | Any Python function wrapped in `@weave.op()` is a first‑class call that appears in the trace tree, effectively making tools visible.[8][22][23] | LangChain Weave integration tracks tools used by agents and chains.[9] OpenAI Agents integration traces `function_tool` calls and tool outputs.[12] Google ADK routes FunctionTool calls through OTEL spans to Weave.[17] | For custom tool stacks (e.g., Playwright browser), wrap tool invocations in `@weave.op()` or OTEL spans with descriptive names and attributes.[7][17] |
| **Agent steps / planning** | When each agent step is implemented as a `@weave.op` or logical function, those steps appear as sequential or nested calls.[8][22][20] | LangChain Weave docs explicitly state it tracks agent steps.[9] OpenAI Agents SDK + WeaveTracingProcessor captures agent executions and tool calls.[12] Google ADK example shows multi‑step agent workflows traced via OTEL to Weave.[17] | For custom agents, define explicit spans per step using OTEL or `@weave.op` wrappers and a shared trace context.[7][17] |
| **Metadata (tags, business attributes)** | `weave.attributes` context manager lets you attach arbitrary metadata (e.g., `{"my_awesome_attribute": "value"}`) to a traced LangChain call.[9] Weave objects and calls also support attributes in the service API.[15][20] | LangChain + Weave uses `weave.attributes` to record per‑request metadata; OpenAI monitoring dashboards group by attributes like model name and project id.[9][13] | OTEL exporters to Weave allow arbitrary span attributes (e.g., `gen_ai.system`, `input.value`, `output.value`, business IDs).[7][10][17] |
| **Latency / timing** | Service API requires `started_at` and `ended_at` timestamps for calls, and the Weave UI summarizes duration per call and trace.[15][8] | OpenAI monitoring example shows dashboards for latency and throughput built on logged call data.[13] | When using OTEL, span start/end times and attributes flow into Weave, enabling latency analysis without extra work.[7][10] |
| **Token usage and cost estimates** | The Weave evaluation docs describe cost tracking and token usage across evaluations; service API’s `summary.usage` structure includes model‑specific token counts.[16][15] | OpenAI monitoring with Weave generates dashboards aggregating cost and usage (tokens and spend) across projects.[13] | For providers without native usage, you can estimate tokens client‑side and log them as attributes or `summary.usage` in custom Weave calls (this is an inference based on the API examples).[15] |
| **Errors / exceptions** | Weave’s tracing and monitoring are described as helping debug errors and safety issues; while docs do not enumerate error fields, failed calls in `@weave.op` are recorded as calls with status (inferred from typical tracing semantics and examples).[24][5] | OTEL spans have standard status fields; when ingested into Weave, they can represent failures and error messages.[7][10] | For more context, you can log error messages and stack snippets as attributes on failed spans or calls (inference, based on OTEL and trace API capabilities).[7][15] |
| **Feedback / scores / evaluations** | Weave provides evaluation primitives (scorers, judges, evaluation datasets) and links scores to traced calls, including cost tracking.[16] Weave’s “main threads” mention feedback collection as a first‑class capability.[1] | Evaluations can use LLM judges to score outputs (e.g., relevance, correctness) and attach these to traces, with UI for comparison and analysis.[16][14] | Human feedback (user ratings, judge scores) can be logged as attributes or as additional evaluation runs referencing the same traces.[16][5] |
| **Sessions / conversations** | `MessagesPrompt` objects represent full conversations and can be published and reused; when used in traced calls, the full transcript is visible.[11] Trace comparison features include chat transcript summaries, indicating Weave stores conversation history per trace.[14] | LangChain integration captures chains over multiple messages, and Weave’s observability docs emphasize storing prompts, responses, and logs of LLM applications.[9][5] | For custom sessionization, use a consistent `session_id` attribute or top‑level call naming convention so all child calls are grouped into one session trace (inference based on Weave trace model).[8][15] |

## Integration options comparison

This section compares four practical integration patterns for a hackathon: direct Weave SDK (`@weave.op` + autopatching), OpenAI Agents SDK integration, LangChain integration, and OTEL ingestion.

### 1. Direct Weave SDK with `@weave.op` + autopatching

**What it does**

- `weave.init("project")` enables automatic tracing of supported LLM provider libraries like `openai`, `anthropic`, `cohere`, and `mistral`.[6][8][21]
- Decorating functions with `@weave.op()` records their inputs, outputs, and nested calls as a trace tree.[23][22][8][21]
- You can optionally use the service API for lower‑level control (start/end calls, set usage summaries) when needed.[15]

**Setup complexity**

- Install and import `weave`, call `weave.init("entity/project")`, and optionally decorate a few functions.[8][21]
- No framework coupling; works with plain Python, custom agents, and tool use.
- Complexity is low and compatible with a same‑day hackathon.

**Tracing depth & demo value**

- Captures all LLM calls from supported providers with prompts and outputs.[21][6][8]
- `@weave.op` boundaries give a clear call tree (e.g., `user_session -> planner_agent -> search_tool -> writer_agent`).[22][20][8]
- Great for showing nested operations, inputs/outputs, latency, cost, and metadata.

**Hackathon suitability**

- Very high: minimal plumbing, flexible enough for any of your listed setups (plain Python, custom multi‑agent, browser tools). The only work is adding decorators and choosing a couple of metadata attributes.

### 2. OpenAI Agents SDK integration

**What it does**

- Official Weave integration for the OpenAI Agents Python SDK: initialize Weave and add a `WeaveTracingProcessor` to agents to capture execution traces.[12]
- Traces include agent invocations and tool calls in multi‑agent workflows built with the SDK.[12]

**Setup complexity**

- Install `weave` and `openai-agents`, call `weave.init("project")`, and configure the Weave tracing processor on agents as shown in the docs.[12]
- Slightly more framework‑specific than plain `@weave.op`, but still straightforward.

**Tracing depth & demo value**

- Gives a structured view of multi‑agent workflows naturally, as each agent and tool is a node in the trace tree.[12]
- Pairs well with OpenAI’s own agent abstractions; judges see an “agent graph” rather than ad‑hoc function calls.

**Hackathon suitability**

- High, if you are already leaning toward the OpenAI Agents SDK: you get multi‑agent structure “for free” and only need to configure the tracing processor.
- If you are not yet committed to Agents SDK, switching to it mid‑hackathon adds overhead.

### 3. LangChain integration

**What it does**

- `weave.init()` automatically enables tracing of LangChain runnables, logging prompt templates, chains, LLM calls, tools, and agent steps.[25][9]
- You can add metadata with `weave.attributes` and, if needed, manually control tracing via `WeaveTracer` or `weave_tracing_enabled()` for specific chains.[26][9]

**Setup complexity**

- If you already use LangChain, adding Weave is just `pip install weave` and `weave.init("project")`.[9]
- Optional customization via callbacks/context managers adds minor complexity.[26]

**Tracing depth & demo value**

- Very strong: traces reflect LangChain’s internal structure—prompt templates, retrievers, tools, and agent logic—without extra code.[9]
- Easy to show judges how a complex chain breaks a task into steps.

**Hackathon suitability**

- High if your app is already built with LangChain. If you do not use LangChain, adopting it just to get tracing is likely too heavy for a same‑day hackathon.

### 4. OpenTelemetry ingestion into Weave

**What it does**

- Weave exposes an OTEL endpoint (`/otel/v1/traces` on `trace.wandb.ai`) to ingest OpenTelemetry‑formatted spans into a Weave project.[7][10]
- Examples show instrumenting OpenAI calls with `OpenAIInstrumentor`, setting attributes like `input.value`, `gen_ai.system`, and `output.value`, and exporting spans to Weave.[10][7]
- Google’s Agent Development Kit (ADK) integrates with Weave by sending OTEL spans for multi‑agent workflows, including tools and agent logic.[17]

**Setup complexity**

- Requires setting up OTEL SDKs, configuring an OTLP exporter with authentication headers (`Authorization` and `project_id`), and wiring instrumentation (e.g., OpenAIInstrumentor, custom spans).[7][10][17]
- More configuration than the direct Weave SDK, especially if you have no existing OTEL setup.

**Tracing depth & demo value**

- Very flexible: anything that can be represented as spans/attributes can be ingested—agent steps, tools, external services, browser actions.[10][17][7]
- Particularly good if you are already using OTEL or building on frameworks like Google ADK that emit OTEL traces.[17]

**Hackathon suitability**

- Medium: powerful but probably overkill unless you are already in an OTEL‑first stack or using ADK. Wiring OTEL from scratch plus Weave in one day may be risky.

## Recommended architecture

This section outlines a pragmatic architecture that works across your potential setups (plain Python, OpenAI Agents SDK, LangChain, custom multi‑agent, browser tools) while prioritizing observability.

### Core concepts

- **One trace per user request/session**: Top‑level function or agent invocation per user interaction maps to a root call/trace in Weave.[8][15]
- **Agents and tools as child calls**: Each agent and important tool is a `@weave.op` or framework‑level node (LangChain runnable, Agents SDK tool) so the trace shows a tree.[20][22][9][12]
- **Attributes for context**: Use `weave.attributes` or OTEL span attributes to attach `session_id`, `user_id`, `experiment_variant`, and business event names.[7][9][17]
- **Automatic LLM tracing**: Rely on Weave’s autopatching of OpenAI/Anthropic/etc. so each `client.chat.completions.create(...)` is visible with full prompt/response.[6][21][8]

### Architecture diagram (conceptual)

- **Frontend / browser agent** (optional): Sends requests with a `session_id` to a backend endpoint or uses a headless browser agent.
- **Backend orchestrator** (Python):
  - Top‑level `@weave.op` function `run_session(session_id, user_input)`.
  - Calls `planner_agent`, `research_agent`, `writer_agent`, `publisher_agent` (each `@weave.op`).
  - Each agent uses OpenAI/Anthropic via the provider SDK (autopatched by Weave).[21][6][8]
  - Tools (web search, browser automation, DB operations) wrapped with `@weave.op` or emit OTEL spans.
- **Weave**:
  - Receives traces via automatic LLM integration, `@weave.op` calls, and optional OTEL spans.[6][8][10][7]
  - UI shows trace tree, chat transcripts, cost/latency summaries, and evaluation scores.[14][13][16][15]

### Mapping to your scenarios

1. **Plain Python app calling LLM APIs directly**
   - Use `weave.init`, autopatching, and a few `@weave.op` decorators around orchestrator functions.
2. **OpenAI Agents SDK**
   - Same as above, plus attach WeaveTracingProcessor to agents so each agent and tool is a first‑class node.[12]
3. **LangChain**
   - `weave.init` and rely on LangChain integration to trace chains, tools, and agent steps automatically.[9]
4. **Custom multi‑agent workflow**
   - Model each agent as a `@weave.op` function and design explicit handoff calls so the tree reflects agent‑to‑agent flows.[22][20]
5. **Browser/tool‑using agent**
   - Wrap key tool calls (browser actions, HTTP calls, DB updates) as `@weave.op` so they appear as named nodes under the responsible agent.

## Minimal hackathon implementation plan

### Fastest possible setup & recommended stack

**Recommended stack for the hackathon**

- **Backend**: Plain Python orchestration with OpenAI (or Anthropic) SDK.
- **Observability**: Weave SDK with:
  - `weave.init("<team>/<project>")`.
  - Autopatching for LLM calls.
  - `@weave.op` around: (1) top‑level session handler, (2) each agent, (3) 1–2 key tools.
- **Optional**: If you are already heavily using LangChain or OpenAI Agents SDK, also enable their Weave integrations, but do not switch frameworks only for observability.

This path requires minimal new concepts, avoids OTEL complexity, and yields an impressive trace tree.

### Exactly what to trace

Focus on:

- **Top‑level user session**: `run_session(session_id, input)` as a root `@weave.op`.
- **Each agent**: planner, researcher, writer, browser/publisher agents as `@weave.op` children.
- **Key tools**: any external system call that might fail or be slow (web search, browser automation, DB writes) as `@weave.op`.
- **LLM calls**: rely on autopatching; ensure all LLM calls go through supported clients (OpenAI, Anthropic, etc.).[8][21][6]
- **Minimal metadata**: `session_id`, `user_id` (or `"demo_user"`), `flow_name`, `experiment_variant` via `weave.attributes`.
- **One or two evaluation scores**: e.g., after generating final content, call a scorer `@weave.op` that uses an LLM judge to rate quality; Weave links these scores to the trace.[16]

### Exactly what to ignore (for hackathon time constraints)

- Full `wandb` runs, sweeps, and artifacts for training.[18][2][19]
- Complex prompt versioning and publishing flows beyond a couple of `StringPrompt` or `MessagesPrompt` objects.[11]
- Comprehensive OTEL instrumentation unless you already use OTEL.
- Full production‑grade dashboards or alerting; instead, rely on Weave’s default boards and simple filters.[13]

## Code snippets

> The following snippets illustrate a minimal Weave integration for a multi‑agent app in pure Python, plus variations for LangChain and OpenAI Agents.

### 1. Basic Weave initialization and top‑level trace (plain Python)

```python
import weave
from openai import OpenAI

# Initialize Weave tracing
weave.init("team-name/agent-hackathon")  # entity/project

client = OpenAI()  # Weave autopatches this client for tracing[web:16][web:20]

@weave.op()
def call_llm(messages, model="gpt-4o") -> str:
    """Single LLM call; inputs/outputs automatically traced."""
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content

@weave.op()
def browser_tool(url: str) -> str:
    """Example tool; replace with real browser or HTTP calls."""
    # ... do something expensive/interesting here ...
    return f"[stubbed page content for {url}]"

@weave.op()
def writer_agent(topic: str) -> str:
    draft = call_llm([
        {"role": "system", "content": "You write concise, helpful summaries."},
        {"role": "user", "content": f"Write a short overview about: {topic}"},
    ])
    return draft

@weave.op()
def planner_agent(goal: str) -> dict:
    plan = call_llm([
        {"role": "system", "content": "Break the user's goal into 2-3 high-level steps."},
        {"role": "user", "content": goal},
    ])
    return {"plan": plan}

@weave.op()
def run_session(session_id: str, user_input: str) -> dict:
    """Top-level entry point for one end-user request (one trace)."""
    # Optional metadata
    with weave.attributes({"session_id": session_id, "flow": "landing_page"}):
        plan = planner_agent(user_input)
        research = browser_tool("https://example.com")
        draft = writer_agent(user_input)
        return {"plan": plan, "research": research, "draft": draft}

if __name__ == "__main__":
    result = run_session("demo-session-1", "Design a landing page for a coffee subscription.")
    print(result["draft"])
```

This code produces a trace where `run_session` is the root, with child calls `planner_agent`, `browser_tool`, `writer_agent`, and nested `call_llm` operations, plus autopatched OpenAI LLM calls.[22][21][6][8]

### 2. LangChain integration example

```python
import weave
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# Initialize Weave; enables LangChain tracing by default[web:21]
weave.init("team-name/langchain-agent")

llm = ChatOpenAI(model="gpt-4o")
prompt = PromptTemplate.from_template("1 + {number} = ")
llm_chain = prompt | llm

# Attach metadata for this call
with weave.attributes({"flow": "simple-math", "experiment": "v1"}):
    output = llm_chain.invoke({"number": 2})
    print(output)
```

Weave automatically logs the prompt template, the LLM call, and the chain as a trace; you can see these per‑call traces in the Weave UI.[25][9]

### 3. OpenAI Agents SDK + WeaveTracingProcessor (simplified)

```python
from pydantic import BaseModel
from agents import Agent, Runner, function_tool
import agents
import asyncio
import weave

weave.init("team-name/openai-agents")  # enable Weave for this project[web:10]

class Weather(BaseModel):
    city: str
    temperature_range: str
    conditions: str

@function_tool
def get_weather(city: str) -> Weather:
    return Weather(city=city, temperature_range="14-20C", conditions="Sunny with wind.")

# Configure your agent as usual
agent = Agent(
    name="Hello world",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)

# Attach WeaveTracingProcessor according to the docs (pseudo-code; exact API may vary slightly):
# agents.add_processor(WeaveTracingProcessor(project="team-name/openai-agents"))

async def main():
    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

The integration ensures the agent and its tool calls appear as a trace in Weave, with nested nodes for agent reasoning and `get_weather` tool usage.[12]

### 4. OTEL → Weave example (only if you already use OTEL)

```python
import base64
import os
import openai
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry import trace

WANDB_BASE_URL = "https://trace.wandb.ai"  # SaaS endpoint[web:22]
PROJECT_ID = "team-name/otel-agent-demo"  # entity/project
WANDB_API_KEY = os.getenv("WANDB_API_KEY")

# Configure OTLP exporter to Weave[web:22]
AUTH = base64.b64encode(f"api:{WANDB_API_KEY}".encode()).decode()
exporter = OTLPSpanExporter(
    endpoint=f"{WANDB_BASE_URL}/otel/v1/traces",
    headers={
        "Authorization": f"Basic {AUTH}",
        "project_id": PROJECT_ID,
    },
)

tracer_provider = trace_sdk.TracerProvider(
    resource=Resource({"wandb.entity": "team-name", "wandb.project": "otel-agent-demo"}),
)
tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(__name__)

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def my_agent():
    with tracer.start_as_current_span("session") as span:
        messages = [
            {"role": "user", "content": "Describe OTel in a single sentence."},
        ]
        span.set_attribute("input.value", str(messages))
        span.set_attribute("gen_ai.system", "openai")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        content = response.choices[0].message.content
        span.set_attribute("output.value", content)
        return content

if __name__ == "__main__":
    print(my_agent())
```

This pattern is powerful but should only be used if you already work with OTEL, as it adds configuration overhead.[10][17][7]

## Demo plan for judges (W&B UI walkthrough)

### What to show in the Weave UI

1. **Trace list** (Weave traces board)
   - Filter by project and show recent traces corresponding to individual hackathon runs (e.g., `landing_page_flow`).[15][8]
   - Highlight that each row is a full user session, not just a single LLM call.

2. **Trace tree / call graph**
   - Open one trace and show the tree: `run_session` → `planner_agent` → `writer_agent` → `call_llm`, plus any tools like `browser_tool`.[20][22][8]
   - Expand nodes to show nested operations and reasoning steps (or agent/tool names for Agents SDK or LangChain).[9][12]

3. **Input/output inspection**
   - Click on a call to show full prompt and response (chat transcript style), including roles and content.[11][21][15]
   - Emphasize how this helps debug hallucinations or prompt issues quickly.[24][5]

4. **Latency and cost**
   - Show columns or summary panels for duration, token usage, and estimated cost; explain that these are aggregated across traces for performance and budget analysis.[14][13][16][15]

5. **Metadata and business events**
   - Show how `session_id`, `flow`, and business event tags like `"event": "page_published"` appear as attributes and can be used to filter traces.[17][7][9]
   - Demonstrate filtering or grouping by these attributes (e.g., all traces where `event = page_published`).[13]

6. **Evaluation / feedback**
   - If you implement a small evaluation, show a panel where Weave attaches scores (e.g., exact match, LLM judge rating) to each trace.[1][14][16]
   - Explain how this could be extended post‑hackathon to continuous evaluation and monitoring (real‑time guardrails, safety checks).[5][16]

7. **Comparison view (if time)**
   - Use Weave’s improved trace comparison to show two runs side by side with score diffs, usage differences, and call breakdowns.[14]
   - This illustrates how teams can quickly choose better prompts or agent configurations.

### Why this matters for autonomous agents

- Agents are multi‑step, stateful systems; without a trace, teams cannot see **which step failed or was slow**.[27][5]
- Observability makes agents debuggable and improvable by exposing their internal decisions and tool usage.
- The same traces form a **dataset of real behavior** that can later power evaluations, fine‑tuning, or RL, aligning with how Weave is positioned for iterative LLM development.[27][4][1][16]

## Risks / limitations

### Setup friction

- **Account and API key management**: You must create a W&B account, obtain an API key, and set environment variables or login locally; this is straightforward but an extra step for a hackathon team.[10][17]
- **Library versions and integrations**: Autopatching assumes supported provider libraries (`openai`, etc.) are used; other HTTP clients require manual `@weave.op` or OTEL spans.[6][7][8]
- **Framework coupling**: The OpenAI Agents and LangChain integrations require familiarity with those frameworks; switching stacks mid‑hackathon to use them can slow you down.[9][12]

### Dashboard and feature limits

- Weave’s UI is evolving quickly; features like trace comparison, panels, and boards are powerful but may change layouts or require some clicking to learn.
  This is noted in recent announcements about improved trace comparison and analysis features rather than a static UI.[14]
- Some advanced features (e.g., deep model registry integration, large‑scale evaluation workflows) are more valuable for long‑running projects than for a 1‑day hackathon, so time spent there has low marginal value.[4][16]

### Metadata and privacy concerns

- Weave stores full prompts, responses, and metadata; W&B’s observability docs emphasize logging “every user prompt, model output, and system metric.”[5]
- If prompts include PII, secrets, or proprietary data, it will be visible in W&B unless masked or redacted client‑side.
- Hackathon projects usually avoid sensitive data, but you should still:
  - Avoid logging API keys or raw auth tokens.
  - Keep user identifiers pseudonymous where possible.
  - Use project scoping and team permissions appropriately.[3][18]

### Cost and performance overhead

- Each traced call implies additional network round‑trips and storage in W&B; OpenAI monitoring docs highlight comprehensive logging and dashboards built from that data, which inherently has some overhead.[13]
- For a hackathon‑sized workload, overhead is negligible, but at production scale you would selectively trace or sample to control cost (this is an inference based on typical observability patterns rather than an explicit W&B requirement).

### What does not work well in a hackathon timeframe

- **Full OTEL build‑out** for a custom system if you do not already use OTEL: configuring exporters, resources, and instrumentation for every component is time‑consuming.[7][17][10]
- **Deep evaluation pipelines** with large labeled datasets, complex scorers, and model registry integration; Weave supports this but it is overkill for a weekend and requires dataset curation.[16]
- **Advanced prompt/version governance** with many published prompts and variants; managing this well requires more design time across the team.[11]

## Final recommendation

### Best observability demo with least engineering time

Given the constraints and goals, the most effective approach is:

1. **Use Weave as the primary observability layer** (not classic wandb runs).
2. **Build the agentic app in plain Python (or your existing LangChain / OpenAI Agents code) and minimally instrument it with Weave**:
   - Call `weave.init("team/project")` once at startup.[21][8]
   - Ensure all LLM calls go through supported provider SDKs so autopatching captures prompts and outputs.[8][6]
   - Decorate the top‑level session handler, each agent, and a couple of key tools with `@weave.op` to create a clear trace tree.[23][22][8]
   - Use `weave.attributes` (or similar) to add `session_id`, `flow`, and 1–2 business events (e.g., `event = page_published`).[7][9]
   - Optionally, add a small evaluation step using Weave’s evaluation utilities later if time permits.[16]

This yields a polished, judge‑friendly demo: a Weave traces board where each row is a user request; click through to see a readable tree of agents, tools, and LLM calls with prompts, outputs, latency, and cost.

### Recommended implementation plan

1. **Day‑of setup (1–2 hours)**
   - Create W&B account and project; obtain API key.[10]
   - `pip install weave` (and `wandb` if desired for future runs).
   - Add `weave.init("team-name/agent-hackathon")` at app startup.[21][8]

2. **Instrument core flows (1–2 hours)**
   - Identify the main user journey (e.g., “design and publish landing page”).
   - Wrap the entrypoint in `@weave.op` (`run_session`).
   - Wrap each agent and 1–2 tools in `@weave.op` and ensure they call the LLM through supported clients.[22][6][8]
   - Add `weave.attributes` with `session_id`, `flow`, and business events (`event = page_published`, `event = design_selected`).[7][9]

3. **Polish the demo (1–2 hours)**
   - Generate a few representative runs to populate traces.
   - In the Weave UI, configure a saved view or simple dashboard showing:
     - Trace table with columns: flow, duration, token usage, cost.[15][13][14]
     - Example trace expanded to show nested agents/tools.
     - (Optional) evaluation scores for final outputs.[16]

4. **Prepare talking points for judges**
   - Emphasize how Weave gives step‑level visibility into agents and tools, making debugging and iteration faster.[24][27][5]
   - Connect this observability story to reliability, cost control, and safety in autonomous agents.

### Fallback plan

If the Weave SDK approach encounters unexpected friction (e.g., networking constraints, library conflicts), use this fallback:

- **Fallback: OTEL → Weave with minimal spans**
  - Set up a basic OTEL tracer and exporter to Weave as shown in the official docs.[10][7]
  - For each user request, create a top‑level span with attributes for `session_id`, `flow`, and serialized prompt/response.
  - Optionally create child spans for key tools or agents.

This fallback still provides a coherent trace per session in the Weave UI, though with less automatic detail than full Weave SDK integration.[17][7][10]

Overall, for a hackathon, **Weave SDK with `@weave.op` and automatic LLM tracing is the primary recommendation**, with OTEL as a backup only if you are already set up for OpenTelemetry.