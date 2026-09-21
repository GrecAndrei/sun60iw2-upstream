# Build guide

Run repository and factory validation before changing an integration tree:

```bash
cd projects/sun60iw2-upstream
python3 scripts/check-repository-layout.py
python3 scripts/validate-factory.py
```

## Current integration build

There is no active reproducible patch series. `scripts/apply-patches.sh`
intentionally refuses the historical implicit series; use `--list` only to
inspect the archived/WIP inventory. The current integration reference is the
existing Linux v7.1.3 tree:

```bash
make -C ../../kernels/a733-v7.1.3 \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LOCALVERSION= \
  sun60iw2_defconfig
make -C ../../kernels/a733-v7.1.3 \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LOCALVERSION= -j"$(nproc)" \
  Image dtbs modules
```

Expected outputs are `arch/arm64/boot/Image` and
`arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb` inside that
kernel tree. A future clean-tree patch baseline must be regenerated and tested
as a complete sequence before these instructions may describe it as active.

The AIC8800 driver remains separate from any future boot-baseline patches. See
[`../aic8800.md`](../aic8800.md) before exporting it to a Linux tree.

## Update an existing SD boot partition

`scripts/update-sd-boot.sh` updates only the existing rootfs partition's boot
files; it never repartitions or writes the whole SD device. It preserves
timestamped backups, writes and syncs the new files, then unmounts, remounts
the partition read-only, and verifies SHA-256 checksums before its final
unmount.

```bash
./scripts/update-sd-boot.sh \
  --device /dev/mmcblk0p1 \
  --image /path/to/linux/arch/arm64/boot/Image \
  --dtb /path/to/linux/arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb
```

The legacy recovery U-Boot has an independent source tree, toolchain, package
format, and guarded flash procedure. Follow
[`bootloader.md`](bootloader.md) rather than placing its binary in the kernel
tree.
