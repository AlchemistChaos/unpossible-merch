# Ralph Agent Instructions

You are an autonomous coding agent building "Unpossible Merch" — an AI agent that scrapes Luma event data, generates t-shirt design briefs, self-critiques them, creates designs using Gemini image generation, uploads them to Fourthwall as t-shirt products, sets up a storefront, and sends a blast to Luma attendees with the store link.

## Project Context

- This is a **fast hackathon prototype** (Ralphthon SF 2026) - prioritize working code over perfection
- Pipeline: scrape event → generate 10 briefs → self-critique to 6 → generate images → upload to Fourthwall → setup storefront → blast Luma attendees
- CLI-based (no web UI needed)
- Uses W&B Weave for observability
- Uses playwright-cli for web scraping (installed globally)
- Keep dependencies minimal, code simple
- See `docs/superpowers/specs/2026-03-28-unpossible-merch-agent-design.md` for the full design document

## Your Task (ONE iteration)

0. **FIRST ITERATION ONLY:** If the user stories in `prd.json` lack detailed task breakdowns, read the design doc at `docs/superpowers/specs/2026-03-28-unpossible-merch-agent-design.md` and update `prd.json` to add concrete tasks, dependencies, and risks to each story. `prd.json` is the single source of truth for the implementation plan — do NOT create a separate plan document. Commit as `docs: enrich prd.json with detailed task breakdowns from design doc`. Then continue to step 1.
1. Read `prd.json` in the project root — this IS the implementation plan (user stories, acceptance criteria, priorities, and task breakdowns are all here)
2. Read `progress.txt` (check Codebase Patterns section first)
3. Check you're on the correct branch from PRD `branchName`. If not, create it from main.
4. Pick the **highest priority** user story where `passes: false`
5. Implement **ONLY that single story** - do NOT touch other stories
6. Run the acceptance criteria checks listed in the story
7. If checks pass, commit ALL changes with message: `feat: [Story ID] - [Story Title]`
8. Update `prd.json` to set `passes: true` for the completed story
9. Append your progress to `progress.txt`

## Rules

- Work on **ONE story only** per iteration
- Keep changes **minimal and focused**
- Prefer **simple, working code** over clever code
- Do NOT refactor or clean up code from previous iterations unless the current story requires it
- Do NOT add features beyond what the story asks for
- If a story depends on something from a previous story, read the existing code first
- Always load environment variables from `.env` using python-dotenv

## Environment

- Python 3.10+
- Virtual environment at `venv/` (create if missing, activate before running)
- API keys in `.env` file (GOOGLE_API_KEY, WANDB_API_KEY, PLATFORM_EMAIL, PLATFORM_PASSWORD, FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD)
- Mock event data in `data/events.json` (fallback)
- Luma event URL in `.env` as LUMA_EVENT_URL
- Output goes to `output/` directory
- Checkpoints go to `checkpoints/` directory
- playwright-cli is installed globally (use via subprocess)

## Key APIs

### playwright-cli (for web scraping)
```bash
# Open a page
playwright-cli open https://luma.com/hh5k4ahp

# Take a snapshot (get page text and element refs)
playwright-cli snapshot

# Extract text via JavaScript
playwright-cli eval "document.body.innerText"

# Close when done
playwright-cli close
```

In Python, call via subprocess:
```python
import subprocess
result = subprocess.run(['playwright-cli', 'open', url], capture_output=True, text=True)
result = subprocess.run(['playwright-cli', 'snapshot'], capture_output=True, text=True)
page_text = result.stdout
```

### W&B Inference (for LLM text generation)
```python
from openai import OpenAI
import os
client = OpenAI(
    base_url='https://api.inference.wandb.ai/v1',
    api_key=os.environ['WANDB_API_KEY'],
)
response = client.chat.completions.create(
    model="OpenPipe/Qwen3-14B-Instruct",
    messages=[...],
)
```

