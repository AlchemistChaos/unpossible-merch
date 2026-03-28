"""Quality review generated t-shirt designs using Gemini vision and regenerate if needed."""

import json
import os
import time
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from PIL import Image

from app.config import GOOGLE_API_KEY


def _review_single(client, image_path: str, brief: dict) -> dict:
    """Use Gemini to review a single design image and score it 1-10."""
    img = Image.open(image_path)

    prompt = f"""You are a t-shirt design quality reviewer. Evaluate this design image.

DESIGN BRIEF:
- Title: {brief.get('title', '')}
- Category: {brief.get('category', '')}
- Description: {brief.get('description', '')}
- Main slogan: {brief.get('slogans', [''])[0]}

CRITERIA (score each pass/fail):
1. GRAPHIC ONLY: This is JUST the logo/graphic — NOT a t-shirt mockup, NOT a person wearing a shirt, NO fabric texture visible
2. CLEAN BACKGROUND: Background is plain white (no checkerboard patterns, no gradients, no texture)
3. TEXT READABLE: Any text in the design is legible, correctly spelled, and not garbled or duplicated
4. BLACK AND WHITE: Design uses only black and white (no color, no gray gradients)
5. NOT DUPLICATED: The graphic appears once, not repeated/mirrored side by side
6. HAS ILLUSTRATION: Contains at least one illustrated graphic element (icon, character, drawing) — not just plain text
7. FUNNY: The design is genuinely humorous — would someone actually want to wear this?

Score the overall design 1-10 (7+ is acceptable).

Respond with ONLY a JSON object:
{{"score": 1-10, "verdict": "accept" or "regenerate", "scores": {{"graphic_only": true/false, "transparent_bg": true/false, "text_readable": true/false, "black_ink_only": true/false, "not_duplicated": true/false, "has_illustration": true/false, "funny": true/false}}, "feedback": "specific issues to fix if regenerating"}}
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[prompt, img],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"],
        ),
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        result = {"score": 5, "verdict": "accept", "scores": {}, "feedback": f"Could not parse review: {text[:200]}"}

    # Override: score below 7 means regenerate
    if result.get("score", 10) < 7:
        result["verdict"] = "regenerate"

    return result


def _regenerate_design(client, brief: dict, feedback: str, output_dir: str) -> Optional[str]:
    """Regenerate a design with improved prompt based on critique feedback."""
    import re

    slogans = brief.get("slogans", [])
    slogan_text = slogans[0] if slogans else brief.get("title", "Hackathon")

    persona_guidance = {
        "crisp-simple": "Deadpan minimalist style. The humor is understated — one clean line that's quietly absurd.",
        "funny-meme": "Bold, in-your-face roast humor. Visual gag with punchy text. Make it loud and funny.",
        "sponsor-logo": "Sharp cultural commentary style. Typography-heavy, sponsor names remixed as absurd fake products.",
    }
    style = persona_guidance.get(brief.get("category", ""), "Bold and funny graphic design.")

    prompt = f"""Create a graphic design for screen printing on a t-shirt. A previous attempt was rejected:
"{feedback}"

FIX THOSE ISSUES. Here is the design brief:

DESIGN: {brief.get('title', '')}
CONCEPT: {brief.get('description', '')}
TEXT ON DESIGN: {slogan_text}

CRITICAL REQUIREMENTS:
- This is ONLY the graphic/logo — NOT a t-shirt mockup, NOT a person wearing a shirt
- Black and white ONLY — no color, no grayscale gradients
- White background with black design elements
- High contrast, clean bold lines suitable for screen printing
- Bold, readable typography — text must be legible at t-shirt scale
- Centered composition, standalone graphic — appears ONCE, not duplicated
- MUST include an illustrated graphic element (character, icon, drawing), not just text
- Illustration/graphic style only — no photographic elements
- Funny, clever, the kind of design that makes people laugh and want to wear it

COMEDY STYLE: {style}"""

    def _sanitize(title):
        name = title.lower().strip()
        name = re.sub(r"[^a-z0-9]+", "-", name)
        return name.strip("-")[:60]

    filename = f"{brief.get('id', 'design')}-{brief.get('category', 'design')}.png"
    filepath = os.path.join(output_dir, filename)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                image.save(filepath)
                print(f"    Regenerated: {filepath}")
                return filepath

        print(f"    Warning: No image in regeneration response for '{brief['title']}'")
        return None

    except Exception as e:
        print(f"    Regeneration error for '{brief['title']}': {e}")
        return None


def review_designs(briefs, image_results):
    """Review all generated designs and regenerate rejected ones.

    Args:
        briefs: List of selected brief dicts.
        image_results: List of image result dicts with 'brief_id', 'file', 'status'.

    Returns:
        Updated image_results list with regenerated paths where needed.
    """
    client = genai.Client(api_key=GOOGLE_API_KEY)
    output_dir = "output"
    updated_results = []

    # Build a map of brief_id -> brief
    brief_map = {b["id"]: b for b in briefs}

    for i, img in enumerate(image_results):
        brief_id = img.get("brief_id", "")
        brief = brief_map.get(brief_id, {})
        img_path = img.get("file", "")
        title = brief.get("title", brief_id)

        print(f"Reviewing {i + 1}/{len(image_results)}: {title}")

        if not img_path or not os.path.exists(img_path):
            print(f"  Skipped (no image file)")
            updated_results.append(img)
            continue

        review = _review_single(client, img_path, brief)
        score = review.get("score", 5)
        verdict = review.get("verdict", "accept")
        feedback = review.get("feedback", "")
        scores = review.get("scores", {})

        print(f"  Score: {score}/10 | Verdict: {verdict}")
        if feedback:
            print(f"  Feedback: {feedback}")

        if verdict == "accept":
            updated_results.append(img)
        else:
            print(f"  Regenerating...")
            time.sleep(2)
            new_path = _regenerate_design(client, brief, feedback, output_dir)
            if new_path:
                updated_results.append({
                    "brief_id": brief_id,
                    "file": new_path,
                    "status": "regenerated",
                })
            else:
                print(f"  Keeping original (regeneration failed)")
                updated_results.append(img)

        if i < len(image_results) - 1:
            time.sleep(2)

    accepted = sum(1 for r in updated_results if r.get("status") in ("success", "regenerated"))
    print(f"\nQuality review complete: {accepted}/{len(image_results)} designs accepted")
    return updated_results
