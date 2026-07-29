#!/bin/sh
# Mainline Wi-Fi SDIO bring-up helper.
# Boot: mmc-pwrseq asserts WL_REG_ON, waits 50 ms, then CMD5.
# Vendor aicbsp does NOT unbind the host — only mmc_detect_change().
# Prefer the sunxi-mmc "rescan" sysfs attr; fall back to unbind/bind.

set -u

klog() { echo "$1" > /dev/kmsg 2>/dev/null || true; echo "$1"; }

reg_by_name() {
	name="$1"
	for d in /sys/class/regulator/regulator.*; do
		[ -f "$d/name" ] || continue
		[ "$(cat "$d/name")" = "$name" ] || continue
		echo "$d"
		return 0
	done
	return 1
}

show_reg() {
	name="$1"
	d=$(reg_by_name "$name") || {
		klog "wifi-up: missing $name"
		return 1
	}
	klog "wifi-up: $name state=$(cat "$d/state" 2>/dev/null || echo ?) uV=$(cat "$d/microvolts" 2>/dev/null || echo ?)"
}

klog "wifi-up: start"

dump_pinctrl() {
	for d in /sys/kernel/debug/pinctrl/*; do
		[ -d "$d" ] || continue
		case "$d" in
			*/7022000.pinctrl|*/2000000.pinctrl|*/pinctrl-sun60i-a733)
				klog "wifi-up: pinctrl=$d"
				for f in pinmux-pins pinconf-pins; do
					[ -r "$d/$f" ] || continue
					klog "wifi-up: $f"
					grep -E 'PG[0-5]|mmc1|4021000' "$d/$f" || true
				done
				;;
		esac
	done
}

show_reg axp8191-bldo5 || true
show_reg axp8191-cldo1 || true
dump_pinctrl

# Read PIO_POW_MOD_SEL/CTL. A733 main PIO is at 0x02000000 (NOT CCU at
# 0x02002000). TYPE_4 POW_MOD lives at +0x40/+0x48. Also dump PG mux at
# bank base 0x380 to confirm mmc1 pinmux landed.
PIO_BASE=0x02000000
if command -v devmem >/dev/null 2>&1; then
	klog "wifi-up: PIO_POW_MOD_SEL@0x40 = $(devmem $((PIO_BASE + 0x40)) 32 2>/dev/null || echo ?)"
	klog "wifi-up: PIO_POW_MOD_CTL@0x48 = $(devmem $((PIO_BASE + 0x48)) 32 2>/dev/null || echo ?)"
	klog "wifi-up: PG_CFG0@0x380 = $(devmem $((PIO_BASE + 0x380)) 32 2>/dev/null || echo ?)"
else
	klog "wifi-up: devmem not available — install busybox/devmem to read PIO"
fi

if [ -d /sys/bus/sdio/devices ] && ls /sys/bus/sdio/devices 2>/dev/null | grep -q .; then
	klog "wifi-up: SDIO already present:"
	ls -la /sys/bus/sdio/devices/
	dmesg | grep -E 'a733-sdio|mmc1:|4021000|pwrseq' | tail -20 || true
	klog "wifi-up: done (already up)"
	exit 0
fi

# Soft rescan first (vendor sunxi_mmc_rescan_card → mmc_detect_change)
RESCAN=
for p in \
	/sys/devices/platform/soc/4021000.mmc/rescan \
	/sys/bus/platform/devices/4021000.mmc/rescan
do
	[ -w "$p" ] && RESCAN=$p && break
done

if [ -n "$RESCAN" ]; then
	klog "wifi-up: soft rescan via $RESCAN"
	echo 1 > "$RESCAN"
	sleep 1
elif [ -w /sys/kernel/debug/mmc1/force_rescan ]; then
	klog "wifi-up: soft rescan via debugfs force_rescan"
	echo 1 > /sys/kernel/debug/mmc1/force_rescan
	sleep 1
else
	klog "wifi-up: no soft-rescan node (need sunxi-mmc rescan attr)"
fi

if [ -d /sys/bus/sdio/devices ] && ls /sys/bus/sdio/devices 2>/dev/null | grep -q .; then
	klog "wifi-up: SDIO present after soft rescan"
	ls -la /sys/bus/sdio/devices/
	klog "wifi-up: done"
	exit 0
fi

klog "wifi-up: fallback unbind/bind 4021000.mmc (re-runs pwrseq; pulses REG_ON)"
echo 4021000.mmc > /sys/bus/platform/drivers/sunxi-mmc/unbind 2>/dev/null || true
sleep 0.2
echo 4021000.mmc > /sys/bus/platform/drivers/sunxi-mmc/bind 2>/dev/null || true
sleep 1

klog "wifi-up: mmc/sdio devices:"
ls -la /sys/bus/mmc/devices/ 2>/dev/null || true
ls -la /sys/bus/sdio/devices/ 2>/dev/null || true
dmesg | grep -E 'a733-sdio|mmc1:|4021000|pwrseq|SDIO' | tail -40 || true
klog "wifi-up: done"
