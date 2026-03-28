#!/usr/bin/env python
"""Run the Unpossible Merch t-shirt design pipeline."""
import argparse

import weave

from app.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Unpossible Merch - AI T-Shirt Design Pipeline")
    parser.add_argument("--clean", action="store_true", help="Clear checkpoints and start fresh")
    parser.add_argument("--event-url", type=str, default=None, help="Custom Luma event URL")
    parser.add_argument("--mock", action="store_true", help="Use mock data from data/events.json instead of scraping")
    parser.add_argument("--skip-blast", action="store_true", help="Skip sending the Luma blast to attendees")
    args = parser.parse_args()

    weave.init("saikolapudi-aws/tshirt-gen")
    run_pipeline(
        event_url=args.event_url,
        clean=args.clean,
        mock=args.mock,
        skip_blast=args.skip_blast,
    )


if __name__ == "__main__":
    main()
