# Development Status

Last updated: 2026-04-21

## Legend

| Symbol | Meaning |
|--------|---------|
| :white_check_mark: | Working / Complete |
| :construction: | In Progress |
| :x: | Not Started / Blocked |
| :warning: | Partially Working / Known Issues |

---

## Phase 1: "Hello World" Boot

| Component | Status | Notes | Assignee |
|-----------|--------|-------|----------|
| Base DTSI (`sun60i-a733.dtsi`) | :construction: | WIP - basic structure done | - |
| Board DTS (`sun60i-a733-orangepi-4-pro.dts`) | :construction: | WIP - basic structure done | - |
| Main CCU driver | :x: | Not started | - |
| R-CCU driver | :x: | Not started | - |
| RTC CCU driver | :x: | Not started | - |
| CPUPLL driver | :x: | Not started | - |
| Pinctrl (main) | :x: | Not started | - |
| Pinctrl (R-domain) | :x: | Not started | - |
| dt-bindings headers | :white_check_mark: | All clock/reset/power IDs defined | - |
| UART earlyprintk | :x: | Blocked on clocks + pinctrl | - |
| Timer | :construction: | Node added, needs driver verification | - |
| GICv3 + ITS | :white_check_mark: | Generic ARM - should work | - |
| **Phase 1 Goal** | :construction: | UART boot messages | - |

---

## Phase 2: Storage & Power

| Component | Status | Notes | Assignee |
|-----------|--------|-------|----------|
| MMC/SD host | :x: | Needs sun60iw2 quirks in sunxi-mmc | - |
| eMMC | :x: | Same driver as MMC | - |
| Thermal (8 sensors) | :x: | Extend sun8i_thermal.c | - |
| CPUFreq / DVFS | :x: | Needs OPP tables + nvmem | - |
| Power domains (PCK600) | :x: | Extend sun55i-pck600.c | - |
| AXP515 PMIC | :x: | New PMIC, needs driver | - |
| AXP8191 PMIC | :x: | 35+ regulators, major work | - |
| **Phase 2 Goal** | :x: | Boots to userspace shell | - |

---

## Phase 3: Connectivity

| Component | Status | Notes | Assignee |
|-----------|--------|-------|----------|
| Ethernet (GMAC0) | :x: | Extend dwmac-sun55i.c | - |
| USB 2.0 Host (EHCI/OHCI) | :x: | Generic platform + glue | - |
| USB 2.0 OTG (MUSB) | :x: | Generic platform + glue | - |
| USB 3.0 (DWC3/xHCI) | :x: | Needs xhci glue + PHY | - |
| PCIe RC | :x: | **NO MAINLINE DRIVER EXISTS** | - |
| PCIe PHY (Cadence Combophy) | :x: | **NO MAINLINE DRIVER EXISTS** | - |
| SDIO (WiFi/BT) | :x: | Same MMC driver + firmware | - |
| **Phase 3 Goal** | :x: | Headless server functional | - |

---

## Phase 4: Display, GPU, NPU, Camera

| Component | Status | Notes | Assignee |
|-----------|--------|-------|----------|
| Display Engine (DE v352) | :x: | New generation, no template | - |
| HDMI 2.0 | :x: | Vendor has full stack | - |
| MIPI DSI | :x: | Panel output | - |
| eDP | :x: | Panel output | - |
| GPU (Imagination BXM-4-64) | :x: | No upstream driver | - |
| NPU (3 TOPS VIP) | :x: | No upstream driver | - |
| VIN/ISP (CSI, MIPI, ISP600) | :x: | Completely vendor-only | - |
| Audio (I2S, DMIC, OWA, HDMI) | :x: | Platform audio stack | - |
| Video Engine (Cedar) | :x: | May work with Cedrus | - |
| **Phase 4 Goal** | :x: | Full desktop/media/AI | - |

---

## Known Issues / Blockers

1. **No mainline U-Boot support.** We rely on vendor bootloader for now.
2. **PCIe controller driver does not exist in mainline.** Must be written from scratch using Synopsys DWC framework.
3. **Cadence Combophy driver does not exist in mainline.** Shared USB3/PCIe PHY.
4. **AXP8191 PMIC is brand new.** No mainline driver exists.
5. **Display stack is entirely vendor-specific.** No upstream DE v352 or HDMI 2.0 support.
6. **NPU and GPU have no upstream drivers.** These will likely remain out-of-tree modules.

---

## Testing Matrix

| Test | Orange Pi 4 Pro (8GB) | Orange Pi 4 Pro (4GB) | Orange Pi 4 Pro (2GB) |
|------|:---------------------:|:---------------------:|:---------------------:|
| UART boot | :x: | :x: | :x: |
| SD card boot | :x: | :x: | :x: |
| eMMC boot | :x: | :x: | :x: |
| Ethernet | :x: | :x: | :x: |
| USB host | :x: | :x: | :x: |
| PCIe/NVMe | :x: | :x: | :x: |
| WiFi/BT | :x: | :x: | :x: |
| HDMI output | :x: | :x: | :x: |
| GPU acceleration | :x: | :x: | :x: |
| NPU inference | :x: | :x: | :x: |

