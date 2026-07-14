#!/usr/bin/env python3
"""Emit AIC8800 upstream progress statistics."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def generated_files_stats(path: Path) -> dict:
    files = [p for p in path.rglob("*") if p.is_file()]
    by_ext = {}
    for f in files:
        ext = f.suffix or "<none>"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return {
        "total_files": len(files),
        "by_extension": dict(sorted(by_ext.items())),
    }


def agy_stats(log_dir: Path) -> dict:
    metas = sorted(log_dir.glob("*.meta.json"))
    out_nonempty = 0
    quota_hits = 0
    for meta_path in metas:
        meta = json.loads(meta_path.read_text())
        out_path = Path(meta["stdout_log"])
        agy_log = Path(meta.get("agy_log", ""))
        if out_path.exists() and out_path.read_text(errors="replace").strip():
            out_nonempty += 1
        if agy_log.exists() and "RESOURCE_EXHAUSTED" in agy_log.read_text(errors="replace"):
            quota_hits += 1
    return {
        "jobs_total": len(metas),
        "jobs_with_nonempty_stdout": out_nonempty,
        "jobs_with_quota_errors": quota_hits,
    }


def build_report() -> dict:
    generated = ROOT / "generated" / "aic8800"
    logs = ROOT / ".tmp" / "agy-logs"
    validation = ROOT / ".tmp" / "validation"
    compile_check = validation / "aic8800-compile-check.json"
    dtb_check = validation / "aic8800-dtb-check.json"

    compile_info = {
        "status": "not_run",
    }
    if compile_check.exists():
        compile_info = json.loads(compile_check.read_text())

    dtb_info = {
        "status": "not_run",
    }
    if dtb_check.exists():
        dtb_info = json.loads(dtb_check.read_text())

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_artifacts": generated_files_stats(generated),
        "compile_check": compile_info,
        "dtb_check": dtb_info,
        "agy_delegate": agy_stats(logs) if logs.exists() else {
            "jobs_total": 0,
            "jobs_with_nonempty_stdout": 0,
            "jobs_with_quota_errors": 0,
        },
    }


def write_outputs(report: dict) -> None:
    out_dir = ROOT / ".tmp" / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "aic8800-progress.json"
    out_md = out_dir / "aic8800-progress.md"

    out_json.write_text(json.dumps(report, indent=2) + "\n")

    md = [
        "# AIC8800 Local Validation Snapshot",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        "",
        "## Generated Artifacts",
        f"- Files in `generated/aic8800`: `{report['generated_artifacts']['total_files']}`",
        "",
        "## Compile Check",
        f"- Status: `{report['compile_check'].get('status', 'unknown')}`",
        f"- Last checked: `{report['compile_check'].get('checked_at_utc', 'n/a')}`",
        "",
        "## DTB Check",
        f"- Status: `{report['dtb_check'].get('status', 'unknown')}`",
        f"- Target: `{report['dtb_check'].get('target', 'n/a')}`",
        f"- Last checked: `{report['dtb_check'].get('checked_at_utc', 'n/a')}`",
        "",
        "## AGY Delegate",
        f"- Jobs total: `{report['agy_delegate']['jobs_total']}`",
        f"- Jobs with non-empty stdout: `{report['agy_delegate']['jobs_with_nonempty_stdout']}`",
        f"- Jobs with quota errors: `{report['agy_delegate']['jobs_with_quota_errors']}`",
        "",
        "## Generated File Extensions",
    ]
    for ext, count in report["generated_artifacts"]["by_extension"].items():
        md.append(f"- `{ext}`: `{count}`")

    out_md.write_text("\n".join(md) + "\n")


def main() -> None:
    report = build_report()
    write_outputs(report)


if __name__ == "__main__":
    main()
