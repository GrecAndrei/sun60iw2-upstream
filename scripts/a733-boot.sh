#!/bin/sh
# PID 1 wrapper: set up the mounts systemd expects, then exec it for real.
# If exec fails, print the reason to the serial console and drop to bash.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/root
export TERM=linux

log() {
	echo "a733-boot: $*" > /dev/kmsg 2>/dev/null || true
	echo "a733-boot: $*" > /dev/console 2>/dev/null || true
	echo "a733-boot: $*"
}

mount -t proc proc /proc 2>/dev/null
mount -t sysfs sysfs /sys 2>/dev/null
mount -t devtmpfs devtmpfs /dev 2>/dev/null
mkdir -p /run /dev/pts /tmp /sys/fs/cgroup
mount -t tmpfs -o mode=755,nodev,nosuid,noexec tmpfs /run 2>/dev/null
mount -t devpts -o noexec,nosuid,gid=5,mode=0620 devpts /dev/pts 2>/dev/null
mount -t tmpfs tmpfs /tmp 2>/dev/null
mount -o remount,rw / 2>/dev/null

# cgroup2 early — systemd 255+ is happier if the hierarchy exists
if ! mountpoint -q /sys/fs/cgroup 2>/dev/null; then
	mount -t cgroup2 -o nsdelegate,memory_recursiveprot cgroup2 /sys/fs/cgroup 2>/dev/null \
		|| mount -t cgroup2 cgroup2 /sys/fs/cgroup 2>/dev/null \
		|| true
fi

ip link set lo up 2>/dev/null

# Prefer the real binary path (Arch /sbin -> usr/bin; /lib -> usr/lib).
SYSTEMD=/usr/lib/systemd/systemd
if [ ! -x "$SYSTEMD" ]; then
	SYSTEMD=/lib/systemd/systemd
fi

log "exec $SYSTEMD as PID 1"
# IMPORTANT: do not redirect systemd's stdio away from the console.
# A failed exec returns here; a successful exec never returns.
exec "$SYSTEMD" "$@"

# Still here → execve failed (missing ELF interpreter, noexec, etc.)
rc=$?
log "FAILED to exec $SYSTEMD (shell rc=$rc)"
if [ -x /lib/ld-linux-aarch64.so.1 ]; then
	log "ld.so --verify:"
	/lib/ld-linux-aarch64.so.1 --verify "$SYSTEMD" > /dev/console 2>&1 || true
	log "ld.so --list (first lines):"
	/lib/ld-linux-aarch64.so.1 --list "$SYSTEMD" 2>&1 | head -20 > /dev/console || true
fi
log "dropping to bash — fix systemd then reboot"
exec /bin/bash -i </dev/console >/dev/console 2>&1
