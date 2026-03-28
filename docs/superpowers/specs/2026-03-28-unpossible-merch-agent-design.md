# Unpossible Merch — Design Document

## Overview

Unpossible Merch is an autonomous AI agent that scrapes Luma event data, generates t-shirt design briefs, self-critiques them, and creates designs using Gemini image generation. CLI-based, no web UI needed.

Pipeline:
1. Scrape event details via playwright-cli
2. Generate 10 t-shirt design briefs (W&B Inference API)
3. Self-critique and narrow to 6 (W&B Inference API)
4. Generate images via Gemini Imagen
5. Output designs + Weave traces

One-shot execution: runs start-to-finish with no human intervention.

## Target Event

- **Event:** Unpossible Ralphathon
- **URL:** https://luma.com/hh5k4ahp
- **Date:** March 28–31, 2026 (main event March 30–31)
- **Location:** W&B Office, 400 Alabama St, San Francisco, CA 94110
- **Sponsors:** OpenAI, Naver D2SF, Hanriver Partners, Kakao Ventures, Bass Ventures, Weights & Biases
- **Type:** AI agent hackathon — teams deploy autonomous AI agents while networking
- **Hosts:** River Tamoor Baig + Unpossible Merch (co-host)

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Web scraping | playwright-cli (global install, called via subprocess) |
| Text generation (briefs/critique) | W&B Inference API (`OpenPipe/Qwen3-14B-Instruct` via OpenAI client) |
| Image generation | Gemini (`gemini-3.1-flash-image-preview` via `google-genai`) |
| Observability | W&B Weave (`weave`) |
| Config | python-dotenv |
| Dev loop | Ralph Loop (iterative autonomous build) |

### Python Dependencies

```
google-genai
openai
weave
wandb
python-dotenv
```

## Architecture

### Single Orchestrator

```
run.py
  └── app/pipeline.py (run_pipeline)
        ├── Stage 1: Scrape Luma event (playwright-cli via subprocess)
        ├── Stage 2: Generate 10 design briefs (W&B Inference)
        ├── Stage 3: Self-critique & narrow to 6 (W&B Inference)
        ├── Stage 4: Generate images (Gemini Imagen)
        └── Stage 5: Save results + Weave traces
```

Each stage writes a checkpoint file (JSON) to `./checkpoints/`. If the agent crashes and restarts, it can skip completed stages.

### Module Structure

```
app/
  __init__.py
  config.py              # Loads .env, exports config values
  pipeline.py            # Orchestrator — runs stages sequentially
  scrape_event.py        # Stage 1: playwright-cli event scraping
  briefs.py              # Stage 2: Design brief generation
  critique.py            # Stage 3: Self-critique & selection
  design.py              # Stage 4: Gemini image generation
run.py                   # Entry point — calls run_pipeline()
data/
  events.json            # Mock/fallback event data
  scraped_event.json     # Scraped event output
output/                  # Generated images
checkpoints/             # Stage checkpoints
.env                     # Credentials (gitignored)
```

## Stage Details

### Stage 1: Scrape Luma Event

**File:** `app/scrape_event.py` — `scrape_event(event_url) -> dict`

**Input:** Event URL (`https://luma.com/hh5k4ahp`)
**Output:** `EventData` dict saved to `data/scraped_event.json`

**Approach:** Use playwright-cli via subprocess. The event page is public — no login needed for scraping.

```python
subprocess.run(['playwright-cli', 'open', event_url], capture_output=True, text=True)
subprocess.run(['playwright-cli', 'snapshot'], capture_output=True, text=True)
# Parse page_text into EventData
subprocess.run(['playwright-cli', 'close'], capture_output=True, text=True)
```

Data to extract:
- Event name, description/theme, date/time, location
- Sponsors: OpenAI, Naver D2SF, Hanriver Partners, Kakao Ventures, Bass Ventures, Weights & Biases
- Attendee profile keywords: AI engineers, builders, startup founders

**Fallback:** If scraping fails, load `data/events.json` mock data (first entry = Ralphthon).

**Checkpoint:** `checkpoints/01-event-data.json`

### Stage 2: Generate Design Briefs

**File:** `app/briefs.py` — `generate_briefs(event_data) -> list[dict]`

**Input:** `EventData` dict
**Output:** 10 `DesignBrief` dicts

Uses W&B Inference API (OpenAI-compatible client with `OpenPipe/Qwen3-14B-Instruct`) to generate 10 t-shirt design concepts.

Each brief includes:
- `id`: unique identifier
- `title`: e.g., "The Lobster Rule"
- `category`: one of `crisp-simple`, `funny-meme`, `sponsor-logo`
- `description`: visual concept description
- `slogans`: list of text/slogans for the shirt
- `color_notes`: always "black and white"

**Distribution:** 4 crisp-simple, 4 funny-meme, 2 sponsor-logo

**Prompt strategy:** Single LLM call requesting JSON output. Prompt includes event context and references the event's unique character — lobster costume rule, autonomous-agents-only theme, Ralph Wiggum "me fail English" meme origin.

**Sponsor treatment:** All sponsor references use text/typography only (company names styled creatively). No actual logo images.

**Checkpoint:** `checkpoints/02-briefs.json`

### Stage 3: Self-Critique & Narrow to 6

**File:** `app/critique.py` — `critique_briefs(briefs) -> list[dict]`

**Input:** 10 `DesignBrief` dicts
**Output:** 6 selected `DesignBrief` dicts with `critique_notes` field added

