# A733 bootloader recovery

The Orange Pi 4 Pro SD card reserves the first 32 MiB for the vendor boot
chain. The ext4 root partition begins at sector 65536. The current recovery
work replaces only U-Boot's packaged BL33 image; it intentionally retains the
known-working boot0, monitor, and SCP firmware.

| Component | SD location | Handling |
|---|---:|---|
| boot0 | sector 16 | Preserve during ordinary U-Boot tests. |
| boot package | sector 32800 | Contains U-Boot, monitor, and SCP; replace this package only. |
| root partition | sector 65536 | Do not touch when updating U-Boot. |

The boot package must be at most 16,760,832 bytes, the gap between sectors
32800 and 65536. `scripts/build-a733-uboot.sh` checks this limit and records
the package layout and hashes.

## Build

The legacy Allwinner U-Boot is a reference dependency, not source imported
into this repository. Apply the tracked patch with `git am` or `git apply` to
the vendor source checkout, then build it with the verified ARM toolchain and
the Orange Pi packing tools:

```bash
./scripts/build-a733-uboot.sh \
  --source ../../references/orangepi-u-boot-sun60iw2 \
  --pack-root ../../tools/orangepi-build/external/packages/pack-uboot \
  --toolchain ../../artifacts/build-tools/toolchains/gcc-linaro-7.4.1-2019.02-x86_64_arm-linux-gnueabi/bin/arm-linux-gnueabi- \
  --out ../../artifacts/builds/u-boot-a733-reliable
```

Use [`../../bootloader/patches/0001-sunxi-a733-reliable-mmc-recovery.patch`](../../bootloader/patches/0001-sunxi-a733-reliable-mmc-recovery.patch)
with the exact source revision recorded in the generated `BUILD-INFO` file.
The build script keeps the package inputs and logs alongside the resulting
`boot_package.fex`; check `SHA256SUMS` before flashing.

The patch fixes the legacy block-cache aliasing that made `mmc 1` reuse the
first MMC descriptor, restores partition discovery, uses the real physical
MMC device number as the default, makes reset/calibration waits bounded, and
keeps failure diagnostics concise. It also disables persistent environment
writes, so recovery commands cannot silently modify the root filesystem.

## Flash and recover

Use the whole SD device, never its `p1` partition. The device must be
unmounted. The script copies all 32 MiB of reserved boot space before it writes
the package, then reads the exact written sectors back and verifies SHA-256:

```bash
./scripts/flash-a733-uboot.sh \
  --device /dev/sdX \
  --package ../../artifacts/builds/u-boot-a733-reliable/boot_package.fex \
  --backup-dir ../../artifacts/boot-backups/current
```

To restore the captured boot reservation, with the same whole-device path:

```bash
sudo dd if=orangepi4pro-sd-reserved-YYYYMMDD-HHMMSS.img of=/dev/sdX \
  bs=1M count=32 conv=fsync status=progress
```

## UART acceptance checks

After a power cycle, capture a complete serial log but report only the command
and result milestones. At the U-Boot prompt verify:

```text
mmc list
part list mmc 0
ls mmc 0:1 /boot
ls mmc 1:1 /boot
```

The first three commands must find the SD card and its partition. The last
command must fail rather than aliasing `mmc 0`. `mmc rescan` must return or
time out with one concise diagnostic, not hang indefinitely or dump register
pages. A Linux boot remains a separate kernel/DTB test: record the exact
Image, DTB, boot arguments, and UART output before claiming it successful.
