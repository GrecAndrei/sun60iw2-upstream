# Build guide

Run factory validation before creating an integration tree:

```bash
cd projects/sun60iw2-upstream
python3 scripts/validate-factory.py
```

`scripts/apply-patches.sh` requires a Git repository with configured author
identity. It applies only Git-format patch files in `patches/` and then copies
both A733 defconfigs into the target tree. Use a clean Linux v7.0 checkout:

```bash
./scripts/apply-patches.sh /path/to/clean-linux-v7.0
cd /path/to/clean-linux-v7.0
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- sun60iw2_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j"$(nproc)" Image dtbs
```

Expected outputs are `arch/arm64/boot/Image` and
`arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dtb`.

The AIC8800 driver is separate from the boot-baseline patches. See
[`../aic8800.md`](../aic8800.md) before exporting it to a Linux tree.
