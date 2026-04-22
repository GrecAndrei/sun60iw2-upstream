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
from generators.extractor import DEFAULT_ROOT_SOURCES


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
    root_sources = data.get("root_sources")
    if root_sources is None:
        root_sources = list(DEFAULT_ROOT_SOURCES)
    print(f"Root sources tracked: {len(root_sources)}")


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
        print(f"  Runs: {info.get('run_count', 1)}")
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


def cmd_extract(args):
    """Run extraction on a file or directory."""
    from generators.extractor import Engine

    engine = Engine()
    target = Path(args.input)
    if not target.exists():
        raise SystemExit(f"Input path does not exist: {target}")

    if target.is_dir():
        results = engine.batch.process_directory(
            target, args.subsystem, skip_unchanged=args.skip_unchanged
        )
        print(f"Processed files: {len(results)}")
        total_items = sum(len(r.items) for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        cached = sum(1 for r in results.values() if r.cached)
        print(f"Items extracted: {total_items}")
        print(f"Errors: {total_errors}")
        print(f"Warnings: {total_warnings}")
        print(f"Cached skips: {cached}")
        if args.output and args.export:
            merged = []
            for result in results.values():
                merged.extend(result.items)
            engine.export(merged, args.export, Path(args.output))
            print(f"Exported merged output to {args.output} ({args.export})")
        return

    result = engine.extract(
        args.subsystem,
        source_file=target,
        validate=args.validate,
        skip_unchanged=args.skip_unchanged,
    )
    print(engine.report(result))
    if args.output and args.export:
        engine.export(result.items, args.export, Path(args.output))
        print(f"Exported output to {args.output} ({args.export})")


def cmd_phase1_audit(args):
    """Run a focused Phase 1 bringup audit using SSEE."""
    from generators.extractor import Engine

    repo_root = Path(args.repo_root).resolve()
    dtsi = (
        repo_root / "arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi"
    )
    board_dts = (
        repo_root / "arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts"
    )
    ccu_driver = repo_root / "drivers/clk/sunxi-ng/ccu-sun60i-a733.c"
    clk_bindings = repo_root / "include/dt-bindings/clock/sun60i-a733-ccu.h"
    rst_bindings = repo_root / "include/dt-bindings/reset/sun60i-a733-ccu.h"

    engine = Engine()
    clocks = engine.extract("clocks", source_file=ccu_driver, validate=True)
    resets = engine.extract("resets", source_file=ccu_driver, validate=True)
    clk_ids = engine.extract("bindings", source_file=clk_bindings, validate=True)
    rst_ids = engine.extract("bindings", source_file=rst_bindings, validate=True)
    dtsi_nodes = engine.extract("dts", source_file=dtsi, validate=True) if dtsi.exists() else None
    board_nodes = engine.extract("dts", source_file=board_dts, validate=True) if board_dts.exists() else None
    dtsi_items = dtsi_nodes.items if dtsi_nodes else []
    board_items = board_nodes.items if board_nodes else []

    board_text = board_dts.read_text() if board_dts.exists() else ""
    dtsi_by_label = {item.get("label"): item for item in dtsi_items if item.get("label")}
    dtsi_by_node = {item.get("node"): item for item in dtsi_items}

    checks = [
        ("Base DTSI exists", dtsi.exists()),
        ("Board DTS exists", board_dts.exists()),
        ("CCU driver exists", ccu_driver.exists()),
        ('Board enables uart0 (`&uart0 { status = "okay"; }`)', '&uart0' in board_text and 'status = "okay"' in board_text),
        ('Board defines serial stdout-path', "stdout-path" in board_text and "serial0:" in board_text),
        ("SoC DTSI has CCU node", "clock-controller@2002000" in dtsi_by_node),
        ("SoC DTSI has main pinctrl node", "pinctrl@2000000" in dtsi_by_node),
        ("SoC DTSI has uart0 node", "uart0" in dtsi_by_label),
    ]

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)

    lines = [
        "# Phase 1 Audit Report (SSEE)",
        "",
        f"- Repo: `{repo_root}`",
        f"- Checks passed: **{passed}/{total}**",
        f"- Extracted clocks from CCU driver: **{len(clocks.items)}**",
        f"- Extracted resets from CCU driver: **{len(resets.items)}**",
        f"- Clock IDs from dt-bindings: **{len([x for x in clk_ids.items if x.get('domain') == 'clock'])}**",
        f"- Reset IDs from dt-bindings: **{len([x for x in rst_ids.items if x.get('domain') == 'reset'])}**",
        f"- Extracted DTSI nodes: **{len(dtsi_items)}**",
        f"- Extracted board DTS nodes: **{len(board_items)}**",
        "",
        "## Bringup Checklist",
    ]
    for name, ok in checks:
        lines.append(f"- [{'x' if ok else ' '}] {name}")

    lines.extend(
        [
            "",
            "## Extraction Validation",
            f"- CCU clock extraction errors: {len(clocks.errors)}",
            f"- CCU reset extraction errors: {len(resets.errors)}",
            f"- Clock bindings extraction errors: {len(clk_ids.errors)}",
            f"- Reset bindings extraction errors: {len(rst_ids.errors)}",
            f"- DTSI extraction errors: {len(dtsi_nodes.errors) if dtsi_nodes else 0}",
            f"- Board DTS extraction errors: {len(board_nodes.errors) if board_nodes else 0}",
        ]
    )

    report_text = "\n".join(lines) + "\n"
    print(report_text)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report_text)
        print(f"Audit report written: {out_path}")


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

    extract_parser = subparsers.add_parser(
        "extract", help="Extract subsystem data from file or directory"
    )
    extract_parser.add_argument(
        "--subsystem",
        required=True,
        choices=["clocks", "resets", "registers", "bindings", "dts"],
        help="Subsystem plugin to use",
    )
    extract_parser.add_argument(
        "--input", required=True, help="Input file or directory path"
    )
    extract_parser.add_argument(
        "--validate", action="store_true", help="Run plugin and semantic validation"
    )
    extract_parser.add_argument(
        "--skip-unchanged",
        action="store_true",
        help="Skip files whose checksum matches semantic-map history",
    )
    extract_parser.add_argument(
        "--export",
        choices=["json", "yaml", "csv", "markdown"],
        help="Export format for extracted items",
    )
    extract_parser.add_argument(
        "--output", help="Output path for exported data (required with --export)"
    )

    phase1_parser = subparsers.add_parser(
        "phase1-audit", help="Run Phase 1 bringup audit with SSEE"
    )
    phase1_parser.add_argument(
        "--repo-root", default=".", help="Repository root path (default: current dir)"
    )
    phase1_parser.add_argument(
        "--output", help="Optional markdown output path for the audit report"
    )

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "learn":
        cmd_learn(args)
    elif args.command == "reset":
        cmd_reset(args)
    elif args.command == "extract":
        if args.export and not args.output:
            raise SystemExit("--output is required when --export is provided")
        cmd_extract(args)
    elif args.command == "phase1-audit":
        cmd_phase1_audit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
