#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
#
# Apply the A733 SMHC1 clock setting after the AIC8800 runtime driver exists.
#
# The generated CCU model currently cannot resolve pll-ref during early boot,
# leaving SMHC1 on sys24M (12 MHz effective SDIO in 2x timing mode). The
# peripheral PLL is already configured by firmware. Switching SMHC1 to its
# 400 MHz output with a /4 module divider gives the requested 100 MHz module
# clock (50 MHz effective SDIO) without touching the PLL configuration.

set -eu

DEVMEM=${DEVMEM:-/usr/bin/devmem}
REG=0x02002d10
DEFAULT=0x80000000
TARGET=0x81000003

log()
{
	echo "a733-sdio-clock: $*" > /dev/kmsg 2>/dev/null || true
	echo "a733-sdio-clock: $*"
}

[ -x "$DEVMEM" ] || {
	log "missing devmem at $DEVMEM"
	exit 1
}

current=$($DEVMEM "$REG" 32)
case "$current" in
"$TARGET")
	log "SMHC1 already uses the 100 MHz module clock"
	exit 0
	;;
"$DEFAULT")
	$DEVMEM "$REG" 32 "$TARGET"
	actual=$($DEVMEM "$REG" 32)
	[ "$actual" = "$TARGET" ] || {
		log "SMHC1 clock readback is $actual, expected $TARGET"
		exit 1
	}
	log "SMHC1 switched to the 100 MHz module clock"
	;;
*)
	log "refusing unexpected SMHC1 register value $current"
	exit 1
	;;
esac
