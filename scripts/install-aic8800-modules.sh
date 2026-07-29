#!/bin/bash
# Install rebuilt AIC8800 modules + firmware + Image onto the SD card.
set -euo pipefail
MNT=${MNT:-/mnt/sun60i-a733-rootfs}
PART=${PART:-/dev/mmcblk0p1}
STAGING=/home/alex/Documents/porting/artifacts/aic8800-board-install
IMG=/home/alex/Documents/porting/kernels/a733-v7.1.3/arch/arm64/boot/Image
[[ $EUID -eq 0 ]] || exec sudo -S -p '' bash "$0" "$@"
[[ -b $PART ]] || { echo "no $PART"; exit 1; }
mkdir -p "$MNT"
mount "$PART" "$MNT"
trap 'sync; umount "$MNT" 2>/dev/null || true' EXIT
REL=$(cat /home/alex/Documents/porting/kernels/a733-v7.1.3/include/config/kernel.release)
mkdir -p "$MNT/lib/modules/$REL/extra" "$MNT/lib/firmware/aic8800d80"
cp -a "$STAGING/lib/modules/$REL/extra/"*.ko "$MNT/lib/modules/$REL/extra/"
cp -a "$STAGING/lib/firmware/aic8800d80/"* "$MNT/lib/firmware/aic8800d80/"
cp -a "$IMG" "$MNT/boot/Image"
cp -a "$IMG" "$MNT/boot/mainline-backup/Image" 2>/dev/null || true
# depmod if available for this arch; otherwise board runs insmod manually
if command -v depmod >/dev/null 2>&1; then
  depmod -b "$MNT" "$REL" 2>/dev/null || true
fi
cat > "$MNT/root/aic-load.sh" <<EOS
#!/bin/sh
set -e
REL=\$(uname -r)
modprobe cfg80211 2>/dev/null || true
insmod /lib/modules/\$REL/extra/aic8800_core.ko
insmod /lib/modules/\$REL/extra/aic8800_sdio.ko
dmesg | grep -iE 'aic8800|sdio|wlan' | tail -40
ls /sys/bus/sdio/devices/
ip link show 2>/dev/null | grep -i wlan || true
EOS
chmod +x "$MNT/root/aic-load.sh"
echo "Installed modules for \$REL=$REL"
echo "On board: /root/aic-load.sh"
echo INSTALL_AIC_OK
