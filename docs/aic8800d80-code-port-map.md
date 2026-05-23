# AIC8800D80 Code Port Map

This map converts vendor file layout into an upstream-oriented split so work can
move in parallel without repeatedly re-discovering ownership.

## WiFi core and platform

- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_fdrv/rwnx_main.c`
  -> `drivers/net/wireless/aicsemi/aic8800/rwnx_main.c`
- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_fdrv/rwnx_msg_tx.c`
  -> `drivers/net/wireless/aicsemi/aic8800/rwnx_msg_tx.c`
- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_fdrv/rwnx_msg_rx.c`
  -> `drivers/net/wireless/aicsemi/aic8800/rwnx_msg_rx.c`
- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_fdrv/rwnx_platform.c`
  -> `drivers/net/wireless/aicsemi/aic8800/rwnx_platform.c`

## SDIO transport

- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_fdrv/aicwf_sdio.c`
  -> `drivers/net/wireless/aicsemi/aic8800/aicwf_sdio.c`
- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_bsp/aicsdio.c`
  -> split between transport probe code and platform power helper

## BSP power and chip-id hooks to remove

- `sunxi_wlan_set_power` -> regulator and GPIO descriptor controls
- `sunxi_wlan_get_oob_irq` -> DT IRQ parsing from device node
- `sunxi_mmc_rescan_card` -> standard MMC/card-detect behavior
- `sunxi_get_soc_chipid` -> `soc_device_match`

## Bluetooth path

- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_btlpm/aic8800_btlpm.c`
  -> do not port directly; use serdev/HCI pattern under `drivers/bluetooth/`
- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_btusb/`
  -> keep as reference only for firmware naming and patch sequencing

## Firmware entry points to preserve during first port

- `aicbt_init()` patch-table and patch-blob load ordering
- `aicwifi_patch_config()` patch-map setup after firmware upload
- `aicwifi_start_from_bootrom()` final handoff at `RAM_FMAC_FW_ADDR`
