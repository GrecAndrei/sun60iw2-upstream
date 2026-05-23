# AIC8800D80 Upstream Checklist

This checklist tracks the minimum upstream path for Orange Pi 4 Pro WiFi/BT
with the onboard AIC8800D80.

Regenerate draft artifacts from structured data:

- `./scripts/generate-aic8800-upstream.sh`
- `./scripts/export-aic8800-kernel-skeleton.sh <linux-tree-root>`
- `./scripts/check-aic8800-skeleton.sh <linux-tree-root>`
- `./scripts/check-aic8800-skeleton-full.sh <linux-tree-root>`
- `./scripts/report-aic8800-progress.sh`

## 0) Automation milestones

- [x] JSON source-of-truth for AIC upstream artifacts is in place
- [x] Draft bindings/DTS/kernel skeleton files are generator-produced
- [x] Repeatable export script to Linux tree exists
- [x] Repeatable progress snapshot report exists
- [x] Compile-check run passed against a full Linux tree
- [x] One-shot regen+export+compile+W=1 validation script exists

## 0.1) Generated WiFi skeleton status

- [x] SDIO probe path has structured error unwind and deinit ordering
- [x] SDIO host init/deinit helpers call core SDIO enable/disable primitives
- [x] cfg80211 register/unregister scaffold is generated
- [x] cfg80211 scan/connect/disconnect event stubs are generated
- [x] cfg80211 connect/disconnect updates internal link state scaffolding
- [x] netdev register/unregister scaffold is generated
- [x] firmware fallback list is generated from JSON data
- [x] firmware SDIO download path (sdio_memcpy_toio) is generated
- [x] bootrom start-app handoff is generated
- [x] netdev TX path is wired to SDIO transport callback (no unconditional drop)
- [x] SDIO IRQ path drains RX frames into net stack (`netif_rx` path)
- [x] Runtime IO telemetry counters are collected and emitted at unregister
- [x] RX malformed-frame drop guard and optional metadata header parsing are implemented
- [x] RX soft-resync path handles oversized frame headers without hard-failing IRQ drain loop
- [x] WiFi TX path uses SDIO transport queue + worker (batched drain model)
- [x] WiFi TX worker has configurable retry/backoff for transient SDIO write failures
- [x] SDIO IRQ handler is minimal and schedules deferred RX worker drain
- [x] RX delivery uses deferred queue + submit worker (bounded budget)
- [x] netdev TX backpressure (stop/wake) is wired to SDIO TX queue depth
- [x] TX watchdog detects stalled queue drain and nudges recovery work
- [x] TX watchdog escalates repeated stalls to automatic SDIO transport reinit
- [x] transport reinit preserves queued/in-flight TX frames for post-reinit drain
- [x] transport reinit uses in-progress and cooldown guards to avoid reinit storms
- [x] debugfs runtime stats endpoint is exposed for live transport counters
- [x] debugfs transport control endpoint supports manual recovery actions
- [x] debugfs stats expose reinit in-progress/cooldown state
- [x] debugfs transport control supports firmware override/load/unload/start hooks
- [x] compile-check passed (0 errors, 0 warnings) against Linux v7.0 arm64
- [x] full kernel Image + modules build passed (aic8800_core.ko + aic8800_sdio.ko)
- [x] project tree drivers/ populated from generated skeleton
- [x] BT firmware fallback helper scaffolding is generated from JSON data
- [x] BT serdev/HCI transport scaffold is generated and compile-checked (`hci_aic8800.o`)
 - [x] BT transport has non-stub H4 RX/TX data path (serdev receive/write wakeup + HCI send/flush)
 - [x] Real SDIO IDs and TX/RX port constants extracted from vendor BSP

## 1) Remove BSP dependencies from vendor flow

- [x] Replace `sunxi_wlan_set_power` with regulator and GPIO controls
- [x] Replace `sunxi_mmc_rescan_card` usage with normal MMC detect flow
- [x] Replace `sunxi_wlan_get_bus_index` with native SDIO matching
- [x] Replace `sunxi_wlan_get_oob_irq` and flag helpers with DT IRQ parsing
- [x] Replace `sunxi_get_soc_chipid` with standard `soc_device` matching
- [x] Replace custom MAC access with `local-mac-address` and/or NVMEM

Reference inventory: `docs/aic8800d80-bsp-debt.csv`.

## 2) Upstream patch series shape

- [x] 1/6 dt-bindings for AIC8800 SDIO WiFi and UART BT
- [x] 2/6 WiFi core driver skeleton (cfg80211/mac80211 integration)
- [x] 3/6 SDIO transport layer for AIC8800
- [x] 4/6 Bluetooth UART transport integration (serdev/HCI)
- [x] 5/6 Board DTS wiring for Orange Pi 4 Pro
- [x] 6/6 Documentation and bringup self-test notes

Draft binding seeds prepared in this repo:

- `docs/upstream-drafts/aicsemi,aic8800.yaml`
- `docs/upstream-drafts/aicsemi,aic8800-bt.yaml`
- `docs/upstream-drafts/patch-1-6-dt-bindings.md`

Patch 2/6 core skeleton draft files:

- `docs/upstream-drafts/patch-2-6-driver-skeleton.md`
- `docs/upstream-drafts/kernel-files/drivers/net/wireless/aicsemi/`

Patch 3/6 SDIO transport draft file:

- `docs/upstream-drafts/patch-3-6-sdio-transport.md`

Patch 6/6 documentation draft files:

- `docs/upstream-drafts/patch-6-6-docs-and-selftest.md`
- `docs/upstream-drafts/aic8800-bringup-selftest.md`

## 3) Firmware loading constraints

- [x] Preserve vendor blob names for first bringup
- [x] Preserve U01/U02 split during initial upstream port
- [x] Preserve patch table and ext patch flow, not only `fmacfw`
- [x] Keep runtime search path under `/lib/firmware/aic8800d80/`

Reference: `docs/aic8800d80-firmware.md`.

## 4) Validation gates per revision

- [x] Board DTB build clean (`allwinner/sun60i-a733-orangepi-4-pro.dtb`)
- [x] `make dt_binding_check` clean for new YAML schemas
- [ ] WiFi probe: `mmc1` enumerates and driver binds
- [ ] Firmware requests visible in `dmesg` with expected filenames
- [ ] `iw dev` shows `wlan0` after successful bringup
- [ ] BT probe: `hci0` appears and can be queried
