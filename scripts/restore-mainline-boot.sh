#!/bin/bash
set -euo pipefail
MNT=/mnt/sun60i-a733-rootfs
BK="$MNT/boot/mainline-backup"
sudo mkdir -p "$MNT"
sudo mount /dev/mmcblk0p1 "$MNT"
sudo cp -a "$BK/Image" "$MNT/boot/Image"
sudo cp -a "$BK/sun60i-a733-orangepi-4-pro.dtb" "$MNT/boot/sun60i-a733-orangepi-4-pro.dtb"
sudo cp -a "$BK/dtb-allwinner-sun60i-a733-orangepi-4-pro.dtb" \
  "$MNT/boot/dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb"
sudo cp -a "$BK/boot.cmd" "$BK/boot.scr" "$BK/orangepiEnv.txt" "$MNT/boot/"
sync
sudo umount "$MNT"
echo RESTORED_MAINLINE_OK
