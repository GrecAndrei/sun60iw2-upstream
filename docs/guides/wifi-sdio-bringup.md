# A733 Wi-Fi SDIO bring-up

Orange Pi 4 Pro soldered AIC8800 on SMHC1 (`mmc1`). Integration tree:
`kernels/a733-v7.1.3`. Driver and board helpers are documented in
[`../aic8800.md`](../aic8800.md).

## Established wiring and software state

- SDIO uses `PG0`–`PG5` on SMHC1, mux value 2.
- BLDO5 (PG) and CLDO1 (PM) at 1.8 V, both `regulator-always-on`.
- `mmc1` has **no** `vmmc-supply` / `vqmmc-supply`. Mainline `sunxi-mmc`
  must still expose a default `ocr_avail` or voltage select fails after
  CMD5. Bring-up is high-speed only until UHS is re-enabled deliberately.
- `WL_REG_ON` is PM1 (active high → active-low reset in `mmc-pwrseq-simple`),
  with vendor 50 ms post-assert and 100 ms power-off delays.
- A733 SMHC v5p3 timing matches vendor 400 kHz defaults (CMD drive 180°,
  DAT 90°, NTSR sample 0, `CSDC=3`, HS400 cleared in `EDSD`).
- Main PIO: `SUNXI_PINCTRL_AUTO_POWER_SWITCH` + `SUNXI_PINCTRL_SUN60_LAYOUT`
  (TYPE_4). Do not use D1 `NEW_REG_LAYOUT` or A523 `ELEVEN_BANKS` on the
  main controller.
- `mmc0` and `mmc1` share STORE/MBUS/MSI_LITE gate clocks (vendor pattern);
  enabling Wi-Fi SDIO must not starve the SD root host.
- Systemd is PID 1 on the Arch rootfs. `aic8800-wifi.service` loads the
  modules and waits for `wlan0`. Optional `wpa_supplicant@wlan0` /
  `dhcpcd@wlan0` drop-ins order after that service. Ship
  `/lib/firmware/regulatory.db` or monitor channel sets fail with `-EINVAL`.

## Validated ladder (stop at the first failure)

1. **Rails / REG_ON** — BLDO5/CLDO1 at 1.8 V; PM1 high after pwrseq.
2. **SDIO enum** — `mmc1: new high speed SDIO card`; functions
   `c8a1:0182` (boot) and `c8a1:0082` (runtime).
3. **Firmware handoff** — dmesg: bootloader probe → firmware started →
   runtime normal mode probe (no `-110` / probe deadlock).
4. **netdev** — `wlan0` present after `aic8800-wifi.service`.
5. **Station** — `iw` / `wpa_supplicant` scan and associate.
6. **Monitor** — `wifi-monitor.sh 6` (or `iw dev wlan0 set type monitor`
   then set channel/freq). Confirm with `tcpdump -i wlan0 -c 20 -n -e`.
   There is **no** `iw … interface add mon0` support.
7. **Inject** — `wifi-inject-probe.py wlan0`; expect non-blocking sends and
   rising `tx_packets` / possible `tx_dropped` under queue pressure.

Soft rescan without pulsing REG_ON:
`echo 1 > /sys/devices/platform/soc/4021000.mmc/rescan`
(or `/root/wifi-up.sh`).

## Current diagnostic baseline

Use a wall / PD supply (≥3 A). After a normal systemd boot:

```text
aic8800_boot_sdio ... firmware started; runtime handoff ready
aic8800_runtime_sdio ... normal mode probe
aic8800-wifi: wlan0 UP
```

If CMD5 still times out (`int=00000104 status=000001e6`), check rails,
PM1, and TYPE_4 pinctrl before loading modules. Do not load AIC modules
until the SDIO card enumerates.

## Vendor control reference

Orange Pi release 1.0.6 Ubuntu,
SHA-256 `0b5f284f943d7d19f7a00c317f396931b0e8e7e9d593922c342699f09ab9340b`.
Shipped DTB + `aic8800_bsp.ko` define the power/rescan sequence (50 ms after
PM1, then MMC redetect, wait for `c8a1:0182`). Phone USB power is not enough
for RF bring-up.
