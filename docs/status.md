<!-- GENERATED: scripts/refresh-documentation.py; do not edit manually. -->
# Live project state

This is an evidence report generated from the workspace. It records source and artifact state, not hardware-success claims.

Refresh with `python3 scripts/refresh-documentation.py`; verify with `python3 scripts/refresh-documentation.py --check`.

## Workspace roles

| Path | Role | Observable state |
|---|---|---|
| `projects/sun60iw2-upstream/` | tracked source and generator repository | `feature/a733-boot-recovery`; source Git changes are intentionally omitted |
| `kernels/mainline-v7/` | Linux v7.0 integration tree | `detached` at `028ef9c96`; 18 working-tree change(s) |
| `kernels/a733-debug/` | local experimental integration/build worktree | `detached` at `ad299312e`; 20 working-tree change(s) |
| `references/orangepi-vendor-linux-6.6/` | vendor reference tree | `orange-pi-6.6-sun60iw2` at `8a9be72c9`; 0 working-tree change(s) |
| `projects/sun60iw2-upstream.wiki/` | canonical local wiki checkout | `master` at `d05d8ac`; 0 working-tree change(s) |

The source checkout's revision and Git-change list are intentionally omitted: committing this generated file must not make it stale by changing the state it reports.

## Generated-source validation

- Result: **FAIL** — 45/51 checks passed; 6 failed.
- Failing checks:
  - `ccu_committed_fresh_match:main`
  - `ccu_committed_fresh_match:r`
  - `ccu_committed_fresh_match:rtc`
  - `ccu_committed_fresh_match:cpupll`
  - `pinctrl_committed_fresh_match`
  - `pinctrl_mainline_pattern_match`

## Local debug build artifacts

- `kernels/a733-debug/arch/arm64/boot/Image`: 11,680,256 bytes; modified 2026-06-16T23:25+03:00
- `kernels/a733-debug/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb`: 17,721 bytes; modified 2026-06-16T21:08+03:00
- Artifact presence and timestamps only prove a local build output exists; they do not prove the image was booted successfully.

## Current Device Tree declarations

| Declaration | Source repository | Debug tree |
|---|---:|---:|
| `mmc1` enabled | yes | yes |
| AXP8191 node (`x-powers,axp8191`) | no | yes |
| R-TWI0 enabled | no | yes |
| R-PIO PL supply declared | no | yes |

The debug tree has declarations that are absent from the tracked source tree. Treat it as an experimental integration snapshot until those changes are represented by source, generated outputs, and reviewable patches.

## Uncommitted integration changes

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

The permanent documentation describes workflow and ownership only. This generated file is the sole status authority; archived notes are intentionally excluded from current guidance.
