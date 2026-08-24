#!/bin/sh
# AIC8800 SDIO Wi-Fi bring-up: load modules, wait for wlan0, bring it up.
set -u
klog() { echo "aic8800-wifi: $*" > /dev/kmsg 2>/dev/null || true; echo "aic8800-wifi: $*"; }
REL=$(uname -r)
MODDIR=
# Prefer modules matching the running kernel.  /root/aic8800 is a legacy
# fallback and must not shadow modules staged for an OTA trial.
for cand in "/lib/modules/$REL/extra" "/lib/modules/$REL/kernel/drivers/net/wireless/aicsemi/aic8800" /root/aic8800; do
	[ -f "$cand/aic8800_sdio.ko" ] && MODDIR=$cand && break
done
sdio_present() {
	[ -d /sys/bus/sdio/devices ] || return 1
	ls /sys/bus/sdio/devices 2>/dev/null | grep -q .
}
klog "start kernel=$REL"
i=0
while [ "$i" -lt 25 ]; do
	sdio_present && break
	if [ "$i" -eq 5 ] && [ -x /root/wifi-up.sh ]; then
		klog "no SDIO yet — /root/wifi-up.sh"
		/root/wifi-up.sh || true
	fi
	sleep 1
	i=$((i + 1))
done
modprobe cfg80211 2>/dev/null || true
if ! lsmod 2>/dev/null | grep -q '^aic8800_sdio'; then
	if [ -n "$MODDIR" ]; then
		# The card can retain an older duplicate in its normal kernel module
		# tree.  Load the selected pair directly so a fresh board install is
		# actually the module that reaches the hardware.
		klog "insmod pinned modules from $MODDIR"
		insmod "$MODDIR/aic8800_core.ko" 2>/dev/null || true
		insmod "$MODDIR/aic8800_sdio.ko" || { klog "insmod failed"; exit 1; }
	elif modprobe aic8800_sdio 2>/dev/null; then
		klog "modprobe aic8800_sdio fallback ok"
	else
		klog "ERROR: aic8800_sdio not found"
		exit 1
	fi
fi
i=0
while [ "$i" -lt 30 ]; do
	if [ -d /sys/class/net/wlan0 ]; then
		# The high SDIO clock is safe once runtime firmware has brought wlan0
		# into existence. Do not perform this write during MMC enumeration.
		if [ -x /usr/local/sbin/a733-sdio-clock.sh ]; then
			/usr/local/sbin/a733-sdio-clock.sh ||
				klog "WARNING: retained conservative SMHC1 clock"
		fi
		ip link set wlan0 up 2>/dev/null || true
		klog "wlan0 UP"
		ip -br link show wlan0 2>/dev/null || true
		exit 0
	fi
	sleep 1
	i=$((i + 1))
done
klog "ERROR: wlan0 missing"
dmesg 2>/dev/null | grep -iE 'aic8800|mmc1:|firmware|sdio|EPROBE' | tail -50 || true
exit 1
