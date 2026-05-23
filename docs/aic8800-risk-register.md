# AIC8800 Upstream Risk Register

## Planned AIC8800 Series (1/6..6/6)

| Patch | Risk / Description | Probability | Impact | Mitigation | Earliest Detection Check |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **1/6** dt-bindings | Binding schema mismatch or missing required properties. | Low | Medium | Validate YAML against dt-schema and align node properties with wiring. | `make dt_binding_check` clean for both AIC binding files. |
| **2/6** WiFi core | BSP-only symbols leak into core and block build/link. | High | High | Replace BSP hooks with stubs backed by mainline APIs, keep transport split clean. | Core builds with cfg80211/mac80211 enabled. |
| **3/6** SDIO transport | Incorrect IRQ/power sequencing prevents bind/enumeration. | Medium-High | High | Use DT IRQ parsing + `mmc-pwrseq-simple` path + explicit SDIO IDs. | `mmc1` enumerates and driver probe runs in `dmesg`. |
| **4/6** BT UART transport | serdev flow-control or init sequence mismatch breaks `hci0`. | Medium | High | Follow `hci_bcm`/`btmtkuart` style serdev lifecycle and test RTS/CTS. | `hci0` appears and responds via `hciconfig`/`bluetoothctl`. |
| **5/6** Board DTS wiring | Pinmux/GPIO/regulator mismatch leaves chip unpowered. | Medium | High | Cross-check GPIO/pinctrl values against board wiring and boot logs. | DT builds clean and enable line toggles at boot. |
| **6/6** Docs + tests | Firmware naming/path drift causes runtime load failure. | Low-Medium | Medium | Keep exact blob names and include runtime checks in testing docs/scripts. | `request_firmware` resolves expected files under `/lib/firmware/aic8800d80/`. |
