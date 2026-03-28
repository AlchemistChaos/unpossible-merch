import json
import os
import shutil
from datetime import datetime

from app.scrape_event import scrape_event
from app.briefs import generate_briefs
from app.critique import critique_briefs
from app.design import generate_all_designs
from app.config import LUMA_EVENT_URL


CHECKPOINTS_DIR = "checkpoints"
OUTPUT_DIR = "output"


def run_pipeline(event_url=None, clean=False):
    """Run the full t-shirt design pipeline with checkpoint recovery."""
    if clean:
        _clean_checkpoints()

    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    url = event_url or LUMA_EVENT_URL

    # Stage 1: Scrape event data
    print("=" * 50)
    print("STAGE 1: Scrape Event Data")
    print("=" * 50)
    event_data = _run_stage(
        checkpoint="01-event-data.json",
        fn=lambda: scrape_event(url),
        label="event scraping",
    )

    # Stage 2: Generate 10 briefs
    print("\n" + "=" * 50)
    print("STAGE 2: Generate 10 Design Briefs")
    print("=" * 50)
    briefs = _run_stage(
        checkpoint="02-briefs.json",
        fn=lambda: generate_briefs(event_data),
        label="brief generation",
    )

    # Stage 3: Critique and select 6
    print("\n" + "=" * 50)
    print("STAGE 3: Self-Critique → Select 6 Briefs")
    print("=" * 50)
    selected = _run_stage(
        checkpoint="03-selected-briefs.json",
        fn=lambda: critique_briefs(briefs),
        label="brief critique",
    )

    # Stage 4: Generate images
    print("\n" + "=" * 50)
    print("STAGE 4: Generate T-Shirt Designs")
    print("=" * 50)
    images = _run_stage(
        checkpoint="04-images.json",
        fn=lambda: generate_all_designs(selected),
        label="image generation",
    )

    # Save results summary
    results = {
        "timestamp": datetime.now().isoformat(),
        "event_url": url,
        "event_name": event_data.get("name", "Unknown"),
        "total_briefs_generated": len(briefs),
        "briefs_selected": len(selected),
        "images_generated": sum(1 for img in images if img.get("status") == "success"),
        "images_failed": sum(1 for img in images if img.get("status") != "success"),
        "image_results": images,
    }
    results_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)
    print(f"Event: {results['event_name']}")
    print(f"Briefs generated: {results['total_briefs_generated']}")
    print(f"Briefs selected: {results['briefs_selected']}")
    print(f"Images generated: {results['images_generated']}")
    print(f"Images failed: {results['images_failed']}")
    print(f"Results saved to: {results_path}")

    return results


def _run_stage(checkpoint, fn, label):
    """Run a pipeline stage, loading from checkpoint if available."""
    cp_path = os.path.join(CHECKPOINTS_DIR, checkpoint)

    if os.path.exists(cp_path):
        print(f"  ✓ Loading from checkpoint: {checkpoint}")
        with open(cp_path) as f:
            return json.load(f)

    print(f"  → Running {label}...")
    result = fn()

    with open(cp_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved checkpoint: {checkpoint}")

    return result


def _clean_checkpoints():
    """Remove all checkpoint files."""
    if os.path.exists(CHECKPOINTS_DIR):
        shutil.rmtree(CHECKPOINTS_DIR)
        print("Cleared checkpoints.")
