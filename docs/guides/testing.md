# Testing on Real Hardware

## Validation Suite (Pre-Hardware)

Before testing on real hardware, run the automated validation suite:

```bash
cd sun60iw2-upstream
python3 scripts/validate-factory.py
```

**Expected output:** `ALL 24 CHECKS PASSED`

This verifies:
- All JSON data is valid
- Generators are deterministic
- Committed drivers match regenerated output
- Pinctrl structure is valid (bank sizes, IRQ maps, pin ranges)
- Driver patterns match mainline conventions

### Compile Gates

Every driver must compile in the Linux tree before hardware testing:

```bash
# CCU drivers (all 4 domains)
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/clk/sunxi-ng/ccu-sun60i-a733.o
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/clk/sunxi-ng/ccu-sun60i-a733-r.o
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/clk/sunxi-ng/ccu-sun60i-a733-rtc.o
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/clk/sunxi-ng/ccu-sun60i-a733-cpupll.o

# Pinctrl
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/pinctrl/sunxi/pinctrl-sun60i-a733.o

# DTB
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- dtbs
```

## Required Hardware

- Orange Pi 4 Pro (any RAM variant)
- USB-to-TTL serial cable (3.3V logic level)
- microSD card (16GB+ recommended)
- 5V/3A USB-C power supply
- Ethernet cable (for network testing)
- USB keyboard (for interactive testing)
- HDMI monitor (for display testing)

---

## Serial Console Setup

### Pinout (40-pin header)

| Pin | Function |
|-----|----------|
| 6   | GND |
| 8   | UART0_TX (GPIO PH0) |
| 10  | UART0_RX (GPIO PH1) |

### Connection

```
USB-TTL Cable    Orange Pi 4 Pro
-----------      ---------------
GND     ------>  Pin 6 (GND)
TX      ------>  Pin 10 (UART0_RX)
RX      ------>  Pin 8 (UART0_TX)
```

### Serial Parameters

- **Baud rate:** 115200
- **Data bits:** 8
- **Stop bits:** 1
- **Parity:** None
- **Flow control:** None

### Host Commands

```bash
# Linux
sudo minicom -D /dev/ttyUSB0 -b 115200

# Or use screen
screen /dev/ttyUSB0 115200

# Or picocom
picocom -b 115200 /dev/ttyUSB0
```

---

## Boot Process

### Expected Boot Sequence (when working)

```
U-Boot SPL 2024.10-orangepi (Jan 01 2026 - 00:00:00 +0000)
DRAM: 8192 MiB
Trying to boot from MMC1

U-Boot 2024.10-orangepi (Jan 01 2026 - 00:00:00 +0000)

Loading Environment from FAT... OK
Hit any key to stop autoboot:  0
Loading kernel...
Loading device tree...
Starting kernel...

[    0.000000] Booting Linux on physical CPU 0x0000000000 [0x412fd050]
[    0.000000] Linux version 7.0.0-sun60iw2+ (...)
[    0.000000] Machine model: Orange Pi 4 Pro
...
```

### Current Status

**We are not here yet.** Current expected output is either:
- Nothing (kernel doesn't boot at all)
- Garbled text (wrong UART config)
- Hang after "Starting kernel..."

---

## Testing Checklist

### Phase 1: UART Boot

- [ ] Connect serial cable, see U-Boot SPL output
- [ ] U-Boot loads kernel Image
- [ ] Kernel starts, prints version string
- [ ] Device tree is parsed correctly
- [ ] Earlyprintk works
- [ ] Timers initialize
- [ ] CPU cores come online

### Phase 2: Storage Boot

- [ ] SD card detected (MMC0)
- [ ] SD card read/write works
- [ ] eMMC detected (MMC2)
- [ ] eMMC read/write works
- [ ] Rootfs mounts from SD/eMMC
- [ ] Init/systemd starts
- [ ] Get shell prompt

### Phase 3: Connectivity

- [ ] Ethernet link up
- [ ] DHCP or static IP works
- [ ] Ping gateway
- [ ] Ping internet
- [ ] USB 2.0 host (keyboard, storage)
- [ ] USB 3.0 host (storage)
- [ ] PCIe link up
- [ ] NVMe SSD detected

### Phase 4: Advanced

- [ ] HDMI output
- [ ] GPU acceleration (glxgears)
- [ ] NPU inference
- [ ] Camera detected
- [ ] Audio playback
- [ ] WiFi scan
- [ ] Bluetooth pair

---

## Debugging Tips

### No UART Output

1. Check cable connections (TX/RX may be swapped)
2. Verify serial parameters (115200 8N1)
3. Check U-Boot environment for `console=` setting
4. Verify earlyprintk is enabled in kernel config
5. Check device tree has correct UART base address

### Kernel Hang

1. Enable `CONFIG_DEBUG_LL` and `CONFIG_EARLY_PRINTK`
2. Add `earlyprintk` to kernel command line
3. Check if hang is before or after `start_kernel()`
4. Add printks in `setup_arch()` to narrow down

### Device Tree Issues

```bash
# On target (if you get that far)
cat /proc/device-tree/compatible
cat /proc/device-tree/model
ls /proc/device-tree/
```

### Kernel Panic

1. Note the panic message and call trace
2. Check if it's a NULL pointer, page fault, or assertion
3. Look at the line number in the source
4. Common causes: wrong reg addresses, missing clocks, wrong compatible

---

## Performance Testing

### CPU

```bash
cpu-benchmark
sysbench cpu --cpu-max-prime=20000 run
```

### Memory

```bash
sysbench memory --memory-block-size=1K --memory-total-size=2G run
```

### Storage

```bash
# SD card
sudo hdparm -t /dev/mmcblk0

# eMMC
sudo hdparm -t /dev/mmcblk2

# NVMe (if PCIe works)
sudo hdparm -t /dev/nvme0n1
```

### Network

```bash
# Ethernet
iperf3 -c server_ip

# WiFi (when working)
iperf3 -c server_ip
```

---

## Reporting Results

When reporting test results, include:

1. **Hardware:** Orange Pi 4 Pro variant (2GB/4GB/8GB)
2. **Git commit:** `git rev-parse HEAD`
3. **Kernel config:** `gzip -c .config | base64` (or attach)
4. **Boot log:** Full serial capture from power-on
5. **What works:** List of passing tests
6. **What doesn't:** List of failing tests with symptoms
7. **Steps to reproduce:** Exact commands or sequence

Use GitHub Issues with label `testing`.
