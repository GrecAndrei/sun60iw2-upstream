# Hardware Documentation

## Allwinner A733 (sun60iw2p1)

The A733 is Allwinner's newest high-performance ARM SoC, launched in late 2025/early 2026. It is part of the `sun60iw2` family.

### CPU

| Cluster | Cores | Architecture | Max Frequency |
|---------|-------|--------------|---------------|
| Little | 6x | Cortex-A55 | 1.8 GHz |
| Big | 2x | Cortex-A76 | 2.0 GHz |

- DSU (DynamIQ Shared Unit) with L3 cache
- GICv3 with ITS (Interrupt Translation Service)
- ARMv8.2-A architecture

### Memory

- LPDDR4X controller
- Supports up to 8GB RAM
- 32-bit bus width

### Co-Processors

| Unit | Description |
|------|-------------|
| **RISC-V** | Embedded RISC-V core in CPUS/RTC domain (clocks/resets exist, firmware-managed) |
| **NPU** | 3 TOPS AI accelerator (VeriSilicon/Vivante VIP architecture) |
| **GPU** | Imagination BXM-4-64 (IMG Rogue architecture) |
| **VE** | Cedar video engine (decoder + encoder) |
| **ISP** | ISP600 image signal processor |

---

## Memory Map

| Address Range | Size | Device |
|---------------|------|--------|
| `0x0000_0000` | 4KB | SRAM / Boot ROM |
| `0x0200_0000` | 64KB | Pinctrl (PIO) |
| `0x0200_2000` | 8KB | Clock Controller Unit (CCU) |
| `0x0250_0000` | 28KB | UART0-6 |
| `0x0251_0000` | 52KB | TWI0-12 (I2C) |
| `0x0300_0000` | 4KB | SRAM control |
| `0x0300_4000` | 4KB | Mailbox |
| `0x0300_5000` | 4KB | HW Spinlock |
| `0x0300_6000` | 4KB | SID / eFuses |
| `0x0340_0000` | 64KB | GIC Distributor |
| `0x0346_0000` | 1MB | GIC Redistributors |
| `0x0390_0000` | 128KB | IOMMU |
| `0x0402_0000` | 16KB | MMC0-3 (SD/SDIO/eMMC) |
| `0x0450_0000` | 32KB | GMAC0 |
| `0x0451_0000` | 32KB | GMAC1 |
| `0x0460_1000` | 8KB | DMA |
| `0x0500_0000` | 4MB | Display Engine (DE v352) |
| `0x0550_0000` | 64KB | TCON / Video Output |
| `0x0580_0000` | 1MB | VIN / ISP |
| `0x0600_0000` | 4.5MB | PCIe RC |
| `0x06A0_0000` | 1MB | USB3 DWC3 (xHCI) |
| `0x0701_0000` | 1KB | R-CCU |
| `0x0702_5000` | 1KB | R-Pinctrl |
| `0x0706_0000` | 44KB | PCK-600 Power Controller |
| `0x0708_0000` | 2KB | R-UART |
| `0x0709_0000` | 1KB | RTC + RTC-CCU |
| `0x4000_0000` | + | DRAM start |

---

## Clock Architecture

The A733 has **4 separate clock controllers**:

1. **Main CCU** (`0x0200_2000`) - ~333 clocks for all main-domain peripherals
2. **R-CCU** (`0x0701_0000`) - ~46 clocks for CPUS/RTC domain
3. **RTC CCU** (`0x0709_0000`) - RTC and low-power clocks
4. **CPUPLL CCU** (`0x0887_0000`) - CPU cluster PLLs and DSU

### Root Clocks

| Clock | Frequency | Source |
|-------|-----------|--------|
| DCXO24M | 24 MHz | External crystal |
| DCXO19.2M | 19.2 MHz | Alternative crystal |
| DCXO26M | 26 MHz | Alternative crystal |
| RC-16M | 16 MHz | Internal RC oscillator (300ppm) |
| EXT-32K | 32.768 kHz | External RTC crystal |

### Key PLLs

| PLL | Output | Used By |
|-----|--------|---------|
| PLL_DDR | DDR memory clock | DRAM controller |
| PLL_PERI0/1 | Peripheral clocks | USB, MMC, UART, etc. |
| PLL_CPU_L | Little cluster | 6x A55 |
| PLL_CPU_B | Big cluster | 2x A76 |
| PLL_CPU_DSU | DSU/L3 cache | Shared L3 |
| PLL_GPU0 | GPU clock | Imagination BXM |
| PLL_NPU | NPU clock | AI accelerator |
| PLL_VIDEO0/1/2 | Video clocks | Display, HDMI |
| PLL_VE0/1 | Video engine | Cedar encoder/decoder |
| PLL_AUDIO0/1 | Audio clocks | I2S, DMIC, SPDIF |

---

## Pinmux Architecture

### Main Pinctrl (PIO)

- **Base:** `0x0200_0000`
- **Banks:** PA, PB, PC, PD, PE, PF, PG, PH, PI, PJ, PK
- **Functions:** GPIO in/out, dedicated peripherals, special functions (JTAG, etc.)

### R-Pinctrl (R_PIO)

- **Base:** `0x0702_5000`
- **Banks:** PL, PM, PN
- **Used for:** RTC domain, always-on peripherals, WiFi/BT control, PMIC I2C

---

## Orange Pi 4 Pro Board Specifics

### Power

- **Input:** 5V/3A USB-C or DC barrel jack
- **PMIC1:** AXP515 @ I2C address `0x34` (always-on domain, USB power)
- **PMIC0:** AXP8191 @ I2C address `0x36` (35+ regulators for all domains)

### Storage

- **microSD:** SDC0 (4-bit, UHS-I SDR104)
- **eMMC:** SDC2 (8-bit, HS200/HS400)
- **UFS:** Optional (SDC3 disabled on this board)

### Network

- **Ethernet:** GMAC0, RGMII, Realtek RTL8211F PHY @ MDIO addr 0x1
- **WiFi/BT:** SDC1 (SDIO), AMPAK AP6275S or similar (WiFi 6 + BT 5.2)

### USB

- **USB0:** OTG (Type-C), ID/VBUS detect via AXP515
- **USB1:** Host (Type-A), EHCI+OHCI
- **USB2:** Host (Type-A), xHCI DWC3 SuperSpeed+

### Display

- **HDMI:** HDMI 2.0 port (full-size)
- **MIPI DSI:** 4-lane DSI for LCD panels
- **eDP:** Embedded DisplayPort (optional, shared with DSI pins)

### Audio

- **HDMI audio:** Via I2S3
- **Analog audio:** ES8388 codec on TWI7
- **Digital MIC:** Onboard DMIC

### GPIO / Headers

- 40-pin GPIO header (shared with Raspberry Pi pinout)
- UART, SPI, I2C, PWM, GPIO exposed

---

## References

- [linux-sunxi A733 Wiki](https://linux-sunxi.org/A733) (if it exists yet)
- [Orange Pi 4 Pro Wiki](http://www.orangepi.org/html/hardWare/computerAndMicrocontrollers/details/Orange-Pi-4-Pro.html)
- Vendor kernel: `https://github.com/orangepi-xunlong/linux-orangepi` branch `orange-pi-6.6-sun60iw2`
- [sun55i-a523 Mainline](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/arch/arm64/boot/dts/allwinner/sun55i-a523.dtsi) (closest template)
