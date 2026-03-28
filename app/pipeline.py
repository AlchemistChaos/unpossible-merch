import json
import os
import shutil
import uuid
from datetime import datetime

import weave

from app.scrape_event import scrape_event
from app.briefs import generate_briefs
from app.critique import critique_briefs
from app.design import generate_all_designs
from app.quality_check import review_designs
from app.fourthwall import upload_designs
from app.storefront import setup_storefront
from app.luma_blast import send_blast
from app.config import LUMA_EVENT_URL


CHECKPOINTS_DIR = "checkpoints"
OUTPUT_DIR = "output"


@weave.op()
def run_pipeline(event_url=None, clean=False, mock=False, skip_blast=False):
    """Run the full t-shirt design pipeline with checkpoint recovery."""
    if clean:
        _clean_checkpoints()

    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)

    url = event_url or LUMA_EVENT_URL
    session_id = str(uuid.uuid4())[:8]
    run_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_output_dir = os.path.join(OUTPUT_DIR, f"run-{run_timestamp}")
    os.makedirs(run_output_dir, exist_ok=True)
    print(f"Output directory: {run_output_dir}")
    errors = []
    stages_completed = 0

    # Stage 1: Scrape event data
    print("=" * 50)
    print("STAGE 1: Scrape Event Data")
    print("=" * 50)
    if mock:
        event_data = _run_stage(
            checkpoint="01-event-data.json",
            fn=lambda: _load_mock_event(),
            label="loading mock data",
        )
    else:
        try:
            event_data = _run_stage(
                checkpoint="01-event-data.json",
                fn=lambda: scrape_event(url),
                label="event scraping",
            )
        except Exception as e:
            print(f"  ERROR: Stage 1 failed: {e}")
            errors.append(f"Stage 1 (scrape): {e}")
            event_data = _load_mock_event()
            print("  Falling back to mock data")
    stages_completed += 1

    event_name = event_data.get("name", "Unknown")
    print(f"  Session: {session_id} | Event: {event_name}")

    with weave.attributes({"session_id": session_id, "event_name": event_name, "event_url": url}):
        # Always regenerate briefs, images, and uploads (fresh each run)
        for cp in ["02-briefs.json", "03-selected-briefs.json", "04-images.json",
                    "05-fourthwall-products.json", "06-storefront.json"]:
            cp_path = os.path.join(CHECKPOINTS_DIR, cp)
            if os.path.exists(cp_path):
                os.remove(cp_path)

        # Stage 2: Generate 5 briefs
        print("\n" + "=" * 50)
        print("STAGE 2: Generate 5 Design Briefs")
        print("=" * 50)
        briefs = None
        try:
            briefs = _run_stage(
                checkpoint="02-briefs.json",
                fn=lambda: generate_briefs(event_data),
                label="brief generation",
            )
            stages_completed += 1
        except Exception as e:
            print(f"  ERROR: Stage 2 failed: {e}")
            errors.append(f"Stage 2 (briefs): {e}")

        # Stage 3: Critique and select best 3
        selected = None
        if briefs:
            print("\n" + "=" * 50)
            print("STAGE 3: Self-Critique -> Select Best 3 Briefs")
            print("=" * 50)
            try:
                selected = _run_stage(
                    checkpoint="03-selected-briefs.json",
                    fn=lambda: critique_briefs(briefs),
                    label="brief critique",
                )
                stages_completed += 1
            except Exception as e:
                print(f"  ERROR: Stage 3 failed: {e}")
                errors.append(f"Stage 3 (critique): {e}")

        # Stage 4: Generate images into run-specific output dir
        images = None
        if selected:
            print("\n" + "=" * 50)
            print("STAGE 4: Generate T-Shirt Designs")
            print("=" * 50)
            try:
                images = _run_stage(
                    checkpoint="04-images.json",
                    fn=lambda: generate_all_designs(selected, output_dir=run_output_dir),
                    label="image generation",
                )
                stages_completed += 1
            except Exception as e:
                print(f"  ERROR: Stage 4 failed: {e}")
                errors.append(f"Stage 4 (images): {e}")

        # Stage 4b: Quality check & regenerate weak designs
        if selected and images:
            print("\n" + "=" * 50)
            print("STAGE 4b: Quality Review & Regenerate")
            print("=" * 50)
            try:
                images = review_designs(selected, images)
                # Re-save the checkpoint with updated image paths
                cp_path = os.path.join(CHECKPOINTS_DIR, "04-images.json")
                with open(cp_path, "w") as f:
                    json.dump(images, f, indent=2)
                print("  Updated checkpoint: 04-images.json")
            except Exception as e:
                print(f"  ERROR: Quality review failed: {e}")
                errors.append(f"Stage 4b (quality): {e}")

        # Stage 5: Upload to Fourthwall
        fourthwall = None
        if selected and images:
            print("\n" + "=" * 50)
            print("STAGE 5: Upload Designs to Fourthwall")
            print("=" * 50)
            try:
                fourthwall = _run_stage(
                    checkpoint="05-fourthwall-products.json",
                    fn=lambda: upload_designs(selected, images),
                    label="Fourthwall upload",
                )
                stages_completed += 1
            except Exception as e:
                print(f"  ERROR: Stage 5 failed: {e}")
                errors.append(f"Stage 5 (Fourthwall): {e}")

        # Stage 6: Configure storefront
        storefront = None
        if fourthwall:
            print("\n" + "=" * 50)
            print("STAGE 6: Configure Fourthwall Storefront")
            print("=" * 50)
            try:
                storefront = _run_stage(
                    checkpoint="06-storefront.json",
                    fn=lambda: setup_storefront(event_data, fourthwall),
                    label="storefront setup",
                )
                stages_completed += 1
            except Exception as e:
                print(f"  ERROR: Stage 6 failed: {e}")
                errors.append(f"Stage 6 (storefront): {e}")

        # Stage 7: Send Luma blast
        blast = None
        if skip_blast:
            print("\n" + "=" * 50)
            print("STAGE 7: Send Luma Blast (SKIPPED)")
            print("=" * 50)
            blast = {"status": "skipped"}
        elif storefront:
            print("\n" + "=" * 50)
            print("STAGE 7: Send Luma Blast to Attendees")
            print("=" * 50)
            storefront_url = storefront.get("storefront_url", "")
            try:
                blast = _run_stage(
                    checkpoint="07-luma-blast.json",
                    fn=lambda: send_blast(url, storefront_url),
                    label="Luma blast",
                )
                stages_completed += 1
            except Exception as e:
                print(f"  ERROR: Stage 7 failed: {e}")
                errors.append(f"Stage 7 (blast): {e}")

    # Save results summary
    results = {
        "timestamp": datetime.now().isoformat(),
        "event_url": url,
        "event_name": event_name,
        "stages_completed": stages_completed,
        "total_stages": 7,
        "total_briefs_generated": len(briefs) if briefs else 0,
        "briefs_selected": len(selected) if selected else 0,
        "images_generated": sum(1 for img in (images or []) if img.get("status") == "success"),
        "images_failed": sum(1 for img in (images or []) if img.get("status") != "success"),
        "image_results": images or [],
        "fourthwall_products": (fourthwall or {}).get("successful", 0),
        "fourthwall_failed": (fourthwall or {}).get("failed", 0),
        "storefront_url": (storefront or {}).get("storefront_url", ""),
        "storefront_accessible": (storefront or {}).get("storefront_accessible", {}).get("status", "unknown"),
        "blast_status": (blast or {}).get("status", "unknown"),
        "blast_details": (blast or {}).get("blast_details", {}),
        "errors": errors,
        "mock": mock,
        "skip_blast": skip_blast,
    }
    results_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 50)
    print("PIPELINE SUMMARY")
    print("=" * 50)
    print(f"Event: {results['event_name']}")
    print(f"Stages completed: {results['stages_completed']}/{results['total_stages']}")
    print(f"Briefs generated: {results['total_briefs_generated']}")
    print(f"Briefs selected: {results['briefs_selected']}")
    print(f"Images generated: {results['images_generated']}")
    print(f"Images failed: {results['images_failed']}")
    print(f"Fourthwall products: {results['fourthwall_products']}")
    print(f"Fourthwall failed: {results['fourthwall_failed']}")
    print(f"Storefront URL: {results['storefront_url']}")
    print(f"Storefront accessible: {results['storefront_accessible']}")
    print(f"Blast sent: {results['blast_status']}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for err in errors:
            print(f"  - {err}")
    else:
        print("Errors: none")
    print(f"Results saved to: {results_path}")

    return results


def _load_mock_event():
    """Load mock event data from data/events.json."""
    fallback_path = "data/events.json"
    if os.path.exists(fallback_path):
        with open(fallback_path) as f:
            events = json.load(f)
        return events[0] if events else {}
    return {"name": "Ralphthon SF 2026", "description": "AI agent hackathon", "sponsors": []}


def _run_stage(checkpoint, fn, label):
    """Run a pipeline stage, loading from checkpoint if available."""
    cp_path = os.path.join(CHECKPOINTS_DIR, checkpoint)

    if os.path.exists(cp_path):
        print(f"  Loading from checkpoint: {checkpoint}")
        with open(cp_path) as f:
            return json.load(f)

    print(f"  Running {label}...")
    result = fn()

    with open(cp_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Saved checkpoint: {checkpoint}")

    return result


def _clean_checkpoints():
    """Remove all checkpoint files."""
    if os.path.exists(CHECKPOINTS_DIR):
        shutil.rmtree(CHECKPOINTS_DIR)
        print("Cleared checkpoints.")
