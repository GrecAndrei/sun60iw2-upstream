# [RFC PATCH 4/6] Bluetooth: hci_uart: add AIC8800 serdev transport skeleton

## Scope

- Add generated skeleton transport driver: `drivers/bluetooth/hci_aic8800.c`
- Bind to DT compatible `aicsemi,aic8800d80-bt`
- Wire serdev open/close and initial UART setup (`max-speed`, RTS/CTS)
- Register/unregister `hci_dev` lifecycle

## Current Behavior

- Non-stub UART transport path is present (probe/remove/open/close/setup/send/flush)
- RX: H4 frame reassembly for Event/ACL/SCO/ISO from `serdev` receive callback into `hci_recv_frame`
- TX: `hdev->send` enqueues packets, prepends H4 type byte, drains via workqueue + `write_wakeup`
- Probe sets flow control and baud rate from generator JSON (`bt_uart_speed`), opens serdev, registers HCI device
- Remove unregisters/frees HCI, flushes and purges queues, closes serdev

## Remaining for Full Upstream Bringup

- Add controller-specific firmware pre-init handshake over UART
- Add reset/state machine and recoverable error handling
- Wire into final Bluetooth Kconfig/Makefile patch hunks for submission series

## Validation

- Compiles clean as object in Linux v7.0 tree:
  - `make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/bluetooth/hci_aic8800.o`
