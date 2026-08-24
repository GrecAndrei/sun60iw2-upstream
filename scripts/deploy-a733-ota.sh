#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# Deploy a rebuilt A733 Image, board DTB, and AIC8800 modules over SSH.
# The target keeps running until --reboot is requested, so a failed transfer
# cannot leave it with a half-installed boot set.

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
KERNEL_DIR=${KERNEL_DIR:-"$PROJECT_DIR/../../kernels/a733-v7.1.3"}
HOST=${A733_HOST:-auto}
USER=${A733_USER:-root}
PORT=${A733_PORT:-22}
IDENTITY_FILE=${A733_IDENTITY_FILE:-"$HOME/.ssh/id_ed25519_a733"}
REBOOT=0
BUILD=0

usage() {
	cat <<'EOF'
Usage: deploy-a733-ota.sh [options]

Stage and verify the current A733 boot artifacts on the board, then atomically
replace its Image, DTB, and AIC8800 modules over SSH.

Options:
  --host HOST       Board address, or auto to discover its DHCP lease (default)
  --user USER       SSH user (default: A733_USER or root)
  --port PORT       SSH port (default: A733_PORT or 22)
  --build           Build Image/DTBs and regenerate+build the AIC8800 modules
  --reboot          Reboot after a successful install
  -h, --help        Show this help

The script deliberately never stores an SSH password. Configure an SSH key for
unattended updates; otherwise ssh/scp will prompt normally.
EOF
}

while (($#)); do
	case "$1" in
	--host)
		HOST=$2
		shift 2
		;;
	--user)
		USER=$2
		shift 2
		;;
	--port)
		PORT=$2
		shift 2
		;;
	--build)
		BUILD=1
		shift
		;;
	--reboot)
		REBOOT=1
		shift
		;;
	-h|--help)
		usage
		exit 0
		;;
	*)
		echo "unknown option: $1" >&2
		usage >&2
		exit 2
		;;
	esac
done

if ((BUILD)); then
	make -C "$KERNEL_DIR" -j"$(nproc)" ARCH=arm64 \
		CROSS_COMPILE=aarch64-linux-gnu- Image dtbs
	"$PROJECT_DIR/scripts/check-aic8800-skeleton.sh" "$KERNEL_DIR"
fi

IMAGE=$KERNEL_DIR/arch/arm64/boot/Image
DTB=$KERNEL_DIR/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb
CORE=$KERNEL_DIR/drivers/net/wireless/aicsemi/aic8800/aic8800_core.ko
SDIO=$KERNEL_DIR/drivers/net/wireless/aicsemi/aic8800/aic8800_sdio.ko
REL=$(<"$KERNEL_DIR/include/config/kernel.release")

for artifact in "$IMAGE" "$DTB" "$CORE" "$SDIO"; do
	[[ -f $artifact ]] || {
		echo "missing artifact: $artifact" >&2
		exit 1
	}
done

for module in "$CORE" "$SDIO"; do
	vermagic=$(modinfo -F vermagic "$module")
	[[ $vermagic == "$REL "* ]] || {
		echo "module/image release mismatch: ${module##*/}" >&2
		echo "  Image release:  $REL" >&2
		echo "  Module vermagic: $vermagic" >&2
		echo "Rebuild with --build before deploying." >&2
		exit 1
	}
done

if [[ $HOST == auto ]]; then
	HOST=$("$SCRIPT_DIR/find-a733-host.sh" --port "$PORT")
	echo "Discovered A733 at $HOST"
fi

SSH=(ssh -i "$IDENTITY_FILE" -o IdentitiesOnly=yes -p "$PORT" \
	-o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new)
SCP=(scp -i "$IDENTITY_FILE" -o IdentitiesOnly=yes -P "$PORT" \
	-o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new)
TARGET=$USER@$HOST
REMOTE_STAGE=/tmp/a733-ota-$REL-$$

cleanup() {
	"${SSH[@]}" "$TARGET" "rm -rf '$REMOTE_STAGE'" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Staging update on $TARGET"
"${SSH[@]}" "$TARGET" "umask 077 && mkdir -p '$REMOTE_STAGE'"
"${SCP[@]}" "$IMAGE" "$DTB" "$CORE" "$SDIO" "$TARGET:$REMOTE_STAGE/"

verify_remote() {
	local file=$1
	local expected actual

	expected=$(sha256sum "$file" | awk '{print $1}')
	actual=$("${SSH[@]}" "$TARGET" "sha256sum '$REMOTE_STAGE/${file##*/}'" |
		awk '{print $1}')
	[[ $expected == "$actual" ]] || {
		echo "checksum mismatch: ${file##*/}" >&2
		exit 1
	}
}

verify_remote "$IMAGE"
verify_remote "$DTB"
verify_remote "$CORE"
verify_remote "$SDIO"

echo "Checksums match; installing boot set"
"${SSH[@]}" "$TARGET" sh -s -- "$REMOTE_STAGE" "$REL" "$REBOOT" <<'REMOTE'
set -eu

stage=$1
release=$2
reboot_after=$3
dtb=sun60i-a733-orangepi-4-pro.dtb

install_atomic() {
	source=$1
	destination=$2
	directory=$(dirname "$destination")
	temporary=$directory/.${destination##*/}.new

	mkdir -p "$directory"
	install -m 0644 "$source" "$temporary"
	mv -f "$temporary" "$destination"
}

install_atomic "$stage/Image" /boot/Image
install_atomic "$stage/$dtb" "/boot/$dtb"
install_atomic "$stage/$dtb" "/boot/dtb/allwinner/$dtb"
for module_dir in "/lib/modules/$release/extra" /root/aic8800; do
	install_atomic "$stage/aic8800_core.ko" "$module_dir/aic8800_core.ko"
	install_atomic "$stage/aic8800_sdio.ko" "$module_dir/aic8800_sdio.ko"
done

if command -v depmod >/dev/null 2>&1; then
	depmod -a "$release"
fi
sync
echo "A733 OTA deployment complete: $release"

if [ "$reboot_after" = 1 ]; then
	systemctl reboot || reboot
fi
REMOTE

echo "Installed and verified $REL on $TARGET"
if ((REBOOT)); then
	echo "Reboot requested. Wait for the board to return before reconnecting."
else
	echo "Reboot when convenient, or rerun with --reboot."
fi
