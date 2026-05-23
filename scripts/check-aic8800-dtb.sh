#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Usage: %s <linux-tree-root>\n' "$0" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINUX_ROOT="$1"

if [[ ! -d "$LINUX_ROOT/drivers" || ! -f "$LINUX_ROOT/Makefile" || ! -f "$LINUX_ROOT/Kconfig" ]]; then
  printf 'Not a full linux tree (expected drivers/, Makefile, Kconfig): %s\n' "$LINUX_ROOT" >&2
  exit 1
fi

cp "$ROOT_DIR/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts" \
  "$LINUX_ROOT/arch/arm64/boot/dts/allwinner/"
cp "$ROOT_DIR/arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi" \
  "$LINUX_ROOT/arch/arm64/boot/dts/allwinner/"
rsync -a "$ROOT_DIR/include/dt-bindings/" "$LINUX_ROOT/include/dt-bindings/"

make -C "$LINUX_ROOT" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
  allwinner/sun60i-a733-orangepi-4-pro.dtb

python3 - <<'PY' "$ROOT_DIR" "$LINUX_ROOT"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
linux_root = Path(sys.argv[2])
out = root / "docs" / "aic8800-dtb-check.json"
payload = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "linux_tree": str(linux_root),
    "target": "allwinner/sun60i-a733-orangepi-4-pro.dtb",
    "status": "pass",
}
out.write_text(json.dumps(payload, indent=2) + "\n")
PY

printf 'AIC8800 DTS/DTB check passed in %s\n' "$LINUX_ROOT"
