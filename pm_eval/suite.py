"""
CLI entry for binary evals. Checks live in pm_eval/checks_*.py; profiles in registry.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pm_eval.registry import CHECK_PROFILES, DEFAULT_PROFILE, evaluate, list_profiles

__all__ = ["evaluate", "list_profiles", "DEFAULT_PROFILE", "CHECK_PROFILES"]


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="Run binary eval suite on a markdown artifact.")
    p.add_argument("path", nargs="?", type=Path, help="Path to markdown file")
    p.add_argument(
        "--profile",
        "-p",
        default=DEFAULT_PROFILE,
        help=f"Artifact profile (default {DEFAULT_PROFILE}). Use --list-profiles.",
    )
    p.add_argument("--list-profiles", action="store_true", help="Print available profiles and exit")
    p.add_argument("--json", action="store_true", help="Print JSON only")
    args = p.parse_args()

    if args.list_profiles:
        print("Eval profiles:")
        for name in list_profiles():
            print(f"  - {name}")
        sys.exit(0)

    if args.path is None:
        p.error("path is required unless --list-profiles")
    text = args.path.read_text(encoding="utf-8")
    result = evaluate(text, profile=args.profile)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
