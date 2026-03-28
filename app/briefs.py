import json
from openai import OpenAI

from app.config import WANDB_API_KEY


def generate_briefs(event_data):
    """Generate 10 t-shirt design briefs from event data using W&B Inference API."""
    client = OpenAI(
        base_url="https://api.inference.wandb.ai/v1",
        api_key=WANDB_API_KEY,
    )

    prompt = _build_prompt(event_data)

    response = client.chat.completions.create(
        model="OpenPipe/Qwen3-14B-Instruct",
        messages=[
            {"role": "system", "content": "You are a creative t-shirt designer for tech hackathons. Return ONLY valid JSON, no other text."},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
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

    return f"""Generate exactly 10 t-shirt design briefs for the hackathon event below.

EVENT DETAILS:
- Name: {name}
- Date: {date}
- Description: {description}
- Sponsors: {', '.join(sponsors)}
- Speakers: {', '.join(speakers[:5])}
- Tags: {', '.join(tags)}

CATEGORIES (follow this distribution exactly):
- 4 briefs with category "crisp-simple": Minimalist, clean typography, event name, modern design
- 4 briefs with category "funny-meme": Ralph Wiggum references, lobster costume jokes, "don't touch your laptop" humor, AI agent jokes
- 2 briefs with category "sponsor-logo": NASCAR-style with sponsor names ({', '.join(sponsors)}) as creative typography (NOT actual logos)

DESIGN CONSTRAINTS:
- All designs are BLACK AND WHITE only
- Must be print-ready, high contrast
- Slogans should be short and punchy

Return a JSON array of exactly 10 objects, each with these fields:
- "id": string like "brief-01" through "brief-10"
- "title": short title for the design
- "category": one of "crisp-simple", "funny-meme", "sponsor-logo"
- "description": 2-3 sentence description of the visual design
- "slogans": array of 1-3 slogan strings for the design
- "color_notes": notes about the black and white treatment

Return ONLY the JSON array, no markdown formatting, no code blocks, no explanation."""


def _parse_briefs(raw_text):
    """Parse the LLM response into a list of brief dicts."""
    text = raw_text.strip()

    # Strip markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Handle think tags from Qwen models
    if "<think>" in text:
        # Extract content after </think>
        think_end = text.find("</think>")
        if think_end != -1:
            text = text[think_end + len("</think>"):].strip()

    # Strip markdown code blocks again (may appear after think tags)
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    briefs = json.loads(text)

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
