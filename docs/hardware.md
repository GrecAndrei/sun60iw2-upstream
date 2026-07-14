# Hardware declarations

This page records what the current files declare. It does not establish that a
peripheral is electrically present, powered, enumerated, or tested.

## Relevant source files

- Base SoC DTSI: `arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi`
- Board DTS: `arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`
- Local experimental board DTS:
  `../../kernels/a733-debug/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`

The generated [`status.md`](status.md) compares key declarations between the
tracked board DTS and the local debug DTS on every refresh.

## Current integration boundary

The tracked board DTS contains the boot-baseline description and AIC8800
nodes. The local debug tree additionally declares R-TWI0, an AXP8191 node, and
R-PIO supply assignments. Those debug-tree additions are not yet represented
by the tracked source and standalone patch series, so they must not be described
as upstream-port support.

## Hardware-validation rule

A declaration becomes a validation claim only when a captured test identifies
the exact Image/DTB, source revision, serial or console output, and result.
Store such evidence outside permanent prose or in a dedicated test record;
refresh `status.md` afterward so source/artifact provenance remains visible.
