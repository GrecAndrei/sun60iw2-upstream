# sun60iw2-upstream

Mainline Linux upstream port for the **Allwinner A733 (sun60iw2p1)** SoC and the **Orange Pi 4 Pro** board.

---

## Status: WIP / PRE-ALPHA

This repository now contains a real early-bringup port. It is **not production-ready yet**, but it now boots SD media to a BusyBox userspace shell.

### Verified So Far
- Kernel boots on Orange Pi 4 Pro hardware
- All 8 CPUs come online
- GICv3, timer, PSCI, and serial console basics are working
- SD card boot reaches a BusyBox root shell prompt
- Generated CCU, R-CCU, RTC CCU, CPUPLL, and pinctrl drivers build in the Linux tree
- DTS/DTSI, generator pipeline, and factory validation are in active use

### Still Not Working Reliably
- eMMC, SDIO, Ethernet, USB, and display still need verification
- Main CCU runtime behavior needs continued hardware soak testing
- RTC/root clock interactions still need cleanup

If you need a working system today, use the [vendor kernel](https://github.com/orangepi-xunlong/linux-orangepi) or [Armbian](https://github.com/jonas5/orangepi-4pro-armbian) instead.

### What's Here Now
- [x] Project scaffolding
- [x] Device Tree Source (DTS/DTSI)
- [x] Clock drivers (CCU)
- [x] Pinctrl drivers
- [x] Thermal driver support
- [x] UART console bringup
- [x] MMC/SD host description and initial driver support
- [ ] Ethernet (GMAC)
- [ ] USB host/device
- [ ] PCIe controller
- [ ] PMIC support (AXP515 + AXP8191)
- [ ] Display/DRM
- [ ] GPU (Imagination BXM-4-64)
- [ ] NPU (3 TOPS)
- [ ] VIN/ISP/Camera

### Boot Helpers
- `scripts/update-sd-boot.sh` refreshes a mounted SD boot partition with a built `Image` and DTB while keeping timestamped backups.
- `tools/pico_uart_bridge.py` mirrors UART output from a MicroPython bridge and watches for shell readiness.

---

## Why This Exists

The Orange Pi 4 Pro (Allwinner A733) launched with no upstream Linux support and minimal documentation. This project aims to:

1. **Port the A733 to mainline Linux** following proper kernel coding standards
2. **Document everything** so other boards using this SoC can be supported
3. **Upstream all code** to `torvalds/linux.git` so every distro works out of the box

### The Vendor Situation

Allwinner/Xunlong provides a vendor kernel (`orange-pi-6.6-sun60iw2`) with a massive `bsp/` directory containing ~1.3 million lines of out-of-tree drivers. This vendor code **will not be copied verbatim** into this project. Instead, we use it as a reference for register maps and hardware behavior, then write clean, upstreamable drivers using Linux kernel frameworks.

---

## Hardware

| Spec | Details |
|------|---------|
| **SoC** | Allwinner A733 (sun60iw2p1) |
| **CPU** | 6x Cortex-A55 @ 1.8GHz + 2x Cortex-A76 @ 2.0GHz |
| **GPU** | Imagination BXM-4-64 |
| **NPU** | 3 TOPS (VeriSilicon/Vivante VIP) |
| **RAM** | 2GB / 4GB / 8GB LPDDR4X |
| **Storage** | microSD, 32-128GB eMMC, UFS |
| **Network** | Gigabit Ethernet (GMAC), WiFi 6 + BT 5.2 (SDIO) |
| **USB** | USB 2.0 OTG, USB 2.0 Host, USB 3.0 SS+ |
| **PCIe** | PCIe 3.0 x1 |
| **Display** | HDMI 2.0, MIPI DSI, eDP, LVDS |
| **PMIC** | AXP515 + AXP8191 (dual PMIC) |
| **Extras** | RISC-V co-processor, 8-channel thermal sensors |

---

## Roadmap

### Phase 1: "Hello World" Boot (~3,750 LoC)
- Base Device Tree (`sun60i-a733.dtsi`)
- Orange Pi 4 Pro board DTS
- Clock Controller Unit (CCU) - main + R-domain
- Pinctrl (GPIO/Pinmux)
- UART earlyprintk
- **Goal:** Kernel prints boot messages over serial

### Phase 2: Storage & Power (~1,250 LoC)
- MMC/SD/eMMC host driver
- Thermal sensor support
- CPUFreq / DVFS
- Power domains (PCK600)
- PMIC drivers (AXP515, AXP8191)
- **Goal:** SD boot reaches a BusyBox shell; eMMC validation is still pending

### Phase 3: Connectivity (~2,600 LoC)
- Ethernet (GMAC200)
- USB 2.0/3.0 host
- PCIe controller + PHY
- **Goal:** Headless server/NAS fully functional

### Phase 4: "Cool Stuff" (~43,000+ LoC)
- Display Engine (DE v352)
- HDMI 2.0 / DSI / eDP
- GPU (Imagination BXM)
- NPU (3 TOPS)
- VIN/ISP/Camera pipeline
- **Goal:** Full desktop/media/AI acceleration

**Total estimated upstream code: ~7,600 lines for Phases 1-3 (realistic), ~50,000+ for everything.**

---

## Contributing

This is a community effort. All contributions must follow the [Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html) and will eventually be submitted via patch series to `linux-sunxi@lists.linux.dev`.

### Patch Workflow
1. Write clean, framework-compliant code
2. Test on real hardware (Orange Pi 4 Pro)
3. Submit as a patch series in `patches/`
4. Review & iterate
5. Submit to linux-sunxi mailing list
6. Land in torvalds/linux.git

### Communication
- **Issues:** Use GitHub Issues for bugs, tasks, and hardware questions
- **Discussions:** Use GitHub Discussions for general chat and planning
- **Mail:** Eventually patch series go to `linux-sunxi@lists.linux.dev`

---

## Building

### Prerequisites
```bash
sudo apt install build-essential bc bison flex libssl-dev libncurses5-dev \
    libelf-dev dwarves crossbuild-essential-arm64 git
```

### Quick Build (when code exists)
```bash
# Clone this repo alongside your linux tree
git clone https://github.com/YOURNAME/sun60iw2-upstream.git
cd sun60iw2-upstream

# Apply patches to a clean Linux 7.0 tree
./scripts/apply-patches.sh /path/to/linux-7.0

# Build
cd /path/to/linux-7.0
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- sun60iw2_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
```

### Flashing (vendor bootloader path)
```bash
# Update the SD boot partition with scripts/update-sd-boot.sh
# or copy Image + DTB manually when using the vendor bootloader.
```

---

## Directory Structure

```
.
├── arch/arm64/boot/dts/allwinner/    # Device Tree files
├── drivers/
│   ├── clk/sunxi-ng/                  # Clock drivers
│   ├── pinctrl/sunxi/                 # Pinctrl drivers
│   └── thermal/                       # Thermal driver patches
├── configs/                            # Kernel defconfigs
├── patches/                            # Patch series for upstream submission
├── scripts/                            # Build/helper scripts
├── docs/
│   ├── status.md                       # Current development status
│   ├── hardware.md                     # Hardware documentation
│   ├── development.md                  # Development guidelines
│   └── guides/                         # How-to guides
├── README.md
└── LICENSE
```

---

## License

All code in this repository is licensed under the [GPL-2.0+](LICENSE) to match the Linux kernel license. Device Tree files are dual-licensed GPL-2.0+ OR MIT where applicable.

---

## Disclaimer

This project is **not affiliated with** Orange Pi, Xunlong, or Allwinner. We are reverse-engineering and documenting a proprietary SoC using publicly available information, vendor source code (used as reference only), and hardware testing.

**Do not expect a production-ready system yet.** SD boot now reaches a BusyBox shell, but eMMC, SDIO, Ethernet, USB, and display still need validation. If you need a fully working system today, use the vendor kernel or Armbian.

---

## Acknowledgments

- [linux-sunxi](https://linux-sunxi.org/) community for sunxi knowledge and templates
- [jonas5](https://github.com/jonas5/orangepi-4pro-armbian) for the Armbian board definition
- Orange Pi / Xunlong for releasing vendor source code (used as reference)
- Andre Przywara and the sunxi upstream maintainers
