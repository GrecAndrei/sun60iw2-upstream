<!-- GENERATED: scripts/refresh-documentation.py; do not edit manually. -->
# Live project state

This is an evidence report generated from the workspace. It records source and artifact state, not hardware-success claims.

Refresh with `python3 scripts/refresh-documentation.py`; verify with `python3 scripts/refresh-documentation.py --check`.

## Workspace roles

| Path | Role | Observable state |
|---|---|---|
| `projects/sun60iw2-upstream/` | tracked source and generator repository | `feature/a733-boot-recovery`; source Git changes are intentionally omitted |
| `kernels/a733-v7.1.3/` | primary integration build (`a733-v7.1.3`) | `debug/a733-v7.1.3` at `215ddda0a`; 19 working-tree change(s) |
| `kernels/mainline-v7/` | Linux v7.0 comparison / export tree | `detached` at `028ef9c96`; 18 working-tree change(s) |
| `kernels/a733-debug/` | experimental worktree only | `detached` at `ad299312e`; 20 working-tree change(s) |
| `references/orangepi-vendor-linux-6.6/` | vendor reference tree | `orange-pi-6.6-sun60iw2` at `8a9be72c9`; 0 working-tree change(s) |
| `projects/sun60iw2-upstream.wiki/` | canonical local wiki checkout | `master` at `d05d8ac`; 0 working-tree change(s) |

The source checkout's revision and Git-change list are intentionally omitted: committing this generated file must not make it stale by changing the state it reports.

## Generated-source validation

- Result: **PASS** — 51/51 checks passed; 0 failed.

## Integration build artifacts (`a733-v7.1.3`)

- `kernels/a733-v7.1.3/arch/arm64/boot/Image`: 13,388,288 bytes; modified 2026-07-30T20:43+03:00
- `kernels/a733-v7.1.3/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb`: 20,360 bytes; modified 2026-07-30T20:36+03:00

## Debug build artifacts (experimental)

- `kernels/a733-debug/arch/arm64/boot/Image`: 10,353,152 bytes; modified 2026-07-15T22:14+03:00
- `kernels/a733-debug/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb`: 17,721 bytes; modified 2026-06-16T21:08+03:00
- Artifact presence and timestamps only prove a local build output exists; they do not prove the image was booted successfully.

## Current Device Tree declarations

| Declaration | Source repository | Integration tree | Debug tree |
|---|---:|---:|---:|
| `mmc1 enabled` | yes | yes | yes |
| `AXP8191 node (`x-powers,axp8191`)` | yes | yes | yes |
| `AXP DCDC3 (big CPU supply)` | yes | yes | no |
| `AXP DCDC5 (little CPU supply)` | yes | yes | no |
| `CPU OPP tables (`sun60i-a733-cpu-opp.dtsi`)` | yes | yes | no |
| `THS nvmem calibration wired` | yes | yes | no |
| `CPU thermal zones (70/90 passive)` | yes | yes | no |
| `R-TWI0 enabled` | yes | yes | yes |
| `R-PIO PL supply declared` | yes | yes | yes |

These rows describe DTS text only. They do not establish driver availability, electrical behavior, or hardware success. Subsystem guides record validated runtime steps.

## Uncommitted integration changes

### Integration `a733-v7.1.3`
- ` M arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`
- ` M arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi`
- ` M arch/arm64/configs/sun60iw2_defconfig`
- ` M arch/arm64/configs/sun60iw2_minimal_defconfig`
- ` M drivers/clk/sunxi-ng/ccu-sun60i-a733.c`
- ` M drivers/mfd/axp20x.c`
- ` M drivers/net/wireless/aicsemi/aic8800/cfg80211_core.c`
- ` M drivers/net/wireless/aicsemi/aic8800/core_fw.c`
- ` M drivers/net/wireless/aicsemi/aic8800/core_types.h`
- ` M drivers/net/wireless/aicsemi/aic8800/fw_protocol.c`
- ` M drivers/net/wireless/aicsemi/aic8800/fw_protocol.h`
- ` M drivers/net/wireless/aicsemi/aic8800/netdev_core.c`
- ` M drivers/net/wireless/aicsemi/aic8800/sdio_io.c`
- ` M drivers/net/wireless/aicsemi/aic8800/sdio_io.h`
- ` M drivers/net/wireless/aicsemi/aic8800/sdio_probe.c`
- ` M drivers/regulator/axp20x-regulator.c`
- ` M include/dt-bindings/clock/sun60i-a733-rtc.h`
- ` M init/main.c`
- `?? arch/arm64/boot/dts/allwinner/sun60i-a733-cpu-opp.dtsi`

### Linux v7.0
- ` M arch/arm64/boot/dts/allwinner/Makefile`
- ` M drivers/bluetooth/Kconfig`
- ` M drivers/bluetooth/Makefile`
- ` M drivers/net/wireless/Kconfig`
- ` M drivers/net/wireless/Makefile`
- `?? arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`
- `?? arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi`
- `?? arch/arm64/configs/sun60iw2_defconfig`
- `?? drivers/bluetooth/Makefile.aic`
- `?? drivers/bluetooth/hci_aic8800.c`
- `?? drivers/net/wireless/aicsemi/`
- `?? include/dt-bindings/clock/sun60i-a733-ccu.h`
- `?? include/dt-bindings/clock/sun60i-a733-cpupll-ccu.h`
- `?? include/dt-bindings/clock/sun60i-a733-r-ccu.h`
- `?? include/dt-bindings/clock/sun60i-a733-rtc.h`
- `?? include/dt-bindings/power/sun60i-a733-power.h`
- `?? include/dt-bindings/reset/sun60i-a733-ccu.h`
- `?? include/dt-bindings/reset/sun60i-a733-r-ccu.h`

### Debug worktree
- ` M arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`
- ` M arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi`
- ` M drivers/clk/sunxi-ng/ccu-sun60i-a733-cpupll.c`
- ` M drivers/clk/sunxi-ng/ccu-sun60i-a733-r.c`
- ` M drivers/clk/sunxi-ng/ccu-sun60i-a733-rtc.c`
- ` M drivers/clk/sunxi-ng/ccu-sun60i-a733.c`
- ` M drivers/i2c/busses/Kconfig`
- ` M drivers/i2c/busses/Makefile`
- ` M drivers/mfd/axp20x-i2c.c`
- ` M drivers/mfd/axp20x.c`
- ` M drivers/mmc/host/sunxi-mmc.c`
- ` M drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c`
- ` M drivers/pinctrl/sunxi/pinctrl-sunxi.c`
- ` M drivers/pinctrl/sunxi/pinctrl-sunxi.h`
- ` M drivers/regulator/axp20x-regulator.c`
- ` M include/linux/mfd/axp20x.h`
- `?? Image`
- `?? arch/arm64/configs/sun60iw2_defconfig`
- `?? arch/arm64/configs/sun60iw2_minimal_defconfig`
- `?? drivers/i2c/busses/i2c-sunxi.c`

## Documentation contract

Permanent docs describe ownership, procedure, and the last recorded capability boundary. This generated file is the live evidence authority for Git/artifact/DTS/factory state; archived notes are intentionally excluded from current guidance.
