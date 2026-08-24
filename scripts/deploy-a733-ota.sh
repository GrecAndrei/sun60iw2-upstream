#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# Deploy a rebuilt A733 Image, board DTB, and AIC8800 modules over SSH.
# Kernel/DTB updates are one-shot trials: U-Boot records the attempt before
# booting them and automatically selects the retained boot set after a reset.

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
SELF_TEST=0

usage() {
	cat <<'EOF'
Usage: deploy-a733-ota.sh [options]

Stage and verify the current A733 boot artifacts on the board.  A new
Image/DTB is booted once from a trial directory and promoted only after it
rejoins Wi-Fi.  If the trial fails, the next boot automatically uses the
retained Image/DTB.

Options:
  --host HOST       Board address, or auto to discover its DHCP lease (default)
  --user USER       SSH user (default: A733_USER or root)
  --port PORT       SSH port (default: A733_PORT or 22)
  --build           Build Image/DTBs and regenerate+build the AIC8800 modules
  --self-test        Trial-boot the current known-good Image/DTB
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
	--self-test)
		SELF_TEST=1
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
	# Export first: it can make the integration tree dirty, which is part of
	# the kernel release string embedded in both Image and module vermagic.
	"$PROJECT_DIR/scripts/generate-aic8800-upstream.sh"
	"$PROJECT_DIR/scripts/export-aic8800-kernel-skeleton.sh" "$KERNEL_DIR"
	make -C "$KERNEL_DIR" -j"$(nproc)" ARCH=arm64 \
		CROSS_COMPILE=aarch64-linux-gnu- Image dtbs
	"$PROJECT_DIR/scripts/check-aic8800-skeleton.sh" "$KERNEL_DIR"
fi

if ((SELF_TEST && BUILD)); then
	echo "--self-test and --build cannot be used together" >&2
	exit 2
fi

IMAGE=$KERNEL_DIR/arch/arm64/boot/Image
DTB=$KERNEL_DIR/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb
CORE=$KERNEL_DIR/drivers/net/wireless/aicsemi/aic8800/aic8800_core.ko
SDIO=$KERNEL_DIR/drivers/net/wireless/aicsemi/aic8800/aic8800_sdio.ko
CLOCK_HELPER=$PROJECT_DIR/scripts/a733-sdio-clock.sh
WIFI_BRINGUP=$PROJECT_DIR/scripts/aic8800-wifi-bringup.sh
TRIAL_BOOT_CMD=$PROJECT_DIR/scripts/a733-ota-trial-boot.txt
TRIAL_COMMIT=$PROJECT_DIR/scripts/a733-ota-commit.sh
TRIAL_SERVICE=$PROJECT_DIR/scripts/a733-ota-commit.service
REL=$(<"$KERNEL_DIR/include/config/kernel.release")

for artifact in "$IMAGE" "$DTB" "$CORE" "$SDIO" "$CLOCK_HELPER" "$WIFI_BRINGUP" \
	"$TRIAL_BOOT_CMD" "$TRIAL_COMMIT" "$TRIAL_SERVICE"; do
	[[ -f $artifact ]] || {
		echo "missing artifact: $artifact" >&2
		exit 1
	}
done

command -v mkimage >/dev/null 2>&1 || {
	echo "mkimage is required to install the A733 OTA trial guard" >&2
	exit 1
}

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
LOCAL_STAGE=$(mktemp -d "${TMPDIR:-/tmp}/a733-ota.XXXXXX")

cleanup() {
	"${SSH[@]}" "$TARGET" "rm -rf '$REMOTE_STAGE'" >/dev/null 2>&1 || true
	rm -rf "$LOCAL_STAGE"
}
trap cleanup EXIT

echo "Staging update on $TARGET"
"${SCP[@]}" "$TARGET:/boot/boot.cmd" "$LOCAL_STAGE/boot.cmd.current"
awk '
BEGIN { inserted = 0; managed = 0 }
$0 == "# A733 OTA trial guard (managed by deploy-a733-ota.sh)" { managed = 1 }
$0 == "load ${devtype} ${devnum} ${kernel_addr_r} ${prefix}Image" {
	print "# A733 OTA trial guard (managed by deploy-a733-ota.sh)"
	print "if test -e ${devtype} ${devnum} ${prefix}a733-ota/boot.scr; then"
	print "\tif load ${devtype} ${devnum} ${load_addr} ${prefix}a733-ota/boot.scr; then"
	print "\t\tsource ${load_addr}"
	print "\tfi"
	print "fi"
	inserted = 1
}
{ print }
END {
	if (managed)
		exit 40
	if (!inserted)
		exit 41
}
' "$LOCAL_STAGE/boot.cmd.current" > "$LOCAL_STAGE/boot.cmd" || awk_status=$?
case ${awk_status:-0} in
0) ;;
40)
	cp "$LOCAL_STAGE/boot.cmd.current" "$LOCAL_STAGE/boot.cmd"
	;;
*)
	echo "unsupported /boot/boot.cmd; refusing to install OTA guard" >&2
	exit 1
	;;