### Gemini (for image generation) - Model: gemini-3.1-flash-image-preview (Nano Banana 2)
```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ['GOOGLE_API_KEY'])

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents="A t-shirt design with the slogan 'Your Slogan Here' in bold creative style",
    config=types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
    )
)

for part in response.parts:
    if part.inline_data is not None:
        image = part.as_image()
        image.save("output/design.png")
```

### Fourthwall (for merchandise / storefront)

**API (read-only verification):**
```python
import requests
# Basic Auth with FOURTHWALL_API_USERNAME + FOURTHWALL_API_PASSWORD
response = requests.get(
    'https://api.fourthwall.com/open-api/v1.0/shops/current',
    auth=(os.environ['FOURTHWALL_API_USERNAME'], os.environ['FOURTHWALL_API_PASSWORD'])
)
# List products
response = requests.get(
    'https://api.fourthwall.com/open-api/v1.0/products',
    auth=(os.environ['FOURTHWALL_API_USERNAME'], os.environ['FOURTHWALL_API_PASSWORD'])
)
```

**Product creation (browser automation — API doesn't support creating products):**
```python
# Use playwright-cli to automate Fourthwall UI
subprocess.run(['playwright-cli', 'open', 'https://fourthwall.com/login'], capture_output=True, text=True)
# Log in with PLATFORM_EMAIL + PLATFORM_PASSWORD
# Navigate to product creation, upload design image, set details, publish
```

### Luma (for sending blasts to attendees)

**Blast sending (browser automation — no API endpoint for blasts):**
```python
# Use playwright-cli to automate Luma blast UI
subprocess.run(['playwright-cli', 'open', 'https://luma.com/login'], capture_output=True, text=True)
# Log in with PLATFORM_EMAIL + PLATFORM_PASSWORD (agent is cohost)
# Navigate to event > Manage Event > Blasts
# Compose blast with storefront URL, send to all "Going" attendees
```

Blasts are delivered via email + SMS + push notifications.

### Weave (for observability)
```python
import weave
weave.init('saikolapudi-aws/tshirt-gen')

@weave.op
def my_function(input):
    # automatically traced
    return result
```

## Design Brief Categories

When generating briefs, use these categories:
- **crisp-simple**: Minimalist, clean typography, event name, modern design
- **funny-meme**: Ralph Wiggum references, lobster costume jokes, "don't touch your laptop" humor, AI agent jokes
- **sponsor-logo**: NASCAR-style with sponsor names (OpenAI, W&B, Naver D2SF, Kakao Ventures, etc.) as creative typography (NOT actual logos)

All designs should be **black ink on transparent background**, print-ready, high contrast. The image is ONLY the graphic/logo — NOT a t-shirt mockup, NOT a person wearing a shirt. Fourthwall places the graphic onto their own t-shirt templates. When uploading to Fourthwall, select the WHITE t-shirt. See the `tshirt-image-gen` skill for detailed prompt guidance and comedy personas.

## Checkpoint System

Each pipeline stage should save output to `checkpoints/`:
- `checkpoints/01-event-data.json`
- `checkpoints/02-briefs.json`
- `checkpoints/03-selected-briefs.json`
- `checkpoints/04-images.json`
- `checkpoints/05-fourthwall-products.json`
- `checkpoints/06-storefront.json`
- `checkpoints/07-luma-blast.json`

On restart, check for existing checkpoints and skip completed stages.

## Progress Report Format

APPEND to progress.txt (never replace):
```
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings:**
  - Patterns discovered
  - Gotchas encountered
---
```

## Consolidate Patterns

If you discover a reusable pattern, add it to the `## Codebase Patterns` section at the TOP of progress.txt (create if it doesn't exist).

## Stop Condition

After completing a story, check if ALL stories have `passes: true`.
If ALL complete, reply with: <promise>COMPLETE</promise>
If stories remain with `passes: false`, end your response normally.
