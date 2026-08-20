# Hardware declarations

This page records what the current files declare. It does not by itself prove
electrical presence, enumeration, or runtime success — pair it with
[`status.md`](status.md) and the subsystem guides for evidence rules.

## Relevant source files

- Base SoC DTSI: `arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi`
- CPU OPP tables: `arch/arm64/boot/dts/allwinner/sun60i-a733-cpu-opp.dtsi`
- Board DTS: `arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`
- Integration kernel: `../../kernels/a733-v7.1.3/`
- Debug worktree (experimental only): `../../kernels/a733-debug/`

The generated [`status.md`](status.md) compares key declarations between the
tracked board/SoC DTS and the integration/debug trees on every refresh.

## Current integration boundary

### Always-on / bring-up rails

- R-TWI0 + AXP8191 on the board
- Wi-Fi: BLDO5 (PG SDIO bank) and CLDO1 (PM control), both 1.8 V
  `regulator-always-on`; `mmc1` has no `vmmc`/`vqmmc`
- CPU DVFS: DCDC5 → little cluster (`cpu0`–`cpu5`), DCDC3 → big cluster
  (`cpu6`–`cpu7`); both always-on. **Do not declare DCDC1** (AXP probe
  abort when `get_voltage` fails under `apply_uV`)
- Undeclared rails keep the bootloader voltage

### Clocks / thermal / cpufreq (SoC + board)

- CPU clocks use `CLK_CPU_L` / `CLK_CPU_B` (mux with `CLK_SET_RATE_PARENT`)
- Plain `operating-points-v2` tables (max vendor-bin voltages; no
  `sun50i-cpufreq-nvmem` for A733 yet)
- THS `@2522000` with `nvmem-cells = <&ths_calibration>`
- Thermal zones: little (sensor 3), big (sensor 0), DDR (1), NPU (2), GPU (4)
- CPU passive trips **70 / 90 °C** (hyst 2 °C), critical **110 °C**;
  cooling-maps to cluster CPUs with `contribution = <1024>`
- GPU/NPU/DDR zones are sensor/critical only until those devices exist as
  coolers

See [`guides/thermals.md`](guides/thermals.md) for config, flash, and
board check steps. Thermal **board** verification was not completed when
this text was written; declarations and Image/DTB build are in tree.

### MMC

- `mmc0` (SD root) and `mmc1` (Wi-Fi SDIO) both list STORE/MBUS/MSI_LITE
  gate clocks so Wi-Fi enable does not hang root I/O
- Pin controllers: hardware-managed I/O-voltage domains (auto-hard /
  TYPE_4 layout)

## Trees

| Tree | Role |
|---|---|
| `projects/sun60iw2-upstream/` | Reviewable source |
| `kernels/a733-v7.1.3/` | Primary integration build / flash target |
| `kernels/a733-debug/` | Experimental only; not authority for upstream choices |

## Hardware-validation rule

A declaration becomes a validation claim only when a captured test identifies
the exact Image/DTB, source revision, serial or console output, and result.
Store evidence outside permanent prose or in a dedicated test record; refresh
`status.md` afterward so source/artifact provenance remains visible.
