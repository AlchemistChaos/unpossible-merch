# Unpossible Merch — Design Document

## Overview

Unpossible Merch is an autonomous AI agent that generates event-branded t-shirt merchandise for Luma events end-to-end. Given a Luma event where it's been added as co-host, the agent:

1. Scrapes event details (name, theme, sponsors, attendee types) via playwright-cli
2. Generates 10 t-shirt design briefs, self-critiques, narrows to 6
3. Generates images via Gemini Imagen
4. Uploads designs to Fourthwall and creates t-shirt products
5. Configures a Fourthwall storefront website to sell the merchandise
6. Sends a blast to Luma attendees (as cohost) with the store link

One-shot execution: the agent runs start-to-finish with no human intervention.

## Target Event

- **Event:** Unpossible Ralphathon
- **URL:** https://luma.com/hh5k4ahp
- **Date:** March 28–31, 2026 (main event March 30–31)
- **Location:** W&B Office, 400 Alabama St, San Francisco, CA 94110
- **Sponsors:** OpenAI, Naver D2SF, Hanriver Partners, Kakao Ventures, Bass Ventures, Weights & Biases
- **Type:** AI agent hackathon — teams deploy autonomous AI agents while networking
- **Hosts:** River Tamoor Baig + Unpossible Merch (co-host)

## Browser Automation Principle

