# Development Status

Last updated: 2026-04-22

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
| Main CCU driver | :construction: | WIP - SSEE extracts 382 items; generator merges extracted model + canonical IDs; report mode added for coverage/fidelity metrics | - |

Current CCU pipeline metrics (`python3 generators/generate_ccu.py --report --no-output`):
- Extractable clocks: 319
- Supported clocks: 319 (100% support coverage)
- ID-mapped clocks: 251 (118 canonical + 133 inferred, 78.68% ID coverage)
- Emitted HW coverage: 100%
- Emitted common coverage: 100%
- Key-gated clocks emitted natively: 35
- Remaining key-gate fallbacks: 0
- Compile gate: generated `ccu-sun60i-a733.c` builds as object and under `drivers/clk/sunxi-ng/ W=1`

**Subagent parallel extraction results:**
- R-CCU: 36 clocks + 7 parent arrays, 100% confidence
- RTC CCU: 13 clocks + 4 parent arrays, 100% confidence
- CPUPLL: 7 clocks + 3 parent arrays, 100% confidence
- Pinmux generator: designed with C/DT/report modes, prototype working
| R-CCU driver | :construction: | Extracted, needs generator | - |
| RTC CCU driver | :construction: | Extracted, needs generator | - |
| CPUPLL driver | :construction: | Extracted, needs generator | - |
| Pinctrl (main) | :construction: | WIP - generated from JSON data | - |
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

## Factory Validation Results

Run `python3 scripts/validate-factory.py` after any generator or data change.

**Latest run: ALL 19 CHECKS PASSED**

| Check | Result |
|-------|--------|
| JSON data validity (ccu-main, extracted, pinctrl) | PASS |
| CCU generator determinism | PASS (67,354 bytes) |
| Pinctrl generator determinism | PASS (1,623 bytes) |
| Committed CCU matches fresh output | PASS |
| Committed pinctrl matches fresh output | PASS |
| Generator Python syntax (6 scripts) | PASS |
| Extractor plugin syntax (3 plugins) | PASS |
| No unsupported clock entries | PASS |
| Key-gate native emission (35/35) | PASS |
| ID coverage | PASS (218/279 = 78.14%) |

**Compile gates passed:**
- `drivers/clk/sunxi-ng/ccu-sun60i-a733.o` — builds as standalone object ✅
- `drivers/clk/sunxi-ng/` (full directory, `W=1`) — builds without warnings ✅
- `drivers/pinctrl/sunxi/pinctrl-sun60i-a733.o` — builds as standalone object ✅

**Orphan dt-binding IDs:** 101 IDs in `sun60i-a733-ccu.h` have no corresponding clock data.
- These are primarily `BUS_*`, `MBUS_*`, and peripheral clock IDs that belong to R-CCU, RTC, or CPUPLL domains, or are awaiting extraction.

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
