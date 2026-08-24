#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Locate the A733 after a DHCP lease change by its pinned SSH host key.

set -euo pipefail

PORT=${A733_PORT:-22}
SUBNET=${A733_SUBNET:-}
FINGERPRINT=${A733_SSH_FINGERPRINT:-SHA256:f+y0FIeMZnYLRoRlpjLLDPFiZlDXFPWpiNljNuQxzvQ}

usage() {
	cat <<'EOF'
Usage: find-a733-host.sh [--port PORT] [--subnet CIDR] [--fingerprint SHA256:...]

Find the A733's current DHCP address on the local LAN. Candidates are accepted
only when their ED25519 SSH host-key fingerprint matches the pinned board key.

Environment overrides: A733_PORT, A733_SUBNET, A733_SSH_FINGERPRINT.
EOF
}

while (($#)); do
	case "$1" in
	--port)
		PORT=$2
		shift 2
		;;
	--subnet)
		SUBNET=$2
		shift 2
		;;
	--fingerprint)
		FINGERPRINT=$2
		shift 2
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

command -v nmap >/dev/null || {
	echo "nmap is required for automatic A733 discovery" >&2
	exit 1
}
command -v ssh-keyscan >/dev/null || {
	echo "ssh-keyscan is required for automatic A733 discovery" >&2
	exit 1
}

if [[ -z $SUBNET ]]; then
	DEFAULT_DEVICE=$(ip route get 1.1.1.1 2>/dev/null |
		awk '{ for (i = 1; i <= NF; i++) if ($i == "dev") { print $(i + 1); exit } }')
	[[ -n $DEFAULT_DEVICE ]] || {
		echo "cannot determine the LAN interface; set A733_SUBNET" >&2
		exit 1
	}
	SUBNET=$(ip -o -4 route show dev "$DEFAULT_DEVICE" scope link |
		awk '$1 ~ /\/[0-9]+$/ { print $1; exit }')
	[[ -n $SUBNET ]] || {
		echo "cannot determine the LAN subnet; set A733_SUBNET" >&2
		exit 1
	}
fi

mapfile -t CANDIDATES < <(
	nmap -n -p "$PORT" --open "$SUBNET" -oG - 2>/dev/null |
		awk '/Host: / && /Ports: [0-9]+\/open/ { print $2 }'
)

for candidate in "${CANDIDATES[@]}"; do
	candidate_fingerprint=$(ssh-keyscan -p "$PORT" -T 3 -t ed25519 "$candidate" \
		2>/dev/null | ssh-keygen -lf - 2>/dev/null | awk '{ print $2; exit }')
	if [[ $candidate_fingerprint == "$FINGERPRINT" ]]; then
		printf '%s\n' "$candidate"
		exit 0
	fi
done

echo "A733 not found on $SUBNET with host key $FINGERPRINT" >&2
exit 1
