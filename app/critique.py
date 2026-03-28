import json

import weave
from openai import OpenAI

from app.config import WANDB_API_KEY


@weave.op()
def critique_briefs(briefs):
    """Evaluate 10 briefs and select the best 6 with critique notes."""
    client = OpenAI(
        base_url="https://api.inference.wandb.ai/v1",
        api_key=WANDB_API_KEY,
    )

    prompt = _build_critique_prompt(briefs)

    response = client.chat.completions.create(
        model="OpenPipe/Qwen3-14B-Instruct",
        messages=[
            {"role": "system", "content": "You are a senior creative director evaluating t-shirt designs for a tech hackathon. Return ONLY valid JSON, no other text."},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content.strip()
    selected = _parse_critique(raw, briefs)
    return selected


def _build_critique_prompt(briefs):
    """Build the LLM prompt for critiquing briefs."""
    briefs_json = json.dumps(briefs, indent=2)

    return f"""You are evaluating 10 t-shirt design briefs for a hackathon event. Your job is to select the BEST 3 designs.

HERE ARE THE 10 BRIEFS:
{briefs_json}

EVALUATION CRITERIA (score each 1-10):
1. **Printability**: Will this look good as a black & white print on a t-shirt? Clean lines, high contrast, readable text?
2. **Relevance**: Does it capture the event's spirit (AI agents, hackathon culture, Ralph Wiggum humor)?
3. **Variety**: Does it add something unique compared to other selected designs?
4. **Humor/Appeal**: Would attendees actually want to wear this?

SELECTION RULES:
- Select exactly 3 briefs
- Aim for ~2 from each category (crisp-simple, funny-meme, sponsor-logo), but prioritize quality over quota
- Drop the weakest designs regardless of category

Return a JSON array of exactly 3 objects. Each object should be the ORIGINAL brief with one added field:
- "critique_notes": A string with 1-2 sentences explaining why this brief was selected and any improvements suggested

Return ONLY the JSON array, no markdown formatting, no code blocks, no explanation."""


def _parse_critique(raw_text, original_briefs):
    """Parse the LLM critique response into a list of selected brief dicts."""
    text = raw_text.strip()

    # Strip markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    # Handle think tags from Qwen models
    if "<think>" in text:
        think_end = text.find("</think>")
        if think_end != -1:
            text = text[think_end + len("</think>"):].strip()

    # Strip markdown code blocks again (may appear after think tags)
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    selected = json.loads(text)

    if not isinstance(selected, list):
        raise ValueError(f"Expected a list, got {type(selected)}")

    # Ensure critique_notes field exists on each
    for brief in selected:
        if "critique_notes" not in brief:
            brief["critique_notes"] = "Selected as a strong design."

    # If LLM returned more or fewer than 6, adjust
    if len(selected) > 3:
        selected = selected[:3]
    elif len(selected) < 3:
        # Fill from originals that weren't selected
        selected_ids = {b.get("id") for b in selected}
        for b in original_briefs:
            if b.get("id") not in selected_ids and len(selected) < 3:
                b["critique_notes"] = "Added to fill selection quota."
                selected.append(b)

    return selected


if __name__ == "__main__":
    import os
    # Load briefs from checkpoint or generate test data
    if os.path.exists("checkpoints/02-briefs.json"):
        with open("checkpoints/02-briefs.json") as f:
            briefs = json.load(f)
    else:
        # Minimal test briefs
        briefs = [
            {"id": f"brief-{i+1:02d}", "title": f"Test Brief {i+1}",
             "category": ["crisp-simple", "funny-meme", "sponsor-logo"][i % 3],
             "description": f"Test design {i+1}", "slogans": [f"Slogan {i+1}"],
             "color_notes": "Black and white"}
            for i in range(10)
        ]

    selected = critique_briefs(briefs)
    print(f"Selected {len(selected)} briefs:")
    for b in selected:
        print(f"  [{b['category']}] {b['title']}: {b.get('critique_notes', 'N/A')}")
