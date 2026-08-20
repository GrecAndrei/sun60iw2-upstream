#!/usr/bin/env python3
"""Generate the live project status document from the workspace itself.

The generated document deliberately reports only observable state: Git state,
build artifact metadata, Device Tree declarations, and factory-validation
output. It is not a replacement for hardware test logs.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
STATUS_PATH = ROOT / "docs" / "status.md"
TREES = {
    "source": ROOT,
    "integration": WORKSPACE / "kernels" / "a733-v7.1.3",
    "baseline": WORKSPACE / "kernels" / "mainline-v7",
    "debug": WORKSPACE / "kernels" / "a733-debug",
    "vendor": WORKSPACE / "references" / "orangepi-vendor-linux-6.6",
    "wiki": WORKSPACE / "projects" / "sun60iw2-upstream.wiki",
}


def command(args: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def display_path(path: Path) -> str:
    """Return a stable workspace-relative path for prose and status output."""
    try:
        return f"{path.relative_to(WORKSPACE).as_posix()}/"
    except ValueError:
        return str(path)


def git_snapshot(path: Path) -> dict[str, object]:
    if not (path / ".git").exists():
        return {"managed": False, "changes": []}

    _, revision = command(["git", "rev-parse", "--short", "HEAD"], path)
    _, branch = command(["git", "symbolic-ref", "--short", "-q", "HEAD"], path)
    _, subject = command(["git", "log", "-1", "--format=%s"], path)
    status_result = subprocess.run(
        ["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True
    )
    changes = []
    for line in status_result.stdout.splitlines():
        if not line:
            continue
        changed_path = line[3:]
        # Avoid the generated file being its own source of drift.
        if path == ROOT and changed_path == "docs/status.md":
            continue
        changes.append(f"{line[:2]} {changed_path}")
    return {
        "managed": True,
        "revision": revision,
        "branch": branch or "detached",
        "subject": subject,
        "changes": changes,
    }


def snapshot_state(snapshot: dict[str, object], *, include_revision: bool = True) -> str:
    if not snapshot["managed"]:
        return "missing or not a Git checkout"
    revision = f" at `{snapshot['revision']}`" if include_revision else ""
    return (
        f"`{snapshot['branch']}`{revision}; "
        f"{len(snapshot['changes'])} working-tree change(s)"
    )


def file_metadata(path: Path) -> str:
    if not path.exists():
        return "missing"
    stamp = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(
        timespec="minutes"
    )
    return f"{path.stat().st_size:,} bytes; modified {stamp}"


def contains(path: Path, marker: str) -> bool:
    return path.exists() and marker in path.read_text(errors="replace")


def node_enabled(path: Path, node: str) -> bool:
    if not path.exists():
        return False
    pattern = rf"&{re.escape(node)}\s*\{{.*?status\s*=\s*\"okay\";"
    return bool(re.search(pattern, path.read_text(errors="replace"), re.S))


def displayed_changes(snapshot: dict[str, object]) -> list[str]:
    """Hide documentation churn while retaining source and integration changes."""
    ignored = (
        "AGENTS.md",
        "README.md",
        ".gitignore",
        "docs/",
        "generated/",
        "generators/README.md",
        "scripts/refresh-documentation.py",
    )
    return [
        item
        for item in snapshot["changes"]
        if not item[3:].startswith(ignored)
    ]


def factory_snapshot() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "scripts/validate-factory.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    try:
        payload, _ = json.JSONDecoder().raw_decode(result.stdout.lstrip())
    except json.JSONDecodeError:
        return {
            "status": "ERROR",
            "detail": result.stdout.strip() or result.stderr.strip(),
            "failed": [],
        }
    return {
        "status": payload["status"],
        "passed": payload["passed"],
        "failed_count": payload["failed"],
        "total": payload["total"],
        "failed": [entry["name"] for entry in payload["checks"] if not entry["pass"]],
    }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def declaration_row(
    name: str,
    source: bool,
    integration: bool,
    debug: bool,
) -> str:
    return (
        f"| `{name}` | {yes_no(source)} | {yes_no(integration)} | "
        f"{yes_no(debug)} |"
    )


def render_snapshot() -> str:
    source = git_snapshot(TREES["source"])
    integration = git_snapshot(TREES["integration"])
    baseline = git_snapshot(TREES["baseline"])
    debug = git_snapshot(TREES["debug"])
    vendor = git_snapshot(TREES["vendor"])
    wiki = git_snapshot(TREES["wiki"])

    integration_tree = TREES["integration"]
    debug_tree = TREES["debug"]
    source_board = ROOT / "arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts"
    source_soc = ROOT / "arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi"
    source_opp = ROOT / "arch/arm64/boot/dts/allwinner/sun60i-a733-cpu-opp.dtsi"
    integration_board = (
        integration_tree
        / "arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts"
    )
    integration_soc = (
        integration_tree / "arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi"
    )
    integration_opp = (
        integration_tree
        / "arch/arm64/boot/dts/allwinner/sun60i-a733-cpu-opp.dtsi"
    )
    debug_board = (
        debug_tree / "arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts"
    )
    debug_soc = debug_tree / "arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi"
    debug_opp = (
        debug_tree / "arch/arm64/boot/dts/allwinner/sun60i-a733-cpu-opp.dtsi"
    )

    integration_image = integration_tree / "arch/arm64/boot/Image"
    integration_dtb = (
        integration_tree
        / "arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb"
    )
    debug_image = debug_tree / "arch/arm64/boot/Image"
    debug_dtb = (
        debug_tree
        / "arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb"
    )
    factory = factory_snapshot()

    declarations = [
        (
            "mmc1 enabled",
            node_enabled(source_board, "mmc1"),
            node_enabled(integration_board, "mmc1"),
            node_enabled(debug_board, "mmc1"),
        ),
        (
            "AXP8191 node (`x-powers,axp8191`)",
            contains(source_board, "x-powers,axp8191"),
            contains(integration_board, "x-powers,axp8191"),
            contains(debug_board, "x-powers,axp8191"),
        ),
        (
            "AXP DCDC3 (big CPU supply)",
            contains(source_board, "reg_dcdc3:")
            or contains(source_board, "dcdc3 {"),
            contains(integration_board, "reg_dcdc3:")
            or contains(integration_board, "dcdc3 {"),
            contains(debug_board, "reg_dcdc3:")
            or contains(debug_board, "dcdc3 {"),
        ),
        (
            "AXP DCDC5 (little CPU supply)",
            contains(source_board, "reg_dcdc5:")
            or contains(source_board, "dcdc5 {"),
            contains(integration_board, "reg_dcdc5:")
            or contains(integration_board, "dcdc5 {"),
            contains(debug_board, "reg_dcdc5:")
            or contains(debug_board, "dcdc5 {"),
        ),
        (
            "CPU OPP tables (`sun60i-a733-cpu-opp.dtsi`)",
            source_opp.exists()
            and contains(source_board, "sun60i-a733-cpu-opp.dtsi"),
            integration_opp.exists()
            and contains(integration_board, "sun60i-a733-cpu-opp.dtsi"),
            debug_opp.exists()
            and contains(debug_board, "sun60i-a733-cpu-opp.dtsi"),
        ),
        (
            "THS nvmem calibration wired",
            contains(source_soc, 'nvmem-cell-names = "calibration"'),
            contains(integration_soc, 'nvmem-cell-names = "calibration"'),
            contains(debug_soc, 'nvmem-cell-names = "calibration"'),
        ),
        (
            "CPU thermal zones (70/90 passive)",
            contains(source_soc, "cpu-l-thermal")
            and contains(source_soc, "temperature = <90000>"),
            contains(integration_soc, "cpu-l-thermal")
            and contains(integration_soc, "temperature = <90000>"),
            contains(debug_soc, "cpu-l-thermal")
            and contains(debug_soc, "temperature = <90000>"),
        ),
        (
            "R-TWI0 enabled",
            contains(source_board, "&s_twi0 {"),
            contains(integration_board, "&s_twi0 {"),
            contains(debug_board, "&s_twi0 {"),
        ),
        (
            "R-PIO PL supply declared",
            contains(source_board, "vcc-pl-supply"),
            contains(integration_board, "vcc-pl-supply"),
            contains(debug_board, "vcc-pl-supply"),
        ),
    ]

    source_state = (
        f"`{source['branch']}`"
        if source["managed"]
        else "missing or not a Git checkout"
    )

    lines = [
        "<!-- GENERATED: scripts/refresh-documentation.py; do not edit manually. -->",
        "# Live project state",
        "",
        "This is an evidence report generated from the workspace. It records source and artifact state, not hardware-success claims.",
        "",
        "Refresh with `python3 scripts/refresh-documentation.py`; verify with `python3 scripts/refresh-documentation.py --check`.",
        "",
        "## Workspace roles",
        "",
        "| Path | Role | Observable state |",
        "|---|---|---|",
        (
            f"| `{display_path(TREES['source'])}` | tracked source and generator "
            f"repository | {source_state}; source Git changes are intentionally "
            "omitted |"
        ),
        (
            f"| `{display_path(TREES['integration'])}` | primary integration "
            f"build (`a733-v7.1.3`) | {snapshot_state(integration)} |"
        ),
        (
            f"| `{display_path(TREES['baseline'])}` | Linux v7.0 comparison / "
            f"export tree | {snapshot_state(baseline)} |"
        ),
        (
            f"| `{display_path(TREES['debug'])}` | experimental worktree only | "
            f"{snapshot_state(debug)} |"
        ),
        (
            f"| `{display_path(TREES['vendor'])}` | vendor reference tree | "
            f"{snapshot_state(vendor)} |"
        ),
        (
            f"| `{display_path(TREES['wiki'])}` | canonical local wiki checkout | "
            f"{snapshot_state(wiki)} |"
        ),
        "",
        "The source checkout's revision and Git-change list are intentionally omitted: committing this generated file must not make it stale by changing the state it reports.",
        "",
        "## Generated-source validation",
        "",
    ]
    if factory["status"] == "ERROR":
        lines.append(f"- Validation could not be parsed: `{factory['detail']}`")
    else:
        lines.extend(
            [
                f"- Result: **{factory['status']}** — {factory['passed']}/{factory['total']} checks passed; {factory['failed_count']} failed.",
            ]
        )
        if factory["failed"]:
            lines.append("- Failing checks:")
            lines.extend(f"  - `{name}`" for name in factory["failed"])
    lines.extend(
        [
            "",
            "## Integration build artifacts (`a733-v7.1.3`)",
            "",
            (
                f"- `{display_path(integration_tree)}arch/arm64/boot/Image`: "
                f"{file_metadata(integration_image)}"
            ),
            (
                f"- `{display_path(integration_tree)}arch/arm64/boot/dts/allwinner/"
                f"sun60i-a733-orangepi-4-pro.dtb`: "
                f"{file_metadata(integration_dtb)}"
            ),
            "",
            "## Debug build artifacts (experimental)",
            "",
            (
                f"- `{display_path(debug_tree)}arch/arm64/boot/Image`: "
                f"{file_metadata(debug_image)}"
            ),
            (
                f"- `{display_path(debug_tree)}arch/arm64/boot/dts/allwinner/"
                f"sun60i-a733-orangepi-4-pro.dtb`: {file_metadata(debug_dtb)}"
            ),
            "- Artifact presence and timestamps only prove a local build output exists; they do not prove the image was booted successfully.",
            "",
            "## Current Device Tree declarations",
            "",
            "| Declaration | Source repository | Integration tree | Debug tree |",
            "|---|---:|---:|---:|",
            *(
                declaration_row(name, src, integ, dbg)
                for name, src, integ, dbg in declarations
            ),
            "",
            "These rows describe DTS text only. They do not establish driver availability, electrical behavior, or hardware success. Subsystem guides record validated runtime steps.",
            "",
            "## Uncommitted integration changes",
            "",
        ]
    )
    for label, snapshot in (
        ("Integration `a733-v7.1.3`", integration),
        ("Linux v7.0", baseline),
        ("Debug worktree", debug),
    ):
        lines.append(f"### {label}")
        visible = displayed_changes(snapshot)
        hidden = len(snapshot["changes"]) - len(visible)
        if visible:
            lines.extend(f"- `{item}`" for item in visible)
            if hidden:
                lines.append(
                    f"- {hidden} documentation or generated-artifact change(s) "
                    "omitted from this list."
                )
        else:
            lines.append(
                "- No source or integration changes outside documentation/"
                "generated artifacts."
            )
        lines.append("")
    lines.extend(
        [
            "## Documentation contract",
            "",
            "Permanent docs describe ownership, procedure, and the last recorded "
            "capability boundary. This generated file is the live evidence "
            "authority for Git/artifact/DTS/factory state; archived notes are "
            "intentionally excluded from current guidance.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if status.md is stale")
    args = parser.parse_args()

    expected = render_snapshot()
    current = STATUS_PATH.read_text() if STATUS_PATH.exists() else ""
    if args.check:
        if current == expected:
            print("Documentation status is current.")
            return 0
        print("Documentation status is stale. Run: python3 scripts/refresh-documentation.py")
        return 1

    STATUS_PATH.write_text(expected)
    print(f"Wrote {STATUS_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