Uses W&B Inference API to evaluate the 10 briefs against criteria:
- **Printability:** Simple shapes, readable text, high contrast black & white
- **Relevance:** Captures the event's identity
- **Variety:** Good range across categories
- **Humor/appeal:** Would attendees want to wear this?

Returns ranked selection of 6 with rationale for each inclusion/exclusion. Target distribution: ~2 crisp, ~2 funny, ~2 sponsor (advisory — quality trumps quota).

**Checkpoint:** `checkpoints/03-selected-briefs.json`

### Stage 4: Generate Images via Gemini

**File:** `app/design.py` — `generate_design(brief) -> str` (returns image path)

**Input:** 6 selected `DesignBrief` dicts
**Output:** 6 PNG images saved to `output/`

Uses Gemini with model `gemini-3.1-flash-image-preview`:

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
    )
)
for part in response.parts:
    if part.inline_data is not None:
        image = part.as_image()
        image.save(f"output/{brief_id}.png")
```

Each image:
- Black and white color scheme
- Standalone graphic (not a t-shirt mockup)
- PNG format, white background
- Resolution: native Gemini output

**Image prompt strategy:** Brief description + slogans converted to prompt emphasizing:
- "Black and white t-shirt graphic design"
- "High contrast, clean lines, print-ready"
- "White background, centered composition"

**Retry:** Up to 2 retries on API error only. Accept whatever Gemini produces if API succeeds.

**Rate limiting:** Sequential generation with 2-second delay between calls.

**Checkpoint:** `checkpoints/04-images.json` (brief IDs + file paths)

## Data Types

```python
# EventData
{
    "name": str,
    "description": str,
    "date": str,
    "location": str,
    "sponsors": list[str],
    "attendee_types": list[str]
}

# DesignBrief
{
    "id": str,
    "title": str,
    "category": str,  # "crisp-simple" | "funny-meme" | "sponsor-logo"
    "description": str,
    "slogans": list[str],
    "color_notes": str,
    "critique_notes": str | None  # added by Stage 3
}

# ImageResult
{
    "brief_id": str,
    "file_path": str,
    "prompt_used": str,
    "retry_count": int
}
```

## Credential Management

All credentials loaded from `.env` via python-dotenv:

```
GOOGLE_API_KEY=<gemini api key>
WANDB_API_KEY=<wandb api key>
LUMA_EVENT_URL=https://luma.com/hh5k4ahp
PLATFORM_EMAIL=riverscreation+ralph@gmail.com
PLATFORM_PASSWORD=UnpossibleMerch101!
```

`app/config.py` loads `.env` and exports config values. No credentials in source code.

## Checkpoint System

Each stage writes JSON to `checkpoints/`. The orchestrator checks for existing checkpoints on startup and skips completed stages.

- `checkpoints/01-event-data.json`
- `checkpoints/02-briefs.json`
- `checkpoints/03-selected-briefs.json`
- `checkpoints/04-images.json`

Pass `--clean` flag to `run.py` to clear checkpoints and start fresh.

## Observability

W&B Weave traces all pipeline functions:

```python
import weave
weave.init('saikolapudi-aws/tshirt-gen')

@weave.op
def scrape_event(event_url):
    ...
```

Key functions decorated with `@weave.op`: `run_pipeline`, `scrape_event`, `generate_briefs`, `critique_briefs`, `generate_design`.

## Error Handling

- **Gemini API failures:** Retry with exponential backoff, 3 attempts max
- **Gemini safety filter rejections:** Retry with softened prompt, 2 attempts
- **playwright-cli failures:** Fall back to mock data from `data/events.json`
- **Individual image failure:** Log error, continue to next brief
- **Partial completion:** Checkpoint system ensures no work is lost

## CLI Interface

```bash
# Full pipeline run
python run.py

# Use mock data instead of scraping
python run.py --mock

# Custom event URL
python run.py --event-url https://luma.com/other-event

# Clear checkpoints and start fresh
python run.py --clean
```

## Expected Runtime

Full pipeline estimate: 3–5 minutes
- Stage 1 (scrape): ~30 seconds
- Stage 2 (briefs): ~10 seconds
- Stage 3 (critique): ~10 seconds
- Stage 4 (images): ~2–3 minutes (6 images with delays)

## Implementation Approach

This project is built iteratively via **Ralph Loop** (`scripts/ralph/ralph.sh`). Ralph reads `prd.json`, picks the highest-priority incomplete user story, implements it, runs acceptance checks, commits, and repeats until all stories pass.

The `prd.json` file contains 8 user stories (US-001 through US-008) that cover the full build:
1. Project setup + dependencies
2. Scrape Luma event via playwright-cli
3. Generate 10 design briefs
4. Self-critique and narrow to 6
5. Generate images with Gemini
6. End-to-end pipeline with checkpoints
7. Weave tracing
8. Error handling, polish, demo script

Ralph writes its own implementation plan implicitly through `progress.txt` — each iteration appends what was built, files changed, and learnings discovered. No separate implementation plan document is needed.

## Success Criteria

The agent is done when:

1. Running `python run.py` executes all stages without intervention
2. 6 PNG t-shirt designs appear in `output/`
3. Designs are relevant to the Unpossible Ralphathon event (not generic)
4. Weave traces are visible in the W&B dashboard
5. `python run.py --mock` works as a reliable demo fallback
6. All 8 user stories in `prd.json` have `passes: true`
