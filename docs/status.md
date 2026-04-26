# Development Status

Last updated: 2026-04-26

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
| Base DTSI (`sun60i-a733.dtsi`) | :white_check_mark: | Timer, WDT, DMA, UART, MMC, thermal, SID nodes added | - |
| Board DTS (`sun60i-a733-orangepi-4-pro.dts`) | :white_check_mark: | SD card, eMMC, SDIO WiFi enabled | - |
| Main CCU driver | :white_check_mark: | 319 clocks, 63 parent arrays, 120 reset lines; generator bug fixed: all 9 previously-missing clocks (including `apb-uart`, `iommu*`, `ve-dec-mbus-gate`) now have explicit IDs in `ccu-main.json` and regenerate identically to committed output; runtime probe still needs hardware re-verification | - |

Current CCU pipeline metrics (`python3 generators/generate_ccu.py --report --no-output`):
- Extractable clocks: 319
- Supported clocks: 319 (100% support coverage)
- ID-mapped clocks: 251 (118 canonical + 133 inferred, 78.68% ID coverage)
- Emitted HW coverage: 100%
- Emitted common coverage: 100%
- Key-gated clocks emitted natively: 35
- Remaining key-gate fallbacks: 0
- Compile gate: generated `ccu-sun60i-a733.c` builds as object and under `drivers/clk/sunxi-ng/ W=1`

**All 4 CCU domains generate cleanly:**
- Main CCU: 319 clocks + 63 parent arrays
- R-CCU: 36 clocks + 7 parent arrays
- RTC CCU: 10 clocks + 4 parent arrays
- CPUPLL: 7 clocks + 3 parent arrays
| R-CCU driver | :white_check_mark: | Generated with 14 reset lines, compiles in linux tree | - |
| RTC CCU driver | :construction: | Generated; now does pre-provider clock-source init, built-in early registration, vendor-style non-exclusive RTC mapping, and special `dcxo-wakeup` reverse/key gate emission; uses DTS-provided `rc-16m`/`ext-32k`/`dcxo19_2M`/`dcxo26M` roots; object + DTB compile in linux tree, hardware retest pending | - |
| CPUPLL driver | :white_check_mark: | Generated, compiles in linux tree | - |
| Pinctrl (main) | :white_check_mark: | 181 pins, 876 functions; C-array and DT modes both compile | - |
| Pinctrl (R-domain) | :x: | Not started | - |
| dt-bindings headers | :white_check_mark: | All clock/reset/power IDs defined; RTC header re-synced to current generated outputs | - |
| UART earlyprintk | :white_check_mark: | Main CCU now exports UART reset lines; boot logs and shell prompt are visible on hardware | - |
| Timer | :white_check_mark: | Node fixed: uses `sun8i-a23-timer` fallback, `0xa0` reg, `osc24M` clock — matches mainline H6/A64 convention | - |
| WDT | :white_check_mark: | Node fixed: uses `sun55i-a523-wdt` fallback (register-identical to vendor `wdt-v103`), added `hosc`/`losc` clocks — matches A523 binding | - |
| DMA engine | :white_check_mark: | Node + UART dmas in DTSI; new `sun60i-a733-dma` cfg in `sun6i-dma.c` with A100 fallback; compiled successfully | - |
| GICv3 + ITS | :white_check_mark: | Generic ARM - should work | - |
| **Phase 1 Goal** | :white_check_mark: | UART boot messages | - |

---

## Phase 2: Storage & Power

| Component | Status | Notes | Assignee |
|-----------|--------|-------|----------|
| MMC/SD host | :white_check_mark: | 4 controllers (mmc0-mmc3); reuses `sun20i_d1_cfg` quirks; driver patch committed | - |
| eMMC | :white_check_mark: | Same driver as MMC; 8-bit mode enabled on mmc2 | - |
| Thermal (5 sensors) | :white_check_mark: | `sun60i-a733-ths` compatible; piecewise-linear calc_temp; 5 thermal zones with cooling maps | - |
| CPUFreq / DVFS | :x: | Needs OPP tables + nvmem | - |
| Power domains (PCK600) | :x: | Extend sun55i-pck600.c | - |
| AXP515 PMIC | :x: | New PMIC, needs driver | - |
| AXP8191 PMIC | :x: | 35+ regulators, major work | - |
| **Phase 2 Goal** | :white_check_mark: | Boots to userspace shell; SD boot args restore `rootwait` and the rootfs now has a BusyBox init entry | - |

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

