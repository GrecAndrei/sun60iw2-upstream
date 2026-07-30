#!/bin/bash
# Install rebuilt AIC8800 modules + firmware + Image onto the SD card,
# restore systemd as PID 1, and enable automatic Wi-Fi bring-up on boot.
set -euo pipefail

MNT=${MNT:-/mnt/sun60i-a733-rootfs}
PART=${PART:-/dev/mmcblk0p1}
STAGING=/home/alex/Documents/porting/artifacts/aic8800-board-install
K=/home/alex/Documents/porting/kernels/a733-v7.1.3
IMG=$K/arch/arm64/boot/Image
DTB=$K/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SKIP_MOUNT=${SKIP_MOUNT:-0}
LOOP_FALLBACK=${LOOP_FALLBACK:-1}

[[ $EUID -eq 0 ]] || exec sudo -p '' bash "$0" "$@"
[[ -f $IMG ]] || { echo "no $IMG"; exit 1; }

cleanup() {
	sync
	if [[ ${DID_MOUNT:-0} -eq 1 ]]; then
		umount "$MNT" 2>/dev/null || true
	fi
	if [[ -n ${LOOPDEV:-} ]]; then
		losetup -d "$LOOPDEV" 2>/dev/null || true
	fi
}
trap cleanup EXIT

if [[ $SKIP_MOUNT -ne 1 ]]; then
	[[ -b $PART ]] || { echo "no $PART"; exit 1; }
	mkdir -p "$MNT"
	if ! mount "$PART" "$MNT" 2>/dev/null; then
		if [[ $LOOP_FALLBACK -eq 1 ]]; then
			echo "direct mount failed (stale ext4 sysfs?) — using loop fallback"
			LOOPDEV=$(losetup -f --show "$PART")
			mount -t ext4 "$LOOPDEV" "$MNT"
		else
			echo "mount $PART $MNT failed"
			exit 1
		fi
	fi
	DID_MOUNT=1
fi

REL=$(cat "$K/include/config/kernel.release")
mkdir -p "$MNT/lib/modules/$REL/extra" \
	"$MNT/lib/firmware/aic8800d80" \
	"$MNT/root/aic8800" \
	"$MNT/usr/local/sbin" \
	"$MNT/etc/modules-load.d" \
	"$MNT/etc/systemd/system" \
	"$MNT/etc/systemd/system/multi-user.target.wants"

# Prefer freshly built modules from the kernel tree; fall back to staging.
if [[ -f $K/drivers/net/wireless/aicsemi/aic8800/aic8800_sdio.ko ]]; then
	cp -a "$K/drivers/net/wireless/aicsemi/aic8800/aic8800_core.ko" \
	      "$K/drivers/net/wireless/aicsemi/aic8800/aic8800_sdio.ko" \
	      "$MNT/lib/modules/$REL/extra/"
	cp -a "$K/drivers/net/wireless/aicsemi/aic8800/aic8800_core.ko" \
	      "$K/drivers/net/wireless/aicsemi/aic8800/aic8800_sdio.ko" \
	      "$MNT/root/aic8800/"
else
	cp -a "$STAGING/lib/modules/$REL/extra/"*.ko "$MNT/lib/modules/$REL/extra/"
	cp -a "$STAGING/lib/modules/$REL/extra/"*.ko "$MNT/root/aic8800/"
fi
if [[ -d $STAGING/lib/firmware/aic8800d80 ]]; then
	cp -a "$STAGING/lib/firmware/aic8800d80/"* "$MNT/lib/firmware/aic8800d80/"
fi
cp -a "$IMG" "$MNT/boot/Image"
if [[ -f $DTB ]]; then
	cp -a "$DTB" "$MNT/boot/sun60i-a733-orangepi-4-pro.dtb"
	mkdir -p "$MNT/boot/dtb/allwinner"
	cp -a "$DTB" "$MNT/boot/dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb"
fi
cp -a "$IMG" "$MNT/boot/mainline-backup/Image" 2>/dev/null || true
if command -v depmod >/dev/null 2>&1; then
	depmod -b "$MNT" "$REL" 2>/dev/null || true
fi

