# Build guide

Run factory validation before creating an integration tree:

```bash
cd projects/sun60iw2-upstream
python3 scripts/validate-factory.py
```

`scripts/apply-patches.sh` requires a Git repository with configured author
identity. It applies only Git-format patch files in `patches/` and then copies
both A733 defconfigs into the target tree. The current tested baseline is a
clean Linux v7.1.3 checkout:

```bash
./scripts/apply-patches.sh /path/to/clean-linux-v7.1.3
cd /path/to/clean-linux-v7.1.3
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LOCALVERSION= sun60iw2_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- LOCALVERSION= -j"$(nproc)" Image dtbs modules
```

Expected outputs are `arch/arm64/boot/Image` and
`arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb`.

The AIC8800 driver is separate from the boot-baseline patches. See
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
