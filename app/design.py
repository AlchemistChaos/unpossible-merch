import os
import time
import json

import weave
from google import genai
from google.genai import types

from app.config import GOOGLE_API_KEY


@weave.op()
def generate_design(brief):
    """Generate a t-shirt design image from a brief using Gemini."""
    client = genai.Client(api_key=GOOGLE_API_KEY)

    prompt = _build_design_prompt(brief)

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

            os.makedirs("output", exist_ok=True)
            filename = f"{brief['id']}-{brief['category']}.png"
            filepath = os.path.join("output", filename)

            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    image.save(filepath)
                    print(f"  Saved: {filepath}")
                    return {"brief_id": brief["id"], "file": filepath, "status": "success"}

            print(f"  Warning: No image in response for {brief['id']}")
            return {"brief_id": brief["id"], "file": None, "status": "no_image"}

        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt + 1}/2 for {brief['id']}: {e}")
                time.sleep(3)
            else:
                print(f"  Failed after 3 attempts for {brief['id']}: {e}")
                return {"brief_id": brief["id"], "file": None, "status": f"error: {e}"}


def generate_all_designs(briefs):
    """Generate designs for all briefs with delays between calls."""
    results = []
    for i, brief in enumerate(briefs):
        print(f"Generating design {i + 1}/{len(briefs)}: {brief['title']}")
        result = generate_design(brief)
        results.append(result)
        if i < len(briefs) - 1:
            time.sleep(2)
    return results


def _build_design_prompt(brief):
    """Build the Gemini prompt for image generation."""
    slogans = ", ".join(brief.get("slogans", []))
    return f"""Create a t-shirt design graphic.

DESIGN: {brief['title']}
DESCRIPTION: {brief['description']}
SLOGANS: {slogans}
STYLE: {brief.get('color_notes', 'Black and white')}

REQUIREMENTS:
- Black and white only, high contrast
- Clean lines, print-ready quality
- White background, centered composition
- Bold, readable typography
- Suitable for screen printing on a t-shirt
- No photographic elements, graphic/illustration style only"""


if __name__ == "__main__":
    if os.path.exists("checkpoints/03-selected-briefs.json"):
        with open("checkpoints/03-selected-briefs.json") as f:
            briefs = json.load(f)
    else:
        briefs = [{"id": "test-01", "title": "Test Design", "category": "crisp-simple",
                    "description": "A simple test design", "slogans": ["Test"], "color_notes": "Black and white"}]

    # Test with just the first brief
    result = generate_design(briefs[0])
    print(f"Result: {result}")