# --- Boot init: /sbin/a733-boot (wifi first), then try systemd ---------------
# This board currently fails to keep systemd as PID 1 and falls through to
# bash, so Wi-Fi must be brought up from the init wrapper itself.
install -m 0755 /dev/stdin "$MNT/sbin/a733-boot" <<'EOF'
#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root
export TERM=linux
mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mkdir -p /run /dev/pts /tmp
mount -t tmpfs -o mode=755,nodev,nosuid,noexec tmpfs /run 2>/dev/null
mount -t devpts devpts /dev/pts 2>/dev/null
mount -t tmpfs tmpfs /tmp 2>/dev/null
mount -o remount,rw / 2>/dev/null
echo "a733-boot: starting" > /dev/kmsg 2>/dev/null
if [ -x /usr/local/sbin/aic8800-wifi-bringup.sh ]; then
	/usr/local/sbin/aic8800-wifi-bringup.sh >/run/aic8800-wifi.log 2>&1
	echo "a733-boot: wifi bringup rc=$?" > /dev/kmsg 2>/dev/null
elif [ -x /root/aic-load.sh ]; then
	/root/aic-load.sh >/run/aic8800-wifi.log 2>&1
fi
ip link set lo up 2>/dev/null
ip link set wlan0 up 2>/dev/null
echo "a733-boot: exec systemd" > /dev/kmsg 2>/dev/null
exec /lib/systemd/systemd "$@" 2>/run/systemd-exec.err
echo "a733-boot: systemd failed" > /dev/kmsg 2>/dev/null
exec /bin/bash -i </dev/console >/dev/console 2>&1
EOF
rm -f "$MNT/init"
cp -a "$MNT/sbin/a733-boot" "$MNT/init"
chmod 755 "$MNT/init"
# Relative symlinks only — absolute /lib/... escapes to the HOST when mounted.
if [[ -x $MNT/lib/systemd/systemd ]]; then
	ln -sfn ../lib/systemd/systemd "$MNT/sbin/init"
	ln -sfn ../lib/systemd/systemd "$MNT/bin/init"
	ln -sfn ../lib/systemd/systemd "$MNT/usr/sbin/init"
fi

# Bootargs: init=/sbin/a733-boot (never rdinit stub / bare systemd).
if [[ -f $MNT/boot/boot.cmd ]]; then
	cp -a "$MNT/boot/boot.cmd" "$MNT/boot/boot.cmd.bak-wifi-auto-$(date +%Y%m%d-%H%M%S)"
	cat > "$MNT/boot/boot.cmd" <<'BOOTCMD'
setenv load_addr "0x43100000"
echo "Boot script loaded from ${devtype} ${devnum}"
if test -e ${devtype} ${devnum} ${prefix}orangepiEnv.txt; then
	load ${devtype} ${devnum} ${load_addr} ${prefix}orangepiEnv.txt
	env import -t ${load_addr} ${filesize}
fi
setenv consoleargs "console=ttyS0,115200 earlycon=uart8250,mmio32,0x02500000"
if test -z "${rootdev}"; then setenv rootdev "/dev/mmcblk0p1"; fi
setenv bootargs "root=${rootdev} rootwait rootfstype=ext4 init=/sbin/a733-boot ${consoleargs} consoleblank=0 loglevel=8 clk_ignore_unused ignore_loglevel random.trust_cpu=on random.trust_bootloader=on rw panic=10"
echo "bootargs=${bootargs}"
load ${devtype} ${devnum} ${kernel_addr_r} ${prefix}Image
load ${devtype} ${devnum} ${fdt_addr_r} ${prefix}dtb/${fdtfile}
fdt addr ${fdt_addr_r}
fdt resize 65536
booti ${kernel_addr_r} - ${fdt_addr_r}
BOOTCMD
	if command -v mkimage >/dev/null 2>&1; then
		mkimage -C none -A arm -T script -d "$MNT/boot/boot.cmd" \
			"$MNT/boot/boot.scr" >/dev/null
	else
		echo "WARNING: mkimage not found — boot.scr not regenerated"
	fi
fi

