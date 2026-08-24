#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
#
# Verify the A733's reachable Wi-Fi baseline through the pinned-key SSH path.

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PING_TARGET=${A733_PING_TARGET:-1.1.1.1}

usage() {
	cat <<'EOF'
Usage: a733-wifi-healthcheck.sh

Discovers the A733 through its pinned ED25519 host key, then verifies its
active Wi-Fi connection, single DHCP default route, late SMHC1 clock setting,
Internet reachability, and transport error counters.

Set A733_PING_TARGET to override the default 1.1.1.1 reachability target.
EOF
}

case ${1:-} in
"" ) ;;
-h|--help)
	usage
	exit 0
	;;
*)
	usage >&2
	exit 2
	;;
esac

"$SCRIPT_DIR/a733-ssh.sh" sh -s -- "$PING_TARGET" <<'REMOTE'
set -eu

ping_target=$1
stats=/sys/kernel/debug/aic8800_sdio/stats
clock_register=$(/usr/bin/devmem 0x02002d10 32)

fail()
{
	echo "A733 Wi-Fi health check: $*" >&2
	exit 1
}

status=$(wpa_cli -i wlan0 status)
printf '%s\n' "$status" | grep -qx 'wpa_state=COMPLETED' ||
	fail "wlan0 is not associated"

[ "$clock_register" = 0x81000003 ] ||
	fail "SMHC1 clock register is $clock_register, expected 0x81000003"

ip -4 addr show dev wlan0 | grep -q 'inet ' ||
	fail "wlan0 has no IPv4 lease"

default_routes=$(ip route show default dev wlan0 | wc -l)
[ "$default_routes" -eq 1 ] ||
	fail "expected one wlan0 default route, found $default_routes"

ping -c 3 -W 2 "$ping_target" >/dev/null ||
	fail "cannot reach $ping_target"

[ -r "$stats" ] || fail "missing AIC8800 debug statistics"
for key in rx_errors tx_errors tx_stall_events tx_recoveries tx_reinit_events \
	tx_drop_queue_full rx_drop_queue_full key_add_failures control_port_failures; do
	value=$(sed -n "s/^$key=//p" "$stats")
	[ "$value" = 0 ] || fail "$key=$value"
done

echo "A733 Wi-Fi health check: PASS"
uname -r
ip -br addr show wlan0
ip route show default dev wlan0
printf '%s\n' "$status" | grep -E '^(ssid|freq|wifi_generation|ieee80211ac|wpa_state)='
grep -E '^(rx_malformed|rx_decap_failures|tx_q_full|fw_active)=' "$stats"
REMOTE
