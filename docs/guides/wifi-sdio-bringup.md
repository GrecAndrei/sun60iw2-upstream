# A733 Wi-Fi SDIO bring-up

This procedure applies to the Orange Pi 4 Pro's soldered AIC8800 SDIO device.
It is deliberately limited to device enumeration; loading firmware or the
AIC driver comes only after `mmc1` responds.

## Established wiring and software state

- SDIO uses `PG0` through `PG5` on SMHC1 (`mmc1`), with mux value 2.
- BLDO5 powers the PG domain and CLDO1 powers the PM control domain; both are
  fixed at 1.8 V and both are `regulator-always-on`, because nothing else
  holds them up once pinctrl skips the bank supplies.
- `mmc1` has **no** `vmmc-supply` / `vqmmc-supply` (vendor leaves them
  unwired; BLDO5/CLDO1 are always-on). Mainline `sunxi-mmc` must then set a
  default `ocr_avail` (2.8–3.4 V), or `mmc_select_voltage()` fails with
  "no support for card's volts" after the card answers CMD5/CMD52.
  unwired). Enumeration bring-up is high-speed only; UHS caps return after
  CMD5 works. See the rail ownership rule in `docs/aic8800.md`.
- `WL_REG_ON` is PM1, active high. `mmc-pwrseq-simple` therefore models it as
  an active-low reset, with the vendor's 50 ms PM1-to-rescan delay and 100 ms
  power-off-to-rescan delay. BLDO5/CLDO1 are shared with Bluetooth and remain
  enabled; the vendor's preceding 10 ms delay is between regulator enable and
  PM1, not part of the post-PM1 interval.
- A733 SMHC v5p3 host programming matches vendor 400 kHz defaults: CMD drive
  180°, DAT 90°, NTSR sample phases 0, SAMP_DL left alone (no
  `SAMP_DL_SW_EN`), and CRC detect `CSDC=3` with HS400 mode cleared in
  `EDSD` on every clock set (vendor `sunxi-mmc-v5p3x`).
- A733 PIO uses `SUNXI_PINCTRL_AUTO_POWER_SWITCH` (vendor `auto_hard`) so it
  does not claim `vcc-pg` or write `PIO_POW_MOD_SEL/CTL`; the hardware power
  detector / bootloader owns that decision. Main PIO uses
  `SUNXI_PINCTRL_SUN60_LAYOUT` (TYPE_4: bank `0x80` @ base `0x80`,
  `POW_MOD` @ `0x40`). Do **not** use D1 `NEW_REG_LAYOUT` or A523
  `ELEVEN_BANKS` on the main controller — those mux PG to the wrong
  offsets and leave SDIO pins unconfigured.

The authoritative vendor image is Orange Pi release 1.0.6, SHA-256
`0b5f284f943d7d19f7a00c317f396931b0e8e7e9d593922c342699f09ab9340b`.
Its shipped DTB and `aic8800_bsp.ko`, rather than the separately published
source tree, define the control behavior used here. Reverse engineering the
shipped module confirms this sequence: power on, wait 50 ms, request normal
MMC redetection, then wait up to 2 seconds for bootloader SDIO ID
`c8a1:0182`. Power-off waits 100 ms before redetection.

Vendor 5.15 control on this board (proper wall supply) confirmed the module:
after `sunxi_wlan_set_power(1)` + 50 ms + `sunxi_mmc_rescan`, the host got
`mmc2: new ultra high speed SDR104 SDIO card` / `aic8800d80` and created
`wlan0`. Early CMD52/CMD5 RTO before that power step is expected. Phone USB
power is not enough for RF bring-up.

Mainline now uses `mmc-pwrseq-simple` + `non-removable` on `mmc1` so the
first probe runs the same power→settle→CMD5 order. Soft rescan without
pulsing REG_ON: `echo 1 > /sys/devices/platform/soc/4021000.mmc/rescan`
(or `/root/wifi-up.sh`, which prefers that and only then unbind/bind).

## Current diagnostic baseline

Use a wall / PD supply (≥3 A). After boot, look for:

```text
... allocated mmc-pwrseq
... a733-sdio: ...
... mmc1: new high speed SDIO card
```

If CMD5 still times out (`int=00000104 status=000001e6`), run
`/root/wifi-up.sh` once and re-check. Do not load AIC modules until the SDIO
card enumerates. The helper also captures pinctrl debugfs state for PG0-PG5;
retain that output with the UART slice. The current capture proves PM1 and
both rails but does not prove the physical PG clock/CMD waveform.
