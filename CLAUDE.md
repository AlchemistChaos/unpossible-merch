# Ralph Agent Instructions

You are an autonomous coding agent building "Unpossible Merch" — an AI agent that scrapes Luma event data, generates t-shirt design briefs, self-critiques them, and creates designs using Gemini image generation.

## Project Context

- This is a **fast hackathon prototype** (Ralphthon SF 2026) - prioritize working code over perfection
- Pipeline: scrape event → generate 10 briefs → self-critique to 6 → generate images
- CLI-based (no web UI needed)
- Uses W&B Weave for observability
- Uses playwright-cli for web scraping (installed globally)
- Keep dependencies minimal, code simple
- See `docs/design-doc.md` for the full design document

## Your Task (ONE iteration)

1. Read `prd.json` in the project root
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
- API keys in `.env` file (GOOGLE_API_KEY, WANDB_API_KEY, PLATFORM_EMAIL, PLATFORM_PASSWORD)
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

All designs should be **black and white**, print-ready, high contrast.

## Checkpoint System

Each pipeline stage should save output to `checkpoints/`:
- `checkpoints/01-event-data.json`
- `checkpoints/02-briefs.json`
- `checkpoints/03-selected-briefs.json`
- `checkpoints/04-images.json`

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
