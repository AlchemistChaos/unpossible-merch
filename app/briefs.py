import json
import re

import weave
from openai import OpenAI

from app.config import WANDB_API_KEY


def _clean_llm_output(text):
    """Strip <think> tags and markdown code blocks from Qwen3 output."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = text.strip()
    code_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if code_match:
        text = code_match.group(1)
    return text.strip()


@weave.op()
def generate_briefs(event_data):
    """Generate 10 t-shirt design briefs from event data using W&B Inference API."""
    client = OpenAI(
        base_url="https://api.inference.wandb.ai/v1",
        api_key=WANDB_API_KEY,
    )

    prompt = _build_prompt(event_data)

    response = client.chat.completions.create(
        model="OpenPipe/Qwen3-14B-Instruct",
        messages=[{"role": "user", "content": prompt}],
    )

    raw = _clean_llm_output(response.choices[0].message.content)
    briefs = _parse_briefs(raw)
    return briefs


def _build_prompt(event_data):
    """Build the LLM prompt for generating design briefs."""
    name = event_data.get("name", "Ralphthon SF 2026")
    description = event_data.get("description", "")
    date = event_data.get("date", "")
    sponsors = event_data.get("sponsors", [])
    tags = event_data.get("tags", [])
    speakers = event_data.get("speakers", [])
    judges = event_data.get("judges", [])

    return f"""Generate exactly 5 t-shirt design briefs for the hackathon event below. These should be GENUINELY FUNNY — the kind of design that makes someone laugh and actually want to wear it.

EVENT DETAILS:
- Name: {name}
- Date: {date}
- Description: {description}
- Sponsors: {', '.join(sponsors)}
- Speakers: {', '.join(speakers[:5])}
- Judges: {', '.join(judges[:5])}
- Tags: {', '.join(tags)}

KEY EVENT HUMOR SOURCE MATERIAL:
- "If you want to touch your laptop, you put on a lobster costume first" (real rule at the event)
- Named after Ralph Wiggum from The Simpsons ("Me fail English? That's unpossible!")
- Teams set up AI agents to code autonomously, then humans go network while agents work
- Previous event in Seoul: people slept while their agents coded overnight
- Prizes include $10K in API credits

CATEGORIES — each has a distinct comedy voice:

2 briefs with category "crisp-simple" — NATE BARGATZE ENERGY:
  Deadpan wholesome absurdism. Say something completely ridiculous like it's totally normal.
  Minimalist typography, one killer deadpan line. The joke lands because it's so understated.
  Examples: "My computer's been working all day. I've been eating snacks." / "I don't know what my agent built but I'm presenting it in 20 minutes"

2 briefs with category "funny-meme" — MATT RIFE ENERGY:
  Crowd-work roast humor. Self-aware, riffs on the absurdity of hackathon culture.
  Bold graphic + roast-style text. Visual gags about the event.
  Examples: Roasting the lobster costume rule / "My AI agent has more commits than my entire team" / Ralph Wiggum references

1 brief with category "sponsor-logo" — HASAN MINHAJ ENERGY:
  Sharp cultural commentary on tech/VC hype. Sponsor names ({', '.join(sponsors)}) styled as NASCAR typography remixed as absurd fake products or startup pitches. NOT actual logos.
  Examples: "Raised $50M to let a robot write code I could've copy-pasted" / Sponsor names as fake VC-funded products

DESIGN CONSTRAINTS:
- All designs are BLACK AND WHITE only, high contrast, print-ready
- White background with black design elements
- The image is JUST the graphic/logo — NOT a t-shirt mockup, NOT a person wearing a shirt
- MUST include illustrated graphic elements (characters, icons, drawings) — not just plain text
- Be specific about visual layout and typography style
- Slogans should be short, punchy, and funny enough that someone would actually wear it in public

Return a JSON array of exactly 5 objects, each with these fields:
- "id": string like "brief-01" through "brief-05"
- "title": short creative title for the design
- "category": one of "crisp-simple", "funny-meme", "sponsor-logo"
- "description": detailed description of the visual design (2-3 sentences). Describe the GRAPHIC only, not a t-shirt. Be specific about visual layout and what illustrated elements to include.
- "slogans": array of 2-3 slogan strings for the design
- "color_notes": "Black and white, high contrast"

Return ONLY the JSON array, no other text."""


def _parse_briefs(raw_text):
    """Parse the LLM response into a list of brief dicts."""
    briefs = json.loads(raw_text)

    if not isinstance(briefs, list):
        raise ValueError(f"Expected a list, got {type(briefs)}")

    # Validate and normalize each brief
    required_fields = {"id", "title", "category", "description", "slogans", "color_notes"}
    valid_categories = {"crisp-simple", "funny-meme", "sponsor-logo"}

    for i, brief in enumerate(briefs):
        # Ensure all required fields exist
        for field in required_fields:
            if field not in brief:
                brief[field] = "" if field != "slogans" else []

        # Normalize category
        if brief["category"] not in valid_categories:
            brief["category"] = "crisp-simple"

        # Ensure slogans is a list
        if isinstance(brief["slogans"], str):
            brief["slogans"] = [brief["slogans"]]

        # Ensure id exists
        if not brief["id"]:
            brief["id"] = f"brief-{i+1:02d}"

    return briefs


if __name__ == "__main__":
    # Test with scraped data
    import os
    if os.path.exists("data/scraped_event.json"):
        with open("data/scraped_event.json") as f:
            event_data = json.load(f)
    else:
        event_data = {"name": "Ralphthon SF 2026", "description": "AI agent hackathon", "sponsors": ["OpenAI", "W&B"]}

    briefs = generate_briefs(event_data)
    print(f"Generated {len(briefs)} briefs:")
    for b in briefs:
        print(f"  [{b['category']}] {b['title']}: {b['slogans']}")
