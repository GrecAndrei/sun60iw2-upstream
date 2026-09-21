#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
#
# Promote a one-shot A733 OTA trial only after the board has rejoined Wi-Fi.

set -eu

BOOT=/boot
OTA=$BOOT/a733-ota
DTB=sun60i-a733-orangepi-4-pro.dtb
TIMEOUT=${A733_OTA_HEALTH_TIMEOUT:-150}
MARKER_DEVICE=/dev/mmcblk0
MARKER_PARTITION=/sys/class/block/mmcblk0/mmcblk0p1/start
MARKER_SECTOR=65520

log()
{
	echo "a733-ota-commit: $*" | systemd-cat -t a733-ota-commit 2>/dev/null || true
	echo "a733-ota-commit: $*" > /dev/kmsg 2>/dev/null || true
}

healthy()
{
	wpa_cli -i wlan0 status 2>/dev/null | grep -qx 'wpa_state=COMPLETED' || return 1
	ip -4 addr show dev wlan0 scope global 2>/dev/null | grep -q 'inet ' || return 1
	ip route show default dev wlan0 2>/dev/null | grep -q '^default ' || return 1
}

rollback()
{
	log "trial did not become healthy; rebooting into rollback set"
	sync
	systemctl reboot --message='A733 OTA trial health check failed' || reboot
}

clear_marker()
{
	[ "$(cat "$MARKER_PARTITION")" = 65536 ] || return 1
	dd if=/dev/zero of="$MARKER_DEVICE" bs=512 seek="$MARKER_SECTOR" count=1 \
		conv=fsync,notrunc status=none
}

promote()
{
	install -m 0644 "$OTA/trial/Image" "$BOOT/.Image.a733-ota-new"
	mv -f "$BOOT/.Image.a733-ota-new" "$BOOT/Image"

	for destination in "$BOOT/$DTB" "$BOOT/dtb/allwinner/$DTB"; do
		install -m 0644 "$OTA/trial/$DTB" "${destination}.a733-ota-new"
		mv -f "${destination}.a733-ota-new" "$destination"
	done

	clear_marker
	rm -f "$OTA/pending"
	sync
	log "trial promoted successfully"
}

case " $(cat /proc/cmdline 2>/dev/null) " in
*' a733.ota_rollback=1 '*)
	clear_marker
	rm -f "$OTA/pending"
	sync
	log "rollback boot completed; cleared failed trial state"
	exit 0
	;;
*' a733.ota_trial=1 '*) ;;
*)
	exit 0
	;;
esac

[ -f "$OTA/pending" ] || exit 0

log "waiting up to ${TIMEOUT}s for Wi-Fi health"
elapsed=0
while [ "$elapsed" -lt "$TIMEOUT" ]; do
	if healthy; then
		promote
		exit 0
	fi
	sleep 3
	elapsed=$((elapsed + 3))
done

rollback
