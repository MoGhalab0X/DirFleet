#!/usr/bin/env python3
import argparse
from core.engine import run_engine


def parse_args():
    p = argparse.ArgumentParser(
        description="DirFleet - multi-URL directory discovery engine"
    )
    p.add_argument("-i", "--input", required=True, help="File containing target URLs")
    p.add_argument("-o", "--output", required=True, help="Output directory")
    p.add_argument("--profile", default="default", help="Profile name")
    p.add_argument("--concurrency", type=int, default=3,
                   help="Number of concurrent base URLs (reserved)")
    p.add_argument("--backend", choices=["native", "ffuf"], default="native",
                   help="Scanning backend")
    p.add_argument("--verbose", action="store_true", help="Verbose mode")
    p.add_argument("--quiet", action="store_true", help="Quiet mode")
    return p.parse_args()


def main():
    args = parse_args()
    run_engine(args)


if __name__ == "__main__":
    main()
