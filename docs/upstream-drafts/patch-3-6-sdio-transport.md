# [RFC PATCH 3/6] wifi: aic8800: add SDIO transport layer

## Scope

- Add generated SDIO transport files:
  - `docs/upstream-drafts/kernel-files/drivers/net/wireless/aicsemi/aic8800/sdio_probe.c`
  - `docs/upstream-drafts/kernel-files/drivers/net/wireless/aicsemi/aic8800/sdio_io.c`
  - `docs/upstream-drafts/kernel-files/drivers/net/wireless/aicsemi/aic8800/sdio_io.h`
- Register SDIO ID table and probe/remove lifecycle
- Wire firmware download/start path and RX/TX transport queue model

## Current Behavior

- RX: IRQ schedules deferred drain worker with bounded budget and malformed-frame guards
- TX: queued worker with retry/backoff, netdev backpressure, watchdog, and recovery path
- Recovery: watchdog escalation to transport reinit with in-progress/cooldown guard
- Observability: debugfs `stats` and `control` endpoints for runtime transport state

## Validation

- Module build passes on Linux v7.0 arm64:
  - `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- M=drivers/net/wireless/aicsemi/aic8800 modules`
  - `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- W=1 M=drivers/net/wireless/aicsemi/aic8800 modules`