esac
mkimage -C none -A arm -T script -d "$LOCAL_STAGE/boot.cmd" "$LOCAL_STAGE/boot.scr" >/dev/null
mkimage -C none -A arm -T script -d "$TRIAL_BOOT_CMD" "$LOCAL_STAGE/a733-ota-trial.scr" >/dev/null
"${SSH[@]}" "$TARGET" "umask 077 && mkdir -p '$REMOTE_STAGE'"
"${SCP[@]}" "$IMAGE" "$DTB" "$CORE" "$SDIO" "$CLOCK_HELPER" "$WIFI_BRINGUP" \
	"$TRIAL_COMMIT" "$TRIAL_SERVICE" "$LOCAL_STAGE/boot.cmd" "$LOCAL_STAGE/boot.scr" \
	"$LOCAL_STAGE/a733-ota-trial.scr" "$TARGET:$REMOTE_STAGE/"

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
verify_remote "$CLOCK_HELPER"
verify_remote "$WIFI_BRINGUP"
verify_remote "$TRIAL_COMMIT"
verify_remote "$TRIAL_SERVICE"
verify_remote "$LOCAL_STAGE/boot.cmd"
verify_remote "$LOCAL_STAGE/boot.scr"
verify_remote "$LOCAL_STAGE/a733-ota-trial.scr"

echo "Checksums match; staging one-shot boot trial"
"${SSH[@]}" "$TARGET" sh -s -- "$REMOTE_STAGE" "$REL" "$REBOOT" "$SELF_TEST" <<'REMOTE'
set -eu

stage=$1
release=$2
reboot_after=$3
self_test=$4
dtb=sun60i-a733-orangepi-4-pro.dtb
ota=/boot/a733-ota
marker_device=/dev/mmcblk0
marker_partition=/sys/class/block/mmcblk0/mmcblk0p1/start
marker_sector=65520

install_atomic() {
	source=$1
	destination=$2
	directory=$(dirname "$destination")
	temporary=$directory/.${destination##*/}.new

	mkdir -p "$directory"
	install -m 0644 "$source" "$temporary"
	mv -f "$temporary" "$destination"
}

read_marker() {
	dd if="$marker_device" bs=512 skip="$marker_sector" count=1 status=none |
		od -An -tu1 -N4 | tr -s ' ' | sed 's/^ //'
}

write_pending_marker() {
	marker_file="$ota/.raw-marker"
	dd if=/dev/zero of="$marker_file" bs=512 count=1 status=none
	printf '\247\063\001\132' | dd of="$marker_file" conv=notrunc status=none
	dd if="$marker_file" of="$marker_device" bs=512 seek="$marker_sector" count=1 \
		conv=fsync,notrunc status=none
	rm -f "$marker_file"
}

if [ -e "$ota/pending" ]; then
	echo "an A733 OTA trial is already pending; refusing to replace it" >&2
	exit 1
fi
[ "$(cat "$marker_partition")" = 65536 ] || {
	echo "unexpected A733 root partition start; refusing raw trial marker" >&2
	exit 1
}
[ "$(read_marker)" = '0 0 0 0' ] || {
	echo "raw A733 trial marker is not clear; refusing to replace it" >&2
	exit 1
}

install_atomic /boot/boot.cmd "$ota/rollback/boot.cmd"
install_atomic /boot/boot.scr "$ota/rollback/boot.scr"
install_atomic /boot/Image "$ota/rollback/Image"
install_atomic "/boot/dtb/allwinner/$dtb" "$ota/rollback/$dtb"
install_atomic "$stage/boot.cmd" /boot/boot.cmd
install_atomic "$stage/boot.scr" /boot/boot.scr
install_atomic "$stage/a733-ota-trial.scr" "$ota/boot.scr"

if [ "$self_test" = 1 ]; then
	install_atomic /boot/Image "$ota/trial/Image"
	install_atomic "/boot/dtb/allwinner/$dtb" "$ota/trial/$dtb"
else
	install_atomic "$stage/Image" "$ota/trial/Image"
	install_atomic "$stage/$dtb" "$ota/trial/$dtb"
fi

for module_dir in "/lib/modules/$release/extra"; do
	install_atomic "$stage/aic8800_core.ko" "$module_dir/aic8800_core.ko"
	install_atomic "$stage/aic8800_sdio.ko" "$module_dir/aic8800_sdio.ko"
done
install -m 0755 "$stage/a733-sdio-clock.sh" /usr/local/sbin/a733-sdio-clock.sh
install -m 0755 "$stage/aic8800-wifi-bringup.sh" /usr/local/sbin/aic8800-wifi-bringup.sh
install -m 0755 "$stage/a733-ota-commit.sh" /usr/local/sbin/a733-ota-commit.sh
install -m 0644 "$stage/a733-ota-commit.service" /etc/systemd/system/a733-ota-commit.service
systemctl daemon-reload
systemctl enable a733-ota-commit.service

if command -v depmod >/dev/null 2>&1; then
	depmod -a "$release"
fi
printf '1' > "$ota/pending"
if ! write_pending_marker; then
	rm -f "$ota/pending"
	echo "failed to write raw A733 trial marker" >&2
	exit 1
fi
sync
echo "A733 OTA trial staged: $release"

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