# Autoload via modules-load (belt) + SDIO aliases via depmod (suspenders).
cat > "$MNT/etc/modules-load.d/aic8800.conf" <<'EOF'
# Force AIC8800 SDIO Wi-Fi at boot. cfg80211 is built-in on 7.1.3-a733.
aic8800_sdio
EOF

install -m 0755 "$SCRIPT_DIR/aic8800-wifi-bringup.sh" \
	"$MNT/usr/local/sbin/aic8800-wifi-bringup.sh"
install -m 0644 "$SCRIPT_DIR/aic8800-wifi.service" \
	"$MNT/etc/systemd/system/aic8800-wifi.service"
ln -sfn /etc/systemd/system/aic8800-wifi.service \
	"$MNT/etc/systemd/system/multi-user.target.wants/aic8800-wifi.service"

if [[ -f $SCRIPT_DIR/wifi-up.sh ]]; then
	install -m 0755 "$SCRIPT_DIR/wifi-up.sh" "$MNT/root/wifi-up.sh"
fi

cat > "$MNT/root/aic-load.sh" <<'EOS'
#!/bin/sh
# Manual reload helper (normally unnecessary — aic8800-wifi.service does this).
set -e
MODDIR=/root/aic8800
REL=$(uname -r)
if [ ! -f "$MODDIR/aic8800_sdio.ko" ]; then
	MODDIR=/lib/modules/$REL/extra
fi
modprobe cfg80211 2>/dev/null || true
rmmod aic8800_sdio 2>/dev/null || true
rmmod aic8800_core 2>/dev/null || true
insmod "$MODDIR/aic8800_core.ko"
insmod "$MODDIR/aic8800_sdio.ko"
sleep 1
dmesg | grep -iE 'aic8800|claim_irq|protocol_boot|io_init|intr enable|normal mode|handoff|Resources present' | tail -40
echo -n 'sdio: '
ls /sys/bus/sdio/devices/ 2>/dev/null || true
for d in /sys/bus/sdio/devices/mmc1:*; do
	[ -d "$d" ] || continue
	echo "  $(basename "$d") vendor=$(cat "$d/vendor" 2>/dev/null) device=$(cat "$d/device" 2>/dev/null) driver=$(basename "$(readlink "$d/driver" 2>/dev/null)" 2>/dev/null)"
done
ip link show 2>/dev/null | grep -i wlan || true
EOS
chmod +x "$MNT/root/aic-load.sh"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
cp -a "$SCRIPT_DIR/wifi-inject-probe.py" "$MNT/root/wifi-inject-probe.py"
cp -a "$SCRIPT_DIR/wifi-monitor.sh" "$MNT/usr/local/sbin/wifi-monitor"
cp -a "$SCRIPT_DIR/wifi-station.sh" "$MNT/usr/local/sbin/wifi-station"
chmod +x "$MNT/root/wifi-inject-probe.py" \
	"$MNT/usr/local/sbin/wifi-monitor" "$MNT/usr/local/sbin/wifi-station"

cat > "$MNT/root/WIFI-TEST.txt" <<'EOS'
Orange Pi 4 Pro / AIC8800 Wi-Fi checks
======================================

Requires: aic8800 modules loaded, /lib/firmware/aic8800d80/, regulatory.db

Station:
  ip link set wlan0 up
  iw dev wlan0 scan | head -40

Monitor (single VIF — type switch, not "interface add"):
  wifi-monitor 6
  tcpdump -i wlan0 -c 20 -n -e
  wifi-inject-probe.py wlan0
  wifi-station

Notes:
  - Host inject is proven via tx_packets; on-air needs a second sniffer.
  - Firmware prefers aic8800d80/fmacfw_8800d80_u02.bin
EOS

echo "Installed Image+modules+auto-wifi for REL=$REL"
echo "vermagic=$(modinfo -F vermagic "$MNT/root/aic8800/aic8800_sdio.ko" 2>/dev/null || true)"
echo "boot init: /sbin/a733-boot (wifi then systemd/shell)"
echo "bootargs line:"
grep 'setenv bootargs' "$MNT/boot/boot.cmd" | head -1 || true
echo "After reboot: ip -br link  # expect wlan0 UP"
echo "Log: cat /run/aic8800-wifi.log"
echo INSTALL_AIC_OK
