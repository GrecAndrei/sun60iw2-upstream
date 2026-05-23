# Patch 2/6 Draft: AIC8800 WiFi Core Skeleton

Goal: prepare an upstream-friendly driver split for core WiFi logic before SDIO
transport is introduced in patch 3/6.

## Scope for patch 2/6 only

- Add vendor folder hooks under `drivers/net/wireless/`
- Add AIC8800 core Kconfig options
- Add minimal compile-safe core files
- Keep transport-specific code out of this patch

## File plan

- `drivers/net/wireless/Kconfig`
  - source `drivers/net/wireless/aicsemi/Kconfig`
- `drivers/net/wireless/Makefile`
  - add `obj-$(CONFIG_WLAN_VENDOR_AICSEMI) += aicsemi/`
- `drivers/net/wireless/aicsemi/Kconfig`
- `drivers/net/wireless/aicsemi/Makefile`
- `drivers/net/wireless/aicsemi/aic8800/Kconfig`
- `drivers/net/wireless/aicsemi/aic8800/Makefile`
- `drivers/net/wireless/aicsemi/aic8800/core_main.c`
- `drivers/net/wireless/aicsemi/aic8800/core_fw.c`
- `drivers/net/wireless/aicsemi/aic8800/core_types.h`

## Patch split boundary

Keep these for patch 3/6:

- SDIO IDs and probe/remove
- SDIO IRQ handling
- bus read/write wrappers

Keep these for patch 4/6:

- UART BT transport
- BT patch loading hooks

## Compile target

- `CONFIG_AIC8800_CORE=m`
- `make M=drivers/net/wireless/aicsemi/aic8800`

## Non-goals in patch 2/6

- No full feature parity with vendor driver
- No advanced power-save path
- No Android wake lock compatibility
