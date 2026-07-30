#!/bin/sh
# Run on the board from a733# as: sh /root/sdio-probe.sh
# Mimics vendor late-rescan without aicbsp: dump state, optional REG_ON
# toggle via unbind/bind of 4021000.mmc (re-runs mmc-pwrseq).

set -eu
LOG=/tmp/sdio-probe.log
exec >"$LOG" 2>&1
echo "=== a733 sdio probe $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

klog() { echo "$1" > /dev/kmsg 2>/dev/null || true; echo "$1"; }

klog "sdio-probe: start"

echo "--- mmc hosts ---"
ls -la /sys/class/mmc_host/ 2>/dev/null || true
for h in /sys/class/mmc_host/mmc*; do
	[ -e "$h" ] || continue
	echo "== $h =="
	ls -la "$h" 2>/dev/null || true
	[ -f "$h/uevent" ] && cat "$h/uevent"
done

echo "--- mmc devices ---"
ls -la /sys/bus/mmc/devices/ 2>/dev/null || true
dmesg 2>/dev/null | grep -E 'mmc1|pwrseq|a733-sdio|aic8800|BLDO5|CLDO1' | tail -80 || true

echo "--- regulators (name/voltage/state) ---"
for d in /sys/class/regulator/regulator.*; do
	[ -f "$d/name" ] || continue
	name=$(cat "$d/name")
	case "$name" in
	*bldo5*|*cldo1*|*axp8191-bldo5*|*axp8191-cldo1*|*vcc3v3_sd*)
		micro=
		[ -f "$d/microvolts" ] && micro=$(cat "$d/microvolts")
		state=
		[ -f "$d/state" ] && state=$(cat "$d/state")
		echo "$name microvolts=$micro state=$state"
		;;
	esac
done

echo "--- gpiochips / PM bank ---"
for c in /sys/class/gpio/gpiochip*; do
	[ -e "$c" ] || continue
	echo "$(basename "$c") base=$(cat "$c/base") ngpio=$(cat "$c/ngpio") label=$(cat "$c/label")"
done
# R_PIO PM1 is WL_REG_ON; label is usually 7022000.pinctrl or similar
for c in /sys/class/gpio/gpiochip*; do
	label=$(cat "$c/label" 2>/dev/null || true)
	case "$label" in
	*7022000*|*r-pinctrl*|*s_pio*|*R_PIO*)
		base=$(cat "$c/base")
		# PM1 = offset 1 within PM bank if chip is R_PIO starting at PM0
		echo "candidate r_pio chip $label base=$base (PM1 would be gpio $((base+1)) if PM0 is offset 0)"
		;;
	esac
done

echo "--- platform 4021000.mmc ---"
ls -la /sys/bus/platform/devices/4021000.mmc/ 2>/dev/null || true
ls -la /sys/bus/platform/drivers/sunxi-mmc/ 2>/dev/null | head -40 || true

DO_RESCAN=${1:-}
if [ "$DO_RESCAN" = "rescan" ]; then
	klog "sdio-probe: unbind 4021000.mmc"
	echo 4021000.mmc > /sys/bus/platform/drivers/sunxi-mmc/unbind || true
	sleep 1
	klog "sdio-probe: bind 4021000.mmc (pwrseq + scan)"
	echo 4021000.mmc > /sys/bus/platform/drivers/sunxi-mmc/bind || true
	sleep 2
	dmesg | grep -E 'mmc1|pwrseq|a733-sdio' | tail -40
	ls -la /sys/bus/mmc/devices/ 2>/dev/null || true
fi

echo "--- done; full log in $LOG ---"
klog "sdio-probe: done (log $LOG)"
cat "$LOG"