**Whenever the agent needs to interact with a website or web service and does not have API access (or the API doesn't support the needed operation), use playwright-cli for browser automation.** This applies to any external service — not just Fourthwall and Luma. If a future stage requires interacting with a website (e.g. uploading to a print service, posting on social media, filling out a form), the default approach is playwright-cli via subprocess. Only use direct API calls when API credentials and endpoints are available for the specific operation.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Web scraping | playwright-cli (global install, called via subprocess) |
| Text generation (briefs/critique) | W&B Inference API (`OpenPipe/Qwen3-14B-Instruct` via OpenAI client) |
| Image generation | Gemini (`gemini-3.1-flash-image-preview` via `google-genai`) |
| Merchandise platform | Fourthwall (browser automation via playwright-cli) |
| Event platform | Luma (scraping + blast sending via playwright-cli) |
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
requests
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
        ├── Stage 5: Upload designs to Fourthwall & create products (playwright-cli)
        ├── Stage 6: Configure Fourthwall storefront (playwright-cli)
        ├── Stage 7: Send Luma blast to attendees with store link (playwright-cli)
        └── Stage 8: Save results + Weave traces
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
  fourthwall.py          # Stage 5: Fourthwall product creation (playwright-cli)
  storefront.py          # Stage 6: Fourthwall storefront setup (playwright-cli)
  luma_blast.py          # Stage 7: Luma blast sending (playwright-cli)
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
- **Black design on transparent background** — NOT a t-shirt mockup, NOT a person wearing a shirt
- The image is ONLY the graphic/logo itself — Fourthwall places it onto their own t-shirt templates
- PNG format with transparency (no background color)
- Black ink only — the design will be printed on a white t-shirt selected in Fourthwall
- Resolution: native Gemini output

**Image prompt strategy:** Brief description + slogans converted to prompt emphasizing:
- "Black graphic design on transparent/blank background"
- "Just the logo/graphic, NOT a t-shirt mockup, NOT a person wearing a shirt"
- "High contrast, clean lines, print-ready, black ink only"
- "PNG with transparent background, centered composition"
- "Bold readable typography, screen-print style"

**Fourthwall upload note:** When uploading to Fourthwall, select the WHITE t-shirt template. The black graphic will be placed on the white shirt by Fourthwall's product designer.

**Humor approach:** Designs should be genuinely funny. Use 3 distinct comedy personas to generate variety — see the `tshirt-image-gen` skill for detailed prompt guidance.

**Retry:** Up to 2 retries on API error only. Accept whatever Gemini produces if API succeeds.

**Rate limiting:** Sequential generation with 2-second delay between calls.

**Checkpoint:** `checkpoints/04-images.json` (brief IDs + file paths)

### Stage 5: Upload Designs to Fourthwall & Create Products

**File:** `app/fourthwall.py` — `upload_designs(selected_briefs, image_paths) -> list[dict]`

**Input:** 6 selected briefs + their generated image file paths
**Output:** List of created product dicts (title, product URL, status)

Fourthwall's Open API is read-only for products (list/get only). Product creation requires browser automation via playwright-cli.

**Approach:**
1. Log in to Fourthwall using PLATFORM_EMAIL + PLATFORM_PASSWORD
2. For each design:
   - Navigate to product creation flow
   - Select t-shirt as product type
   - Upload the PNG design image
   - Set product title from brief title
   - Set description from brief description + slogans
   - Set pricing (use Fourthwall defaults or a reasonable price)
   - Publish the product
3. Collect product URLs for each created product

**Verification:** After creation, use Fourthwall API (Basic Auth) to confirm products exist:
```python
import requests
response = requests.get(
    'https://api.fourthwall.com/open-api/v1.0/products',
    auth=(FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD)
)
```

**Checkpoint:** `checkpoints/05-fourthwall-products.json`

### Stage 6: Configure Fourthwall Storefront

**File:** `app/storefront.py` — `setup_storefront(event_data, product_urls) -> dict`

**Input:** Event data + list of product URLs
**Output:** Storefront config dict with public storefront URL

**Approach:**
1. Log in to Fourthwall (reuse session from Stage 5 if possible)
2. Navigate to shop settings
3. Set shop name to event-themed name (e.g., "Unpossible Merch — Ralphathon")
4. Ensure all created products are visible/published on the storefront
5. Capture the public storefront URL

**Verification:** Use Fourthwall API to confirm shop details:
```python
response = requests.get(
    'https://api.fourthwall.com/open-api/v1.0/shops/current',
    auth=(FOURTHWALL_API_USERNAME, FOURTHWALL_API_PASSWORD)
)
```

**Checkpoint:** `checkpoints/06-storefront.json`

### Stage 7: Send Luma Blast to Attendees

**File:** `app/luma_blast.py` — `send_blast(event_url, storefront_url) -> dict`

**Input:** Luma event URL + Fourthwall storefront URL
**Output:** Blast result dict (sent status, recipient count)

Luma does not have an API endpoint for sending blasts. Blasts must be sent via the event management UI using browser automation.

**Approach:**
1. Log in to Luma using PLATFORM_EMAIL + PLATFORM_PASSWORD (agent is cohost)
2. Navigate to event page > Manage Event > Blasts tab
3. Compose a new blast with:
   - Subject: event-themed merch announcement
   - Body: brief description of designs + storefront URL
4. Set recipients to all "Going" attendees (default)
5. Send the blast

Blasts are delivered via email + SMS + push notifications to all targeted attendees.

**Checkpoint:** `checkpoints/07-luma-blast.json`

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

# FourthwallProduct
{
    "brief_id": str,
    "title": str,
    "product_url": str,
    "status": str  # "published" | "draft" | "failed"
}

# StorefrontConfig
{
    "shop_name": str,
    "storefront_url": str,
    "product_count": int
}

# BlastResult
{
    "event_url": str,
    "storefront_url": str,
    "blast_subject": str,
    "recipient_count": int,
    "sent": bool
}
```

## External Services

### Fourthwall (Merchandise Platform)
- **Website:** https://fourthwall.com
- **API Base URL:** `https://api.fourthwall.com/open-api/v1.0/`
- **Auth:** Basic Auth (FOURTHWALL_API_USERNAME + FOURTHWALL_API_PASSWORD in .env)
- **API use:** Read-only verification (list products, get shop info)
- **Product creation:** Browser automation via playwright-cli (API doesn't support creating products)
- **UI login:** PLATFORM_EMAIL + PLATFORM_PASSWORD

### Luma (Event Platform)
- **API Base URL:** `https://public-api.luma.com`
- **Auth:** API key via `x-luma-api-key` header (requires Luma Plus)
- **Key API endpoints:** GET `/v1/event-get`, GET `/v1/event-get-guests`, POST `/v1/event-send-invites`
- **Blast sending:** No API endpoint — browser automation via playwright-cli
- **UI login:** PLATFORM_EMAIL + PLATFORM_PASSWORD (agent is cohost on the event)

## Credential Management

All credentials loaded from `.env` via python-dotenv:

```
GOOGLE_API_KEY=<gemini api key>
WANDB_API_KEY=<wandb api key>
LUMA_EVENT_URL=https://luma.com/hh5k4ahp
PLATFORM_EMAIL=<login email for Luma + Fourthwall>
PLATFORM_PASSWORD=<login password for Luma + Fourthwall>
FOURTHWALL_API_USERNAME=<fourthwall api basic auth username>
FOURTHWALL_API_PASSWORD=<fourthwall api basic auth password>
```

`app/config.py` loads `.env` and exports config values. No credentials in source code.

## Checkpoint System

Each stage writes JSON to `checkpoints/`. The orchestrator checks for existing checkpoints on startup and skips completed stages.

- `checkpoints/01-event-data.json`
- `checkpoints/02-briefs.json`
- `checkpoints/03-selected-briefs.json`
- `checkpoints/04-images.json`
- `checkpoints/05-fourthwall-products.json`
- `checkpoints/06-storefront.json`
- `checkpoints/07-luma-blast.json`

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

Key functions decorated with `@weave.op`: `run_pipeline`, `scrape_event`, `generate_briefs`, `critique_briefs`, `generate_design`, `upload_designs`, `setup_storefront`, `send_blast`.

## Error Handling

- **Gemini API failures:** Retry with exponential backoff, 3 attempts max
- **Gemini safety filter rejections:** Retry with softened prompt, 2 attempts
- **playwright-cli failures (scraping):** Fall back to mock data from `data/events.json`
- **Individual image failure:** Log error, continue to next brief
- **Fourthwall upload failure:** Log error, continue to next product; pipeline continues with whatever products were created
- **Storefront setup failure:** Log error; pipeline continues — products are still accessible via direct URLs
- **Luma blast failure:** Log error; pipeline reports store URL for manual sharing
- **Partial completion:** Checkpoint system ensures no work is lost

## CLI Interface

```bash
# Full pipeline run
python run.py

# Use mock data instead of scraping
python run.py --mock

# Custom event URL
python run.py --event-url https://luma.com/other-event

# Skip sending the Luma blast (for testing)
python run.py --skip-blast

# Clear checkpoints and start fresh
python run.py --clean
```

## Expected Runtime

Full pipeline estimate: 5–8 minutes
- Stage 1 (scrape): ~30 seconds
- Stage 2 (briefs): ~10 seconds
- Stage 3 (critique): ~10 seconds
- Stage 4 (images): ~2–3 minutes (6 images with delays)
- Stage 5 (Fourthwall upload): ~2–3 minutes (6 products via browser automation)
- Stage 6 (storefront): ~30 seconds
- Stage 7 (Luma blast): ~30 seconds

## Implementation Approach

**The implementation plan is `prd.json`.** There is no separate implementation plan document. On first iteration, Ralph reads this design document and enriches `prd.json` by adding detailed task breakdowns, dependencies, and risks to each user story. After that, `prd.json` is the single source of truth for what to build and in what order.

**Execution via Ralph Loop.** The project is built iteratively via **Ralph Loop** (`scripts/ralph/ralph.sh`). Ralph reads `prd.json`, picks the highest-priority incomplete user story, implements it, runs acceptance checks, commits, and repeats until all stories pass.

The `prd.json` file contains 11 user stories (US-001 through US-011) that cover the full build:
1. Project setup + dependencies
2. Scrape Luma event via playwright-cli
3. Generate 10 design briefs
4. Self-critique and narrow to 6
5. Generate images with Gemini
6. Upload designs to Fourthwall & create t-shirt products
7. Configure Fourthwall storefront website
8. Send Luma blast to attendees with store link
9. End-to-end pipeline with checkpoints
10. Weave tracing
11. Error handling, polish, demo script

Ralph appends progress to `progress.txt` after each iteration — what was built, files changed, and learnings discovered.

## Success Criteria

The agent is done when:

1. Running `python run.py` executes all stages without intervention
2. 6 PNG t-shirt designs appear in `output/`
3. Designs are relevant to the Unpossible Ralphathon event (not generic)
4. T-shirt products are live on Fourthwall storefront
5. Storefront URL is accessible and shows all products
6. Luma blast is sent to attendees with the store link
7. Weave traces are visible in the W&B dashboard
8. `python run.py --mock --skip-blast` works as a reliable demo fallback
9. All user stories in `prd.json` have `passes: true`

## Known Bugs & Required Fixes

These are bugs discovered during the first end-to-end run that must be fixed before the pipeline is considered complete.

### BUG-001: Luma blast not actually sending

**Severity:** Critical
**Stage:** 7 (Luma blast)
**File:** `app/luma_blast.py`

**Problem:** The Luma blast stage reports "success" but doesn't actually send a blast. Two root causes:

1. **Wrong manage URL.** The code navigates to `https://lu.ma/hh5k4ahp/manage/blasts` which shows the public event page, NOT the management page. The correct manage URL pattern is `https://luma.com/event/manage/evt-{EVENT_API_ID}`. The event API ID for this event is `evt-1Vwu5bQHAMd6hlw` (obtainable from `https://api.lu.ma/event/get?event_api_id=hh5k4ahp`).

2. **False success check.** The success check is `"blast" in final_snap.lower()` which is always true on any blast-related page, regardless of whether anything was sent.

**Verified working login flow (tested manually via playwright-cli):**
1. `goto https://lu.ma/signin` → page shows email textbox
2. `fill` email textbox with PLATFORM_EMAIL → click "Continue with Email"
3. Page shows password field (Luma supports password auth for this account)
4. `fill` password textbox with PLATFORM_PASSWORD → click "Continue"
5. Lands on home page (URL changes away from `/signin`). May show a "Create a Passkey" dialog — dismiss with Escape.

**Verified working blast flow (tested manually via playwright-cli):**
1. Navigate to `https://luma.com/event/manage/evt-1Vwu5bQHAMd6hlw` (NOT the `/hh5k4ahp/manage/blasts` URL)
2. Page shows manage tabs: Overview, Guests, Registration, **Blasts**, Insights, More
3. Click "Send a Blast" button (ref=e78)
4. Compose dialog opens with:
   - Recipients selector (ref=e332)
   - Subject field: `textbox "Subject (Optional)"` (ref=e349, placeholder: "New message in Unpossible Ralphathon")
   - Message field: contenteditable paragraph (ref=e360, placeholder: "Share a message with your guests…")
   - Send button (ref=e362)
5. Fill subject, fill message body (must include storefront URL), click Send
6. Verify send by checking for confirmation UI or checking the Blasts tab shows the sent blast with a timestamp

**Fix required:**
1. Get the event API ID by calling `https://api.lu.ma/event/get?event_api_id=hh5k4ahp` and extracting `event.api_id` (value: `evt-1Vwu5bQHAMd6hlw`)
2. After login, navigate to `https://luma.com/event/manage/{event_api_id}`
3. Click "Send a Blast" button
4. Fill the subject field and message body with a merch promotion + Fourthwall storefront URL
5. Click Send
6. Verify the blast actually sent — check for a confirmation message, or navigate to the Blasts tab and confirm the blast appears with a sent timestamp
7. The success check must NOT just look for generic keywords on the page

### BUG-002: Storefront behind password wall

**Severity:** High
**Stage:** 6 (Storefront)
**File:** `app/storefront.py`

**Problem:** The storefront URL (`https://unpossible-merch-shop.fourthwall.com`) redirects to `/password`, meaning the store is not publicly accessible. Visitors cannot see or buy the t-shirts.

**Fix required:**
1. During storefront setup, use playwright-cli to navigate to Fourthwall shop settings and disable the password protection / "coming soon" page.
2. Verify the storefront URL returns the actual store page (HTTP 200, no `/password` redirect) before marking the stage complete.

### BUG-003: Duplicate products on Fourthwall

**Severity:** Medium
**Stage:** 5 (Fourthwall upload)
**File:** `app/fourthwall.py`

**Problem:** There are 8 products on Fourthwall but only 6 unique designs — duplicates like "Ralph Loop Logo" appear 3 times and "Lobster Laptop" appears twice. This happened because the upload stage was retried without checking what already existed.

**Fix required:**
1. Before creating a new product, check the Fourthwall API (`GET /open-api/v1.0/products`) for existing products with the same name/slug.
2. Skip upload if a matching product already exists.
3. Optionally: clean up duplicate products via the Fourthwall UI before the next run.
