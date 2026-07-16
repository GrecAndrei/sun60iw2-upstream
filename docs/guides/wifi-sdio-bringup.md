# A733 Wi-Fi SDIO bring-up

This procedure applies to the Orange Pi 4 Pro's soldered AIC8800 SDIO device.
It is deliberately limited to device enumeration; loading firmware or the
AIC driver comes only after `mmc1` responds.

## Established wiring and software state

- SDIO uses `PG0` through `PG5` on SMHC1 (`mmc1`), with mux value 2.
- BLDO5 powers the PG domain and CLDO1 powers the PM control domain; both are
  fixed at 1.8 V.
- `WL_REG_ON` is PM1, active high. `mmc-pwrseq-simple` therefore models it as
  an active-low reset. PM0 is host wake and is not needed for enumeration.
- A733 PIO and R-PIO choose I/O voltage in hardware. Their pinctrl drivers use
  `SUNXI_PINCTRL_AUTO_POWER_SWITCH` so they do not write the unrelated generic
  power-mode registers.

The latest hardware run reached the root shell with both regulators enabled at
1.8 V and PM1 physically high. It also verified the A733 v5p3 SMHC clock
contract: a 400 kHz card request uses an 800 kHz module clock in new timing
mode. CMD52 still timed out, which establishes a host-to-device response
failure after reset, rails, pinmux, and initial clock setup; it does not
establish a failed Wi-Fi chip.

## Current diagnostic baseline

The tested kernel image includes the native A733 R-PIO driver, the A733-only
2x SMHC clock quirk, and the one-line `a733-sdio` diagnostic. The native R-PIO
driver replaces the A523 compatibility fallback and removes its incorrect
manual pad-voltage programming. The latest run reported
`clock=400000 actual=400000 mclk=800000`, then a response timeout. The normal
updater verifies the mounted card, copies Image and DTB, hashes the copied
files, and unmounts before removal.

After one power cycle, retain only these lines from UART:

```text
... pwrseq diagnostic: reset logical=0 physical=1
... a733-sdio: ...
... mmc1: ...
```

Expected success is an `mmc1: new high speed SDIO card` line. The current
timeout baseline is `int=00000104 status=000001e6` after the correct 800 kHz
module clock. Preserve these values and do not change voltage or timing
properties blindly. The next decision requires a direct electrical measurement
of SDIO CMD/CLK and the two 1.8 V rails.
