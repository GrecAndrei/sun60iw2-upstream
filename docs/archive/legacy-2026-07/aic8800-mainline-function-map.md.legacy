# AIC8800 Vendor-to-Mainline Function Map

This map captures current porting targets so vendor hooks can be replaced with
mainline APIs during code migration.

| vendor_symbol | subsystem | mainline_target | notes |
| :--- | :--- | :--- | :--- |
| `sunxi_wlan_set_power` | mmc / regulator / gpio | Regulator framework and GPIO descriptor APIs | Use DT `vmmc-supply` and enable GPIO in pwrseq path. |
| `sunxi_mmc_rescan_card` | mmc | `mmc_detect_change` | Use native card detect flow instead of vendor rescan hook. |
| `sunxi_wlan_get_bus_index` | mmc / sdio | `sdio_register_driver` | Use normal SDIO ID matching and probe order. |
| `sunxi_wlan_get_oob_irq` | cfg80211 / mac80211 | `of_irq_get` / `gpiod_to_irq` | Parse wake IRQ from DT `interrupts` property. |
| `sunxi_wlan_get_oob_irq_flags` | cfg80211 / mac80211 | `irq_get_trigger_type` | Use DT IRQ flags instead of vendor helper. |
| `sunxi_get_soc_chipid` | base / soc | `soc_device_match` | Standard SoC identification path. |
| `get_custom_mac_address` | cfg80211 / mac80211 | `of_get_mac_address` / `nvmem_cell_read` | Use DT or NVMEM-backed MAC source. |
| `aicbt_init` | bluetooth / serdev | `hci_uart_register_device` + serdev I/O | Re-implement in upstream BT transport driver. |
| `rwnx_plat_bin_fw_upload_android` | firmware | `request_firmware` | Replace Android-specific loader with firmware subsystem. |
| `aicwifi_patch_config` | cfg80211 / mac80211 | SDIO memory writes | Keep patch-map sequencing with standard SDIO accessors. |
| `aicwifi_start_from_bootrom` | cfg80211 / mac80211 | SDIO command / register write | Preserve final jump-to-firmware handoff semantics. |
