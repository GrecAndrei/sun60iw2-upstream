# Ethernet Bringup Plan

## Goal
Bring up wired GMAC0 Ethernet on Orange Pi 4 Pro with a minimal, safe mainline path:
- kernel config enables networking
- DT describes GMAC0, pinmux, MDIO, and PHY
- stmmac glue accepts the A733-compatible hardware path
- board boots, probes PHY, links, and passes DHCP/ping

## Current State
- SD boot reaches BusyBox userspace
- mainline A733 has CCU, pinctrl, MMC, and UART working
- thermal monitoring is now working; `/sys/class/thermal` exposes all 5 A733 zones
- `CONFIG_NETDEVICES` is currently off in `.config`
- `dwmac-sun55i.c` only matches `sun55i-a523-gmac200`
- A733 DTS currently has no Ethernet node in the upstream tree
- Vendor DTS shows GMAC0 at `0x04500000` with RGMII pinmux and PHY at MDIO address 1
- Vendor BSP confirms A733 GMAC uses `allwinner,sunxi-gmac-210` + `snps,dwmac-5.20`, no `syscon` property
- Vendor BSP uses GMAC0 clocks/resets `{gmac0, gmac0_mbus, gmac0_phy, gmac_ptp}` and resets `{gmac0_axi, gmac0}`

## Strategy
1. Keep the first patch set as small as possible.
2. Prefer mainline-compatible properties and drivers.
3. Avoid guessing syscon/power/reset details unless the probe log forces it.
4. Use vendor DTS only as a reference, not as a direct copy target.

## Detailed End-to-End Approach
1. Start from the current BusyBox-booting SD image so Ethernet work does not regress userspace.
2. Add only the minimum kernel config needed for networking and stmmac.
3. Add the GMAC0 device node and pinctrl in the SoC/board DTS files.
4. Extend the existing `dwmac-sun55i` glue only if A733 probe logs require it.
5. Build the driver and DTB first, then flash the SD boot partition.
6. Boot, capture probe logs, and iterate on the smallest failing detail.
7. After probe success, verify link, DHCP, and ping before considering the port complete.

## Bringup Sequence
### Pass 1
- Networking core enabled
- GMAC0 node appears in the device tree
- Driver probes and binds

### Pass 2
- PHY is detected on MDIO address 1
- Link carrier changes with cable insertion
- `eth0` appears in userspace

### Pass 3
- DHCP works
- Ping gateway works
- Ping internet works

### Pass 4
- Refine delays and power/reset handling only if required by signal integrity or probe failures

## Execution Steps
1. Identify the exact A733 GMAC wiring needed in mainline terms.
2. Enable the networking core and STMMAC stack in defconfig.
3. Extend `dwmac-sun55i.c` only as far as the hardware needs.
4. Add GMAC0 to `sun60i-a733.dtsi` and board overrides to `sun60i-a733-orangepi-4-pro.dts`.
5. Build `dwmac-sun55i.o`, `Image`, and `dtbs`.
6. Flash the boot partition and reboot.
7. Inspect probe logs and iterate on the smallest failing piece.

## Unknowns To Resolve
- Whether A733 needs any MAC-side RGMII delay programming beyond current `phy-mode = "rgmii"` defaults.
- Whether board-side PHY reset/power is needed for first probe.
- Whether the mainline node should start with `phy-mode = "rgmii"` or `"rgmii-id"`.
- Whether the board DTS already has everything needed for the PHY, or whether we must add a temporary fixed-supply/regulator hack for first probe.

## Progress Notes
- Added A733-compatible path in `dwmac-sun55i.c` and made syscon programming variant-dependent (required for A523, skipped for A733).
- Added optional PHY clock enable in `dwmac-sun55i.c` for boards that wire a dedicated PHY reference clock gate.
- Added A733 GMAC compatible support in `allwinner,sun8i-a83t-emac.yaml` with `snps,dwmac-5.20` fallback.
- Added `rgmii0_pins` + `gmac0` node to `sun60i-a733.dtsi` using A733 clock/reset IDs and MDIO PHY@1.
- Enabled `&gmac0` and `ethernet0` alias in `sun60i-a733-orangepi-4-pro.dts`.
- Thermal zones now register successfully; boot-time proc/sys/devtmpfs mounting was added for the BusyBox shell path.
- Started USB2 board-side bringup: added fixed `usb-host-vbus` regulator, wired `usb1_vbus-supply`, and enabled `ehci1`/`ohci1` in `sun60i-a733-orangepi-4-pro.dts` (runtime validation still pending).
- Added missing `reset-gpios` for `&gmac0_phy0` in `sun60i-a733-orangepi-4-pro.dts` (`PA14`, active-low), matching vendor SoC dtsi intent.
- Added `compatible = "ethernet-phy-ieee802.3-c22"` and `max-speed = <1000>` for `gmac0_phy0` in `sun60i-a733.dtsi` for parity with `gmac1_phy0`.
- Built a controlled 3-way reset matrix DTB set in `.tmp/`: `pa14-reset`, `ph16-reset`, and `no-reset` to eliminate reset-line uncertainty quickly.
- Created `.tmp/ethernet-reset-matrix.md` with exact flash/test commands and pass/fail criteria (`VALID` PHY read or non-`all_ff=32`).

## Checkpoints
- `eth0` appears in `/sys/class/net`
- PHY is visible on MDIO address 1
- Link carrier goes high with cable attached
- DHCP succeeds
- ICMP ping succeeds

## Status: ABANDONED (2026-04-27)

Ethernet bringup on Orange Pi 4 Pro GMAC0 was abandoned after multiple DTB-only flashes broke SD boot to shell. The underlying issue (MDIO all 0xFF / PHY not responding) was never resolved. Changes attempted: PHY reset GPIO (PA14, PH16, none), clock routing fixes (fixed-clock workaround for broken CCU generator chain), pinctrl bias/drive changes, and `clk_csr` forcing. None produced a valid PHY ID. Revisit after pinctrl R-domain or regulator bringup provides more GPIO/reset visibility.

## Notes
- Update this file as each step completes.
- Do not treat this as a committed doc; it is working context only.
