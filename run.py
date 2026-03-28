#!/usr/bin/env python
"""Run the Unpossible Merch t-shirt design pipeline."""
import argparse

from app.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Unpossible Merch - AI T-Shirt Design Pipeline")
    parser.add_argument("--clean", action="store_true", help="Clear checkpoints and start fresh")
    args = parser.parse_args()

    run_pipeline(clean=args.clean)


if __name__ == "__main__":
    main()
