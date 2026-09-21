# Reverse-engineering the shipping image

The proven-working Orange Pi image is the primary source of vendor-behavior
evidence for this port. A vendor source checkout is **not** presumed to match
the image, board revision, configuration, or shipped binaries, and is not more
authoritative than direct reverse engineering of those binaries.

## Evidence order

Use evidence in this order:

1. Reproducible observations from the exact working image: extracted DTB,
   shipped kernel, modules, firmware, bootloader, and runtime/register captures.
2. Independent hardware documentation and current upstream interfaces.
3. Vendor source as secondary explanatory material only, after checking it
   against the image artifacts.

A convenient name, comment, or register definition in vendor source may help
interpret a binary. It must not override contradictory DTB, disassembly, or
runtime evidence. Never copy vendor implementation code into reviewable source.

For every reverse-engineered claim, record the image identity, artifact hash,
address or symbol, observed operation, and remaining uncertainty. Compilation
is not hardware validation.

## Current reference image

The extracted reference is recorded under
`../../artifacts/re/vendor-iso-extract/SOURCE.txt`:

- Orange Pi 4 Pro image version 1.0.6, Ubuntu Jammy
- shipped kernel `5.15.147-sun60iw2`
- extracted DTB SHA-256
  `d49dfb0b83234aa31f153348a7f6c92098642c780d5939a531f590a30cf97b77`
- extracted kernel Image SHA-256
  `fa1f28e4e6b53dc5976e626d3d104f5ac94255bd2df3e5e676ebba50eab81f9a`

Recompute hashes before relying on a re-extracted artifact.

## CCU console-handoff finding

The last observed bring-up failure was loss of the live UART during main-CCU
registration. The earlier workaround merely skipped eager PLL_REF enabling.
That was incomplete because `sys-24M` remained a CCF child of PLL_REF, allowing
a later functional-clock prepare to acquire PLL_REF again.

Direct evidence from the working image is stronger:

- The decompiled shipping DTB declares `sys24M` as an independent 24 MHz
  `fixed-clock`.
- `of_sun60iw2_ccu_init` is at `0xffffffc009397838` in the shipped kernel
  (`System.map` plus raw Image disassembly).
- Before calling `sunxi_ccu_probe`, that initializer writes CCU offsets `0x26c`
  (bits 31 and 27) and `0x5c0` (bits 31 and 29).
- The initializer contains no explicit write to PLL_REF control offset `0x000`
  before registration.

Therefore the mainline model keeps `sys-24M` as an independent fixed-rate
clock and leaves PLL_REF in its firmware-selected state during probe. This
prevents console and other 24 MHz functional consumers from implicitly
enabling PLL_REF.

The vendor source happens to corroborate these observations, but the extracted
DTB and shipped-kernel disassembly are the basis for the change.

## Reproducing the disassembly

From the workspace root:

```bash
sha256sum artifacts/re/vendor-iso-extract/{vendor-sun60i-a733-orangepi-4-pro.dtb,vmlinux-5.15.147-sun60iw2}
aarch64-linux-gnu-objdump -D -b binary -m aarch64 \
  --adjust-vma=0xffffffc008000000 \
  --start-address=0xffffffc009397838 \
  --stop-address=0xffffffc009397920 \
  artifacts/re/vendor-iso-extract/vmlinux-5.15.147-sun60iw2
```

The reconstructed symbol map is
`../../artifacts/re/ubuntu-v5.15.147/System.map`; the bounded captured output
and provenance note are under
`../../artifacts/re/a733-ccu-console-handoff/`. Keep large extraction and
disassembly outputs under `artifacts/`, not in the source repository.
