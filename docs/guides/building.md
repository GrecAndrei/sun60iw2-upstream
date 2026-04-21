# Building the Kernel

## Prerequisites

### Host System

You need a Linux machine (x86_64 or ARM64) with:

```bash
sudo apt update
sudo apt install -y \
    build-essential \
    bc \
    bison \
    flex \
    libssl-dev \
    libncurses5-dev \
    libelf-dev \
    dwarves \
    git \
    crossbuild-essential-arm64 \
    qemu-user-static \
    debootstrap
```

### Toolchain

The `crossbuild-essential-arm64` package provides `aarch64-linux-gnu-gcc`.

Verify:
```bash
aarch64-linux-gnu-gcc --version
# Should show gcc 12.x or higher
```

---

## Getting the Source

### 1. Clone Upstream Linux

```bash
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git linux-sun60iw2
cd linux-sun60iw2
git checkout v7.0  # or latest stable
```

### 2. Clone This Project

```bash
git clone https://github.com/YOURNAME/sun60iw2-upstream.git
cd sun60iw2-upstream
```

### 3. Apply Patches

When we have patches:

```bash
cd linux-sun60iw2
./scripts/patch-kernel.sh ../sun60iw2-upstream/patches/
```

Or manually:
```bash
cd linux-sun60iw2
git am ../sun60iw2-upstream/patches/*.patch
```

---

## Configuration

### Using Our Defconfig

```bash
cd linux-sun60iw2
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- sun60iw2_defconfig
```

### Customizing

```bash
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- menuconfig
```

### Important Options

For early development, enable:

```
Kernel hacking ->
    Compile-time checks and compiler options ->
        [*] Compile the kernel with debug info
        [*] Provide GDB scripts for kernel debugging

Kernel hacking ->
    printk and dmesg options ->
        [*] Show timing information on printks
        (15) Default message log level

Device Drivers ->
    Serial drivers ->
        <*> 8250/16550 and compatible serial support
        <*> Console on 8250/16550 and compatible serial port

Device Drivers ->
    Character devices ->
        [*] Support for console on serial port
```

---

## Building

### Full Build

```bash
cd linux-sun60iw2
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
```

### Build Artifacts

After successful build:

| File | Location | Purpose |
|------|----------|---------|
| Kernel Image | `arch/arm64/boot/Image` | Main kernel binary |
| Device Tree Blob | `arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb` | Hardware description |
| Modules | `lib/modules/7.0.0/` | Loadable modules |

---

## Creating a Boot Image

### For SD Card (when U-Boot exists)

```bash
# Mount the boot partition
sudo mkdir -p /mnt/sdcard-boot
sudo mount /dev/sdX1 /mnt/sdcard-boot

# Copy kernel and DTB
sudo cp arch/arm64/boot/Image /mnt/sdcard-boot/
sudo cp arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb /mnt/sdcard-boot/

# Copy modules to rootfs
sudo make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- INSTALL_MOD_PATH=/mnt/sdcard-root modules_install
```

### Boot Script (extlinux)

Create `/mnt/sdcard-boot/extlinux/extlinux.conf`:

```ini
label sun60iw2
    kernel /Image
    fdt /sun60i-a733-orangepi-4-pro.dtb
    append console=ttyS0,115200n8 root=/dev/mmcblk0p2 rw rootwait earlyprintk
```

---

## Troubleshooting

### Build Errors

| Error | Solution |
|-------|----------|
| `aarch64-linux-gnu-gcc: command not found` | Install `crossbuild-essential-arm64` |
| `openssl/opensslv.h: No such file` | Install `libssl-dev` |
| `bison: command not found` | Install `bison` |
| `flex: command not found` | Install `flex` |

### Runtime Issues

| Symptom | Likely Cause |
|---------|--------------|
| No UART output | Wrong earlyprintk, clocks not enabled, wrong pins |
| Kernel panic | Missing device tree nodes, wrong memory map |
| Hangs after "Starting kernel..." | Wrong UART base address, GIC issue |

---

## Debug Build

For maximum debug info:

```bash
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- sun60iw2_defconfig
./scripts/config --enable DEBUG_KERNEL
./scripts/config --enable DEBUG_INFO
./scripts/config --enable DEBUG_LL
./scripts/config --enable EARLY_PRINTK
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
```

---

## Next Steps

- [Testing Guide](testing.md) - How to test on real hardware
- [Development Guidelines](../development.md) - Code standards
- [Status](../status.md) - What's implemented
