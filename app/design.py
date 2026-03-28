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

    persona_guidance = {
        "crisp-simple": "Deadpan minimalist style. The humor is understated — one clean line that's quietly absurd.",
        "funny-meme": "Bold, in-your-face roast humor. Visual gag with punchy text. Make it loud and funny.",
        "sponsor-logo": "Sharp cultural commentary style. Typography-heavy, sponsor names remixed as absurd fake products.",
    }
    style = persona_guidance.get(brief.get("category", ""), "Bold and funny graphic design.")

    return f"""Create a graphic design for screen printing on a t-shirt.

DESIGN: {brief['title']}
CONCEPT: {brief['description']}
TEXT ON DESIGN: {slogans}

CRITICAL REQUIREMENTS:
- This is ONLY the graphic/logo — NOT a t-shirt mockup, NOT a person wearing a shirt
- Black ink only on a completely transparent/blank background
- PNG format, no background color at all
- High contrast, clean bold lines suitable for screen printing
- Bold, readable typography — text must be legible at t-shirt scale
- Centered composition, standalone graphic
- Illustration/graphic style only — no photographic elements
- Funny, clever, the kind of design that makes people laugh and want to wear it

COMEDY STYLE: {style}"""


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
