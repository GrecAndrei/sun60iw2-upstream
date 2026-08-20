#!/bin/bash
# Vendor 5.15 DT probes 4022000 first → empty eMMC becomes mmc0.
# Arch root on the SD slot is mmc1 → /dev/mmcblk1p1.
set -euo pipefail
MNT=/mnt/sun60i-a733-rootfs
DEV=${1:-/dev/mmcblk0p1}

echo "Waiting for $DEV ..."
for i in $(seq 1 90); do
	[[ -b "$DEV" ]] && break
	sleep 1
done
[[ -b "$DEV" ]] || { echo "NO_CARD $DEV"; exit 1; }

unalias sudo 2>/dev/null || true
unset SUDO_ASKPASS SUDO_ASKPASS_REQUIRE
printf '1235\n' | /usr/bin/sudo -S -v

/usr/bin/sudo -n mkdir -p "$MNT"
/usr/bin/sudo -n bash -c "umount $DEV 2>/dev/null || true; umount $MNT 2>/dev/null || true"
/usr/bin/sudo -n mount "$DEV" "$MNT"

TS=$(date +%Y%m%d-%H%M%S)
/usr/bin/sudo -n cp -a "$MNT/boot/boot.cmd" "$MNT/boot/boot.cmd.bak-rootfix-$TS"
/usr/bin/sudo -n cp -a "$MNT/boot/boot.scr" "$MNT/boot/boot.scr.bak-rootfix-$TS" 2>/dev/null || true
if [[ -f "$MNT/boot/orangepiEnv.txt" ]]; then
	/usr/bin/sudo -n cp -a "$MNT/boot/orangepiEnv.txt" \
		"$MNT/boot/orangepiEnv.txt.bak-rootfix-$TS"
fi

/usr/bin/sudo -n tee "$MNT/boot/boot.cmd" >/dev/null <<'EOF'
# Vendor-kernel control boot: root is SD → mmcblk1p1 under vendor DT.
setenv load_addr "0x43100000"
echo "Boot script loaded from ${devtype} ${devnum}"
if test -e ${devtype} ${devnum} ${prefix}orangepiEnv.txt; then
	load ${devtype} ${devnum} ${load_addr} ${prefix}orangepiEnv.txt
	env import -t ${load_addr} ${filesize}
fi
setenv rootdev "/dev/mmcblk1p1"
setenv consoleargs "console=ttyS0,115200 earlycon=uart8250,mmio32,0x02500000 earlyprintk=sunxi-uart,0x02500000"
setenv bootargs "root=${rootdev} rootwait rootfstype=ext4 init=/bin/bash ${consoleargs} consoleblank=0 loglevel=8 clk_ignore_unused ignore_loglevel random.trust_cpu=on random.trust_bootloader=on rw panic=10"
echo "bootargs=${bootargs}"
load ${devtype} ${devnum} ${kernel_addr_r} ${prefix}Image
if test -e ${devtype} ${devnum} ${prefix}dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb; then
	load ${devtype} ${devnum} ${fdt_addr_r} ${prefix}dtb/allwinner/sun60i-a733-orangepi-4-pro.dtb
else
	load ${devtype} ${devnum} ${fdt_addr_r} ${prefix}dtb/${fdtfile}
fi
fdt addr ${fdt_addr_r}
fdt resize 65536
booti ${kernel_addr_r} - ${fdt_addr_r}
EOF

/usr/bin/sudo -n mkimage -C none -A arm -T script -d "$MNT/boot/boot.cmd" \
	"$MNT/boot/boot.scr" >/dev/null
/usr/bin/sudo -n tee "$MNT/boot/orangepiEnv.txt" >/dev/null <<'EOF'
verbosity=8
console=serial
rootdev=/dev/mmcblk1p1
rootfstype=ext4
EOF

# Ensure check script exists for after shell appears
/usr/bin/sudo -n tee "$MNT/root/vendor-wifi-check.sh" >/dev/null <<'EOF'
#!/bin/bash
set -x
dmesg | grep -E '4021000|rfkill|wlan|aic|mmc|CMD|sdio' | tail -80
ls -l /sys/bus/sdio/devices 2>/dev/null || true
ls /lib/modules/$(uname -r)/ 2>/dev/null | head
modprobe cfg80211 2>/dev/null || true
modprobe aic8800_bsp 2>/dev/null || insmod /lib/modules/*/aic8800_bsp.ko 2>/dev/null || true
sleep 1
modprobe aic8800_fdrv 2>/dev/null || insmod /lib/modules/*/aic8800_fdrv.ko 2>/dev/null || true
sleep 2
dmesg | grep -E '4021000|rfkill|wlan|aic|mmc|CMD|sdio|new high speed' | tail -60
ls -l /sys/bus/sdio/devices 2>/dev/null || true
ip link 2>/dev/null || true
EOF
/usr/bin/sudo -n chmod +x "$MNT/root/vendor-wifi-check.sh"

sync
/usr/bin/sudo -n umount "$MNT"
echo FIXED_VENDOR_ROOT_mmcblk1p1
