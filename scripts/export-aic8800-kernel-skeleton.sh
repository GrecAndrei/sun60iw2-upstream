#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Usage: %s <linux-tree-root>\n' "$0" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINUX_ROOT="$1"
SRC="$ROOT_DIR/generated/aic8800/kernel-files"

if [[ ! -d "$LINUX_ROOT/drivers" || ! -f "$LINUX_ROOT/Makefile" || ! -f "$LINUX_ROOT/Kconfig" ]]; then
  printf 'Not a full linux tree (expected drivers/, Makefile, Kconfig): %s\n' "$LINUX_ROOT" >&2
  exit 1
fi

rsync -a "$SRC/" "$LINUX_ROOT/"

printf 'Exported generated AIC8800 kernel skeleton to %s\n' "$LINUX_ROOT"