## Factory Validation Results

Run `python3 scripts/validate-factory.py` after any generator or data change.

**Latest run: ALL 51 CHECKS PASSED**

| Check | Result |
|-------|--------|
| JSON data validity (main, extracted, R, RTC, CPUPLL, pinctrl) | PASS |
| CCU generator determinism (main, R, RTC, CPUPLL) | PASS |
| Pinctrl generator determinism | PASS |
| Committed generated CCU matches fresh output (all 4 domains) | PASS |
| Committed pinctrl matches fresh output | PASS |
| Generator Python syntax (6 scripts) | PASS |
| Extractor plugin syntax (3 plugins) | PASS |
| No unsupported clock entries (all 4 CCU domains) | PASS |
| Reset binding coverage (main + R CCU) | PASS |
| Key-gate native emission (35/35, main CCU) | PASS |
| ID coverage | PASS (251/319 = 78.68%) |
| Pinctrl structure + mainline pattern checks | PASS |

**Compile gates passed:**
- `drivers/clk/sunxi-ng/ccu-sun60i-a733.o` — builds as standalone object ✅
- `drivers/clk/sunxi-ng/ccu-sun60i-a733-r.o` — builds as standalone object ✅
- `drivers/clk/sunxi-ng/ccu-sun60i-a733-rtc.o` — builds as standalone object ✅
- `drivers/clk/sunxi-ng/ccu-sun60i-a733-cpupll.o` — builds as standalone object ✅
- `drivers/pinctrl/sunxi/pinctrl-sun60i-a733.o` — builds as standalone object ✅
- `arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb` — builds ✅
- `drivers/dma/sun6i-dma.c` with A733 patch — builds ✅
- `drivers/thermal/sun8i_thermal.c` with A733 patch — builds ✅

**Orphan dt-binding IDs:** 101 IDs in `sun60i-a733-ccu.h` have no corresponding clock data.
- These are primarily `BUS_*`, `MBUS_*`, and peripheral clock IDs that belong to R-CCU, RTC, or CPUPLL domains, or are awaiting extraction.

---

## Known Issues / Blockers

1. **No mainline U-Boot support.** We rely on vendor bootloader for now.
2. **Main CCU runtime bringup still needs hardware re-verification.** The defconfig mismatch that left `CONFIG_SUN60I_A733_CCU` disabled was fixed, and the generated main/R CCU drivers now export reset maps instead of empty reset controllers, but the newly built Image still needs boot testing.
3. **SD boot path has been validated to userspace.** `rootwait` is restored in the SD boot environment and BusyBox init is wired up; remaining work is validation across other media and services.
4. **PCIe controller driver does not exist in mainline.** Must be written from scratch using Synopsys DWC framework.
5. **Cadence Combophy driver does not exist in mainline.** Shared USB3/PCIe PHY.
6. **AXP8191 PMIC is brand new.** No mainline driver exists.
7. **Display stack is entirely vendor-specific.** No upstream DE v352 or HDMI 2.0 support.
8. **NPU and GPU have no upstream drivers.** These will likely remain out-of-tree modules.

---

## Testing Matrix

| Test | Orange Pi 4 Pro (8GB) | Orange Pi 4 Pro (4GB) | Orange Pi 4 Pro (2GB) |
|------|:---------------------:|:---------------------:|:---------------------:|
| UART boot | :white_check_mark: | :x: | :x: |
| SD card boot | :white_check_mark: | :x: | :x: |
| eMMC boot | :x: | :x: | :x: |
| Ethernet | :x: | :x: | :x: |
| USB host | :x: | :x: | :x: |
| PCIe/NVMe | :x: | :x: | :x: |
| WiFi/BT | :x: | :x: | :x: |
| HDMI output | :x: | :x: | :x: |
| GPU acceleration | :x: | :x: | :x: |
| NPU inference | :x: | :x: | :x: |
