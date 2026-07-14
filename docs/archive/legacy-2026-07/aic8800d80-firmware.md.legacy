# AIC8800D80 Firmware Notes

This note captures where the AIC8800D80 firmware is consumed in the vendor
driver stack and which blob names are expected, so we can preserve/reuse the
firmware loading flow while upstreaming board support.

## Source blobs

Current local source directory (provided by user):

- `/home/grec-alexander/Downloads/aic8800d80`

Expected runtime target on Linux rootfs:

- `/lib/firmware/aic8800d80/`

## Relevant blob names (vendor driver)

From `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_bsp/aic_bsp_8800d80.c`:

- `fw_adid_8800d80.bin`
- `fw_patch_8800d80.bin`
- `fw_patch_table_8800d80.bin`
- `fmacfw_8800d80.bin`
- `lmacfw_rf_8800d80.bin`

U02 variants:

- `fw_adid_8800d80_u02.bin`
- `fw_patch_8800d80_u02.bin`
- `fw_patch_table_8800d80_u02.bin`
- `fw_patch_8800d80_u02_ext`
- `fmacfw_8800d80_u02.bin`
- `fmacfw_8800d80_h_u02.bin`
- `lmacfw_rf_8800d80_u02.bin`

## Cortex-M side handoff path

The vendor stack loads patch metadata/blobs through the BSP layer before
starting WiFi firmware:

- `aicbt_init()` unpacks patch info/table and uploads BT patch blobs
- `aicwifi_start_from_bootrom()` starts the WiFi app at `RAM_FMAC_FW_ADDR`

See:

- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_bsp/aic_bsp_8800d80.c`
- `linux-orangepi/bsp/drivers/net/wireless/aic8800/aic8800_fdrv/rwnx_platform.c`

## Follow-up

When doing the firmware-isolation task, preserve:

1. Blob file names exactly (driver matches by name)
2. U01/U02 variant split
3. Patch table + ext patch files, not only `fmacfw` images
