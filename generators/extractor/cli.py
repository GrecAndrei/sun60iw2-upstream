#!/usr/bin/env python3
"""
CLI tool for managing the Sunxi Semantic Extraction Engine.

Usage:
    python3 -m generators.extractor.cli status
    python3 -m generators.extractor.cli history
    python3 -m generators.extractor.cli learn --raw "..." --expected '{...}' --context clocks
    python3 -m generators.extractor.cli reset
"""

import json
import argparse
from pathlib import Path


def cmd_status(args):
    """Show semantic map status."""
    map_path = Path("generators/extractor/data/semantic_map.json")
    if not map_path.exists():
        print("No semantic map found. Run an extraction first.")
        return

    with open(map_path) as f:
        data = json.load(f)

    print("Semantic Map Status")
    print("=" * 40)
    print(f"Macros defined: {len(data.get('macros', {}))}")
    print(f"Types mapped: {len(data.get('types', {}))}")
    print(f"Validation rules: {len(data.get('validation_rules', []))}")
    print(f"Learned patterns: {len(data.get('learned_patterns', []))}")
    print(f"Vendor files processed: {len(data.get('vendor_history', {}))}")


def cmd_history(args):
    """Show vendor file processing history."""
    map_path = Path("generators/extractor/data/semantic_map.json")
    if not map_path.exists():
        print("No history found.")
        return

    with open(map_path) as f:
        data = json.load(f)

    history = data.get("vendor_history", {})
    if not history:
        print("No vendor files processed yet.")
        return

    print("Vendor File History")
    print("=" * 60)
    for filepath, info in history.items():
        print(f"\nFile: {filepath}")
        print(f"  Checksum: {info.get('checksum', 'N/A')}")
        stats = info.get("stats", {})
        for key, val in stats.items():
            print(f"  {key}: {val}")


def cmd_learn(args):
    """Manually teach the engine a pattern."""
    from generators.extractor import Engine

    engine = Engine()
    engine.learn(
        subsystem=args.context,
        raw_block=args.raw,
        expected=json.loads(args.expected),
    )
    print("Pattern learned and saved to semantic map.")


def cmd_reset(args):
    """Reset semantic map to defaults."""
    map_path = Path("generators/extractor/data/semantic_map.json")
    if map_path.exists():
        backup = map_path.with_suffix(".json.backup")
        map_path.rename(backup)
        print(f"Old map backed up to: {backup}")

    from generators.extractor import SemanticMap

    sm = SemanticMap()
    sm.save()
    print("Semantic map reset to defaults.")


def main():
    parser = argparse.ArgumentParser(description="SSEE Management CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Show semantic map status")
    subparsers.add_parser("history", help="Show vendor processing history")

    learn_parser = subparsers.add_parser("learn", help="Teach the engine a pattern")
    learn_parser.add_argument("--raw", required=True, help="Raw C block that failed")
    learn_parser.add_argument("--expected", required=True, help="Expected JSON output")
    learn_parser.add_argument("--context", default="clocks", help="Subsystem context")

    subparsers.add_parser("reset", help="Reset semantic map to defaults")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "learn":
        cmd_learn(args)
    elif args.command == "reset":
        cmd_reset(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
