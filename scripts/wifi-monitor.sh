#!/bin/sh
# Put wlan0 into monitor mode on a given channel (default 6).
# Stops station userspace first so it cannot fight the type change.
set -eu
IFACE=${IFACE:-wlan0}
CHAN=${1:-6}

systemctl stop "wpa_supplicant@${IFACE}.service" "dhcpcd@${IFACE}.service" \
	2>/dev/null || true

ip link set "$IFACE" up 2>/dev/null || true
iw dev "$IFACE" set type monitor
ip link set "$IFACE" up

if ! iw dev "$IFACE" set channel "$CHAN" 2>/dev/null; then
	# 2.4 GHz: freq = 2407 + 5 * chan (channels 1-13)
	freq=$((2407 + 5 * CHAN))
	iw dev "$IFACE" set freq "$freq"
fi

echo "monitor ready on $IFACE channel $CHAN"
echo "  tcpdump -i $IFACE -c 20 -n -e"
echo "  wifi-inject-probe.py $IFACE"
