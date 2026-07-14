#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT_DIR/generators/report_aic8800_progress.py"

printf '%s\n' "Wrote progress snapshots:"
printf '%s\n' "- $ROOT_DIR/.tmp/validation/aic8800-progress.json"
printf '%s\n' "- $ROOT_DIR/.tmp/validation/aic8800-progress.md"
