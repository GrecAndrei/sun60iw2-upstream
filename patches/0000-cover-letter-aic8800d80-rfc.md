Subject: [RFC 0/6] sun60i: Orange Pi 4 Pro AIC8800D80 WiFi/BT bringup

This series starts upstream bringup for the onboard AIC8800D80 on Orange Pi 4
Pro (Allwinner A733 / sun60i).

Current board-side wiring in this tree already enables:

- `mmc1` non-removable path with `mmc-pwrseq-simple` for WiFi power sequencing
- `uart1` with RTS/CTS pinmux for Bluetooth transport

The remaining work is driver-side upstreaming and removal of vendor BSP hooks.

Series outline:

1. dt-bindings: document AIC8800 SDIO WiFi and UART BT nodes
2. wifi: add initial AIC8800 core integration
3. wifi: add SDIO transport support
4. bluetooth: add AIC8800 UART transport integration
5. arm64: dts: allwinner: wire AIC8800D80 on Orange Pi 4 Pro
6. docs/tests: add firmware and bringup validation notes

Known BSP dependencies to remove are tracked in:

- `docs/aic8800d80-bsp-debt.csv`

Firmware constraints for first upstream iterations are tracked in:

- `docs/aic8800d80-firmware.md`

Bringup checklist and acceptance gates are tracked in:

- `docs/aic8800d80-upstream-checklist.md`

This RFC is intentionally split so bindings and board DTS changes can be
reviewed independently from driver internals.
