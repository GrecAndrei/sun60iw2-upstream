#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'Usage: %s <linux-tree-root>\n' "$0" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINUX_ROOT="$1"

"$ROOT_DIR/scripts/generate-aic8800-upstream.sh"
"$ROOT_DIR/scripts/export-aic8800-kernel-skeleton.sh" "$LINUX_ROOT"

make -C "$LINUX_ROOT" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M=drivers/net/wireless/aicsemi/aic8800 modules

if grep -q '^CONFIG_SERIAL_DEV_BUS=y' "$LINUX_ROOT/.config"; then
  make -C "$LINUX_ROOT" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/bluetooth/hci_aic8800.o
  export AIC8800_BT_CHECK="compiled"
else
  make -C "$LINUX_ROOT" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
    KCFLAGS=-DCONFIG_SERIAL_DEV_BUS=1 drivers/bluetooth/hci_aic8800.o
  export AIC8800_BT_CHECK="compiled with CONFIG_SERIAL_DEV_BUS test override"
fi

python3 - <<'PY' "$ROOT_DIR" "$LINUX_ROOT"
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
linux_root = Path(sys.argv[2])
out = root / ".tmp" / "validation" / "aic8800-compile-check.json"
out.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "linux_tree": str(linux_root),
    "status": "pass",
    "bluetooth_check": os.environ["AIC8800_BT_CHECK"],
}
out.write_text(json.dumps(payload, indent=2) + "\n")
PY

printf 'AIC8800 skeleton module compile check passed in %s\n' "$LINUX_ROOT"
