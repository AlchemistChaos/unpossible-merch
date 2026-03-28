import json
import os
import subprocess
import time

import weave

from app.config import LUMA_EVENT_URL


@weave.op()
def scrape_event(event_url=None):
    """Scrape event data from a Luma event page using playwright-cli."""
    url = event_url or LUMA_EVENT_URL
    try:
        event_data = _scrape_with_playwright(url)
        # Save scraped data
        os.makedirs("data", exist_ok=True)
        with open("data/scraped_event.json", "w") as f:
            json.dump(event_data, f, indent=2)
        return event_data
    except Exception as e:
        print(f"Scraping failed: {e}. Falling back to mock data.")
        return _load_fallback()


def _scrape_with_playwright(url):
    """Use playwright-cli to scrape the event page."""
    # Open the page
    subprocess.run(
        ["playwright-cli", "open", url],
        capture_output=True, text=True, timeout=30
    )

    # Wait for page to load
    time.sleep(3)

    # Get page text via eval
    result = subprocess.run(
        ["playwright-cli", "eval", "document.body.innerText"],
        capture_output=True, text=True, timeout=30
    )
    raw_output = result.stdout

    # Close browser
    subprocess.run(["playwright-cli", "close"], capture_output=True, text=True, timeout=10)

    # playwright-cli eval wraps output in markdown code blocks and JSON-escapes it
    # Extract the actual string content
    page_text = _clean_eval_output(raw_output)

    return _parse_event_data(page_text)


def _clean_eval_output(raw_output):
    """Clean playwright-cli eval output: remove markdown formatting and unescape JSON string."""
    text = raw_output.strip()
    # Remove markdown code block wrappers and header lines
    clean_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        # Skip markdown formatting lines
        if stripped.startswith("###") or stripped.startswith("```"):
            continue
        if stripped.startswith("await "):
            continue
        clean_lines.append(line)
    text = "\n".join(clean_lines).strip()
    # The content is a JSON-escaped string (quoted with \\n for newlines)
    # Try to parse it as JSON string first
    if text.startswith('"') and text.endswith('"'):
        try:
            text = json.loads(text)
        except json.JSONDecodeError:
            pass
    # Replace literal \\n with actual newlines
    text = text.replace("\\n", "\n")
    # Remove zero-width spaces
    text = text.replace("\u200b", "")
    text = text.replace("\u00a0", " ")
    return text


def _parse_event_data(page_text):
    """Parse event data from page text."""
    lines = page_text.strip().split("\n")
    lines = [l.strip() for l in lines if l.strip()]

    # Extract event name from heading in snapshot
    name = "Unpossible Ralphathon"
    for line in lines:
        if "Ralphathon" in line or "Ralphthon" in line:
            if len(line) < 80:
                name = line
                break

    # Extract date - look for day/month patterns
    date = ""
    for i, line in enumerate(lines):
        if ("Monday" in line or "Tuesday" in line or "Wednesday" in line or
                "Thursday" in line or "Friday" in line or "Saturday" in line or "Sunday" in line):
            date = line
            # Check if next line has time info
            if i + 1 < len(lines) and (":" in lines[i + 1] and ("AM" in lines[i + 1] or "PM" in lines[i + 1] or "Mar" in lines[i + 1])):
                date += " " + lines[i + 1]
            break
    if not date:
        for line in lines:
            if "March" in line or "Mar" in line:
                if len(line) < 60:
                    date = line
                    break

    # Extract location
    location = ""
    for line in lines:
        if "Address" in line or "Alabama" in line or "San Francisco" in line:
            location = line
            break
    if not location:
        location = "W&B Office, San Francisco, CA"

    # Extract description - grab text between "About Event" and "Prizes" or "Speakers"
    description_parts = []
    in_about = False
    for line in lines:
        if "About Event" in line:
            in_about = True
            continue
        if in_about:
            if any(heading in line for heading in ["Prizes", "Speakers", "Judges", "Schedule"]):
                break
            if line and len(line) > 10:
                description_parts.append(line)
    description = " ".join(description_parts[:5]) if description_parts else ""

    # Extract sponsors
    sponsors = []
    in_sponsors = False
    for line in lines:
        if "Sponsored by" in line:
            in_sponsors = True
            continue
        if in_sponsors:
            if any(heading in line for heading in ["OSS Partners", "Previous", "About", "Contact"]):
                break
            # Sponsor names are short lines
            clean = line.strip()
            if clean and len(clean) < 100 and not clean.startswith("is the"):
                sponsors.append(clean)
    # Add W&B if the long description line was skipped
    if sponsors and not any("Weights" in s or "W&B" in s for s in sponsors):
        sponsors.append("Weights & Biases")
    if not sponsors:
        sponsors = ["OpenAI", "Naver D2SF", "Hanriver Partners", "Kakao Ventures", "Bass Ventures", "Weights & Biases"]

    # Extract attendee types from speakers/judges sections
    speakers = []
    in_speakers = False
    for line in lines:
        if line.strip() == "Speakers":
            in_speakers = True
            continue
        if in_speakers:
            if any(heading in line for heading in ["Judges", "Schedule", "Sponsored"]):
                break
            if ":" in line or "—" in line or "-" in line:
                speakers.append(line.strip())

    judges = []
    in_judges = False
    for line in lines:
        if line.strip() == "Judges":
            in_judges = True
            continue
        if in_judges:
            if any(heading in line for heading in ["Schedule", "Sponsored", "Speakers"]):
                break
            if "—" in line or "-" in line or ":" in line:
                judges.append(line.strip())

    attendee_types = ["hackers", "speakers", "judges", "sponsors"]

    return {
        "name": name,
        "description": description,
        "date": date,
        "location": location,
        "sponsors": sponsors,
        "speakers": speakers[:10],
        "judges": judges[:15],
        "attendee_types": attendee_types,
        "source_url": "https://luma.com/hh5k4ahp",
        "tags": ["hackathon", "AI agents", "autonomous", "Ralph Loop", "lobster costume"]
    }


def _load_fallback():
    """Load fallback mock event data."""
    fallback_path = "data/events.json"
    if os.path.exists(fallback_path):
        with open(fallback_path) as f:
            events = json.load(f)
        # Return first event (Ralphthon)
        return events[0] if events else {}
    return {"name": "Ralphthon SF 2026", "description": "AI agent hackathon", "sponsors": []}


if __name__ == "__main__":
    data = scrape_event()
    print(json.dumps(data, indent=2))
