#!/bin/bash
# Swap the card's /boot to the vendor (5.15.147) kernel so we can boot the
# working vendor image and dump runtime registers (PIO_POW_MOD / SMHC1) for
# comparison with mainline. Restores cleanly via restore-mainline-boot.sh.
#
# Usage: sudo bash flash-vendor-for-dump.sh
set -euo pipefail

MNT=/mnt/sun60i-a733-rootfs
VENDOR_ROOTFS=/home/alex/Documents/porting/artifacts/rootfs/vendor-ubuntu-jammy
PART=/dev/mmcblk0p1
TS=$(date +%Y%m%d-%H%M%S)

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "Run with sudo (root)."
[[ -b "$PART" ]] || fail "$PART not found."
[[ -d "$VENDOR_ROOTFS/boot" ]] || fail "vendor rootfs boot/ not found at $VENDOR_ROOTFS/boot"

mkdir -p "$MNT"
mount "$PART" "$MNT"
trap 'sync; umount "$MNT" 2>/dev/null || true' EXIT

BK="$MNT/boot/mainline-backup"
echo "==> Refreshing mainline backup at $BK (so restore-mainline-boot.sh brings back the LATEST mainline)"
mkdir -p "$BK"
cp -a "$MNT/boot/Image"                              "$BK/Image"
cp -a "$MNT/boot/boot.cmd"                            "$BK/boot.cmd"
cp -a "$MNT/boot/boot.scr"                            "$BK/boot.scr"
cp -a "$MNT/boot/orangepiEnv.txt"                      "$BK/orangepiEnv.txt"
cp -a "$MNT/boot/sun60i-a733-orangepi-4-pro.dtb"       "$BK/sun60i-a733-orangepi-4-pro.dtb"
cp -a "$MNT/boot/sun60i-a733-orangepi-4-pro.dtb"       "$BK/dtb-allwinner-sun60i-a733-orangepi-4-pro.dtb"
mkdir -p "$BK/dtb/allwinner"
cp -a "$MNT/boot/dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb" \
        "$BK/dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb" 2>/dev/null || true

# Also keep a timestamped snapshot of the current /boot kernel/dtb/env, just in case.
echo "==> Snapshotting current /boot kernel/dtb/env -> /boot/mainline-snapshot-$TS"
mkdir -p "$MNT/boot/mainline-snapshot-$TS"
cp -a "$MNT/boot/Image"                              "$MNT/boot/mainline-snapshot-$TS/Image"
cp -a "$MNT/boot/boot.cmd"                           "$MNT/boot/mainline-snapshot-$TS/boot.cmd"
cp -a "$MNT/boot/boot.scr"                           "$MNT/boot/mainline-snapshot-$TS/boot.scr"
cp -a "$MNT/boot/orangepiEnv.txt"                     "$MNT/boot/mainline-snapshot-$TS/orangepiEnv.txt"
cp -a "$MNT/boot/sun60i-a733-orangepi-4-pro.dtb"      "$MNT/boot/mainline-snapshot-$TS/sun60i-a733-orangepi-4-pro.dtb"
cp -a "$MNT/boot/dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb" \
        "$MNT/boot/mainline-snapshot-$TS/dtb-allwinner-sun60i-a733-orangepi-4-pro.dtb" 2>/dev/null || true

echo "==> Installing vendor boot files"
VB="$VENDOR_ROOTFS/boot"
cp -a "$VB/uImage"      "$MNT/boot/uImage"
cp -a "$VB/uInitrd-5.15.147-sun60iw2" "$MNT/boot/uInitrd"
cp -a "$VB/boot.cmd"    "$MNT/boot/boot.cmd"
cp -a "$VB/boot.scr"    "$MNT/boot/boot.scr"

# Vendor orangepiEnv.txt uses rootdev=UUID=dc683cb4... which does NOT match
# this card's mmcblk0p1 UUID (6d825ed9...). Force rootdev to the block device
# so the vendor kernel can actually mount its rootfs.
#
# Also force console=serial (not "both") and bootlogo=false to prevent
# Plymouth/splash from grabbing the console, and add extraargs for
# initcall_debug + no_console_suspend so we can see where the kernel is
# if it hangs.  The vendor boot.cmd reads ${console}, ${bootlogo}, and
# ${extraargs} from this env file.
sed -e 's|^rootdev=.*|rootdev=/dev/mmcblk1p1|' \
    -e 's|^bootlogo=.*|bootlogo=false|' \
    "$VB/orangepiEnv.txt" > "$MNT/boot/orangepiEnv.txt"
# Ensure console=serial (serial-only, no tty1) and add debug extraargs.
# fsck.mode=skip is critical: the vendor initramfs ships e2fsck 1.46.5 which
# cannot handle FEATURE_C12 on our ext4 partition, so it would drop to a
# recovery shell every boot.  The kernel itself mounts the fs fine.
grep -q '^console=' "$MNT/boot/orangepiEnv.txt" || \
    echo 'console=serial' >> "$MNT/boot/orangepiEnv.txt"
grep -q '^extraargs=' "$MNT/boot/orangepiEnv.txt" || \
    echo 'extraargs=fsck.mode=skip initcall_debug no_console_suspend' >> "$MNT/boot/orangepiEnv.txt"

# Vendor dtb (214 KB, has the working SDIO/Wi-Fi nodes). The vendor boot.cmd
# loads ${prefix}dtb/${fdtfile} = dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb
VDTB="$VB/dtb-5.15.147-sun60iw2/allwinner/sun60i-a733-orangepi-4-pro.dtb"
mkdir -p "$MNT/boot/dtb/allwinner"
cp -a "$VDTB" "$MNT/boot/dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb"
cp -a "$VDTB" "$MNT/boot/sun60i-a733-orangepi-4-pro.dtb"

echo "==> Enabling passwordless root login on ttyS0 (clearing root password)"
# ttyS0 is already in /etc/securetty and serial-getty@ttyS0 is enabled.
sed -i 's|^root:[^:]*:|root::|' "$MNT/etc/shadow"

sync
echo
echo "VENDOR BOOT INSTALLED. Card now boots vendor 5.15.147 kernel."
echo "UART: ttyS0 @ 115200 (serial-getty@ttyS0). Login: root (no password)."
echo
echo "After booting, run on the board:"
cat <<'EOF'
  devmem 0x02002340 32   # PIO_POW_MOD_SEL
  devmem 0x02002344 32   # PIO_POW_MOD_CTL
  devmem 0x02002348 32   # GPIO_POW_VAL (auto-detect)
  devmem 0x04021000 32   # SMHC1 GCTRL
  devmem 0x04021004 32   # SMHC1 CLKCR
  devmem 0x0402105c 32   # SMHC1 NTSR
  devmem 0x04021140 32   # SMHC1 DRV_DL
  devmem 0x04021054 32   # SMHC1 CSDC
  devmem 0x0402110c 32   # SMHC1 EDSD
  dmesg | grep -iE 'mmc1|sunxi-mmc|aic|sdio' | head -40
  ls /sys/bus/sdio/devices/ 2>/dev/null
  ls /sys/bus/mmc/devices/ 2>/dev/null
EOF
echo
echo "When done, restore mainline with:  sudo bash restore-mainline-boot.sh"
echo "FLASH_VENDOR_OK"
