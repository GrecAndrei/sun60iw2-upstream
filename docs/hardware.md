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

The tracked DTS now declares R-TWI0, the AXP8191, and the physical 1.8 V Wi-Fi
rails: BLDO5 for the PG SDIO bank and CLDO1 for the PM control bank. It also
describes both A733 pin controllers as hardware-managed I/O-voltage domains.

Those declarations are not an upstream-support claim. The standalone patch
series must carry the matching PMIC support before it can be applied as a
self-contained port, and the current candidate has not enumerated the SDIO
device on hardware. The debug tree remains an experimental integration build,
not an authority for implementation choices.

## Hardware-validation rule

A declaration becomes a validation claim only when a captured test identifies
the exact Image/DTB, source revision, serial or console output, and result.
Store such evidence outside permanent prose or in a dedicated test record;
refresh `status.md` afterward so source/artifact provenance remains visible.
