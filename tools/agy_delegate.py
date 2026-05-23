#!/usr/bin/env python3
"""Headless delegation helper for local agy CLI.

Default behavior launches agy in background, stores logs in a directory, and
injects delegation environment context into every prompt.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from getpass import getuser
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Delegate a prompt to local agy in headless mode.",
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt text. If omitted, stdin is used.",
    )
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Read prompt text from a file.",
    )
    parser.add_argument(
        "--add-dir",
        action="append",
        default=[],
        help="Directory to add to agy workspace (repeatable).",
    )
    parser.add_argument(
        "--conversation",
        help="Resume a specific agy conversation ID.",
    )
    parser.add_argument(
        "--continue-last",
        action="store_true",
        help="Continue the most recent conversation.",
    )
    parser.add_argument(
        "--timeout",
        default="10m",
        help="agy print timeout (default: 10m).",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path(".tmp/agy-logs"),
        help="Directory where job logs/metadata are written.",
    )
    parser.add_argument(
        "--job-name",
        help="Optional human-friendly name used in log file names.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write agy response to this file (only in --wait mode).",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for completion (foreground mode). Default is background launch.",
    )
    parser.add_argument(
        "--sandbox",
        action="store_true",
        help="Run agy with --sandbox.",
    )
    parser.add_argument(
        "--skip-permissions",
        action="store_true",
        help="Pass --dangerously-skip-permissions to agy.",
    )
    return parser


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("No prompt provided. Use positional prompt, --prompt-file, or stdin.")


def build_env_prompt(user_prompt: str, args: argparse.Namespace) -> str:
    cwd = Path.cwd().resolve()
    add_dirs = [str(Path(p).resolve()) for p in args.add_dir]
    env_context = {
        "delegate": "OpenCode orchestration",
        "target_model": "local agy configured model (Gemini 3.5 Flash expected)",
        "hostname": socket.gethostname(),
        "user": getuser(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "cwd": str(cwd),
        "workspace_dirs": add_dirs,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    preamble = (
        "[DELEGATION ENV CONTEXT - REQUIRED]\n"
        "You are running as a delegated worker process for a local engineering "
        "workflow. Use the environment context below to scope your response. "
        "Prefer concise, actionable output.\n\n"
        "Environment:\n"
        f"{json.dumps(env_context, indent=2)}\n\n"
        "Output requirements:\n"
        "- Keep answers concise and technical.\n"
        "- If uncertain, state assumptions explicitly.\n"
        "- If asked for plans, provide phased steps and blockers.\n"
        "[/DELEGATION ENV CONTEXT]\n\n"
        "User task:\n"
    )
    return preamble + user_prompt


def make_job_id(args: argparse.Namespace) -> str:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    if args.job_name:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in args.job_name)
        safe = safe.strip("_") or "job"
        return f"{stamp}-{safe}-{suffix}"
    return f"{stamp}-{suffix}"


def build_command(agy_bin: str, prompt: str, args: argparse.Namespace, agy_log: Path) -> list[str]:
    cmd: list[str] = [
        agy_bin,
        "--print",
        prompt,
        "--print-timeout",
        args.timeout,
        "--log-file",
        str(agy_log),
    ]

    for add_dir in args.add_dir:
        cmd.extend(["--add-dir", add_dir])

    if args.conversation:
        cmd.extend(["--conversation", args.conversation])

    if args.continue_last:
        cmd.append("--continue")

    if args.sandbox:
        cmd.append("--sandbox")

    if args.skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    return cmd


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    agy_bin = shutil.which("agy")
    if not agy_bin:
        print("error: 'agy' not found in PATH", file=sys.stderr)
        return 127

    try:
        prompt = read_prompt(args).strip()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not prompt:
        print("error: prompt is empty", file=sys.stderr)
        return 2

    injected_prompt = build_env_prompt(prompt, args)
    job_id = make_job_id(args)
    log_dir = args.log_dir.resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = log_dir / f"{job_id}.out.log"
    stderr_log = log_dir / f"{job_id}.err.log"
    agy_cli_log = log_dir / f"{job_id}.agy.log"
    meta_log = log_dir / f"{job_id}.meta.json"

    cmd = build_command(agy_bin, injected_prompt, args, agy_cli_log)

    meta = {
        "job_id": job_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cwd": str(Path.cwd().resolve()),
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
        "agy_log": str(agy_cli_log),
        "command": cmd,
        "mode": "wait" if args.wait else "background",
        "prompt_preview": prompt[:300],
    }

    if args.wait:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        stdout_log.write_text(proc.stdout, encoding="utf-8")
        stderr_log.write_text(proc.stderr, encoding="utf-8")
        meta["returncode"] = proc.returncode
        meta_log.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        if args.output:
            args.output.write_text(proc.stdout, encoding="utf-8")
        else:
            sys.stdout.write(proc.stdout)

        if proc.returncode != 0 and proc.stderr:
            print(proc.stderr, file=sys.stderr, end="")
        return proc.returncode

    out_f = stdout_log.open("w", encoding="utf-8")
    err_f = stderr_log.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        cmd,
        stdout=out_f,
        stderr=err_f,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=os.environ.copy(),
    )
    out_f.close()
    err_f.close()

    meta["pid"] = proc.pid
    meta_log.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"launched background agy job: {job_id}")
    print(f"pid: {proc.pid}")
    print(f"meta: {meta_log}")
    print(f"stdout: {stdout_log}")
    print(f"stderr: {stderr_log}")
    print(f"agy-log: {agy_cli_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
