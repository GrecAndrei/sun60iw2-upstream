#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-only
# Open an SSH session to the A733, locating its current DHCP lease first.

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
USER=${A733_USER:-root}
PORT=${A733_PORT:-22}
IDENTITY_FILE=${A733_IDENTITY_FILE:-"$HOME/.ssh/id_ed25519_a733"}

[[ -f $IDENTITY_FILE ]] || {
	echo "A733 SSH identity not found: $IDENTITY_FILE" >&2
	echo "Set A733_IDENTITY_FILE to the board's private key." >&2
	exit 1
}

HOST=$("$SCRIPT_DIR/find-a733-host.sh" --port "$PORT")
echo "Connecting to A733 at $HOST" >&2
exec ssh -i "$IDENTITY_FILE" -o IdentitiesOnly=yes -p "$PORT" \
	-o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new "$USER@$HOST" "$@"
