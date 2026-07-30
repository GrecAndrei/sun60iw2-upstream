#!/bin/sh
# Return wlan0 to managed mode and restart station userspace.
set -eu
IFACE=${IFACE:-wlan0}

iw dev "$IFACE" set type managed
ip link set "$IFACE" up
systemctl start "wpa_supplicant@${IFACE}.service" "dhcpcd@${IFACE}.service" \
	2>/dev/null || true
echo "station mode on $IFACE"
