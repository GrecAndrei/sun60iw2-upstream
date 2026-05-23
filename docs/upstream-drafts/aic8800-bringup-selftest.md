# AIC8800 Bringup Self-Test Notes

## Preconditions

- Kernel tree exported with generated AIC8800 artifacts
- Orange Pi 4 Pro DTS includes `mmc1` WiFi node and `uart1` BT child node
- Firmware files staged under `/lib/firmware/aic8800d80/`

## Build + Static Validation

1. Run one-shot generator/build check:
   - `./scripts/check-aic8800-skeleton-full.sh <linux-tree-root>`
2. Run DTB validation:
   - `./scripts/check-aic8800-dtb.sh <linux-tree-root>`

## Runtime Bringup Checks

1. Boot board with generated kernel + DTB
2. Confirm SDIO enumeration and probe:
   - `dmesg | grep -i aic8800`
3. Confirm firmware requests:
   - `dmesg | grep -i firmware`
4. Confirm WiFi netdev presence:
   - `iw dev`
5. Confirm BT HCI presence:
   - `hciconfig -a`

## Transport Telemetry Checks

- Read debugfs transport stats:
  - `cat /sys/kernel/debug/aic8800_sdio/stats`
- Manual recovery controls:
  - `echo tx_recover > /sys/kernel/debug/aic8800_sdio/control`
  - `echo reinit > /sys/kernel/debug/aic8800_sdio/control`
  - `echo rx_purge > /sys/kernel/debug/aic8800_sdio/control`

## Firmware Override and Hook Controls

- Set runtime firmware override path:
  - `echo "fw_set aic8800d80/fmacfw_8800d80_u02.bin" > /sys/kernel/debug/aic8800_sdio/control`
- Clear override and return to default JSON-configured probe name:
  - `echo fw_clear > /sys/kernel/debug/aic8800_sdio/control`
- Firmware control hooks:
  - `echo fw_load > /sys/kernel/debug/aic8800_sdio/control`
  - `echo fw_reload > /sys/kernel/debug/aic8800_sdio/control`
  - `echo fw_start > /sys/kernel/debug/aic8800_sdio/control`
  - `echo fw_cycle > /sys/kernel/debug/aic8800_sdio/control`
  - `echo fw_unload > /sys/kernel/debug/aic8800_sdio/control`
