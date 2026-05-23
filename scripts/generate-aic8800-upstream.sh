#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT_DIR/generators/generate_aic8800_upstream.py" "$@"

printf '%s\n' "Generated AIC8800 upstream draft artifacts:"
printf '%s\n' "- $ROOT_DIR/docs/upstream-drafts/aicsemi,aic8800.yaml"
printf '%s\n' "- $ROOT_DIR/docs/upstream-drafts/aicsemi,aic8800-bt.yaml"
printf '%s\n' "- $ROOT_DIR/docs/upstream-drafts/sun60i-a733-orangepi-4-pro-aic8800d80.dts.fragment"
printf '%s\n' "- $ROOT_DIR/docs/upstream-drafts/kernel-files/drivers/net/wireless/aicsemi/"
printf '%s\n' "- $ROOT_DIR/docs/upstream-drafts/kernel-files/drivers/bluetooth/hci_aic8800.c"
printf '%s\n' "- $ROOT_DIR/docs/aic8800d80-bsp-debt.csv"
