# Script catalog

Run scripts from the repository root unless a guide says otherwise. Defaults
are workspace-relative where possible. Inspect device and mount arguments
before every command that uses `sudo`.

## Safety levels

- **Check** — reads source or creates ignored validation output.
- **Tree write** — regenerates source or modifies a supplied kernel checkout.
- **Board write** — changes an SD card, boot files, raw sectors, or a running
  board. These commands require deliberate target verification.

## Validation and documentation (Check)

- `check-repository-layout.py` — validate links, path hygiene, script catalog,
  patch boundaries, and tracked-output rules.
- `validate-factory.py` — deterministic CCU/pinctrl factory validation.
- `refresh-documentation.py` — regenerate or check `docs/status.md`.
- `report-aic8800-progress.sh` — write ignored local AIC8800 validation summary.

## AIC8800 generation and compile checks

- `generate-aic8800-upstream.sh` — **Tree write**; regenerate owned driver and
  review snapshot.
- `export-aic8800-kernel-skeleton.sh` — **Tree write**; export into a supplied
  Linux tree.
- `check-aic8800-dtb.sh`, `check-aic8800-skeleton.sh`, and
  `check-aic8800-skeleton-full.sh` — **Tree write**; regenerate/export before
  compile checks, so use a checkout intended for integration testing.

## Kernel, bootloader, and media operations

- `apply-patches.sh` — guard/list command. It refuses application because no
  validated active Linux patch series exists.
- `update-sd-boot.sh` — **Board write**; guarded Image/DTB update of an explicit
  boot partition with backup and read-back verification.
- `build-a733-uboot.sh` — build the separate legacy recovery U-Boot package.
- `flash-a733-uboot.sh` — **Board write**; backup, raw write, and verify a U-Boot
  package on an explicitly selected device.
- `fix-vendor-root-mmcblk1.sh` — **Board write**; repair vendor root-device boot
  configuration on mounted media.
- `flash-vendor-for-dump.sh` and `restore-mainline-boot.sh` — **Board write**;
  temporary vendor-kernel comparison workflow and its restore operation.

## Remote board deployment and access

- `find-a733-host.sh` — locate the board and verify its pinned SSH host key.
- `a733-ssh.sh` — connect through the verified discovery helper.
- `deploy-a733-ota.sh` — **Board write**; build, upload, and optionally reboot
  into a guarded one-shot trial.
- `a733-wifi-healthcheck.sh` — check association, routing, SDIO state, and fatal
  transport counters.
- `install-aic8800-modules.sh` — **Board write**; install Image, DTB, modules,
  firmware, and boot helpers onto a selected root filesystem.

## Installed board assets and diagnostics

The deployment/install scripts consume these files; they are not general host
commands unless copied to the board:

- Boot/OTA: `a733-boot.sh`, `a733-ota-commit.sh`,
  `a733-ota-commit.service`, `a733-ota-trial-boot.txt`.
- Wi-Fi startup: `a733-sdio-clock.sh`, `aic8800-wifi-bringup.sh`,
  `aic8800-wifi.service`, `wifi-up.sh`.
- Wi-Fi tests: `wifi-monitor.sh`, `wifi-station.sh`,
  `wifi-inject-probe.py`, `sdio-probe.sh`, `sdio-electrical-checklist.txt`.

Keep credentials, firmware blobs, captured logs, staged boot files, and rootfs
content outside this repository under workspace `artifacts/`.
