# [RFC PATCH 1/6] dt-bindings: net: wireless: add AIC8800 SDIO WiFi and UART BT bindings

## Scope

- Add WiFi binding seed: `docs/upstream-drafts/aicsemi,aic8800.yaml`
- Add BT binding seed: `docs/upstream-drafts/aicsemi,aic8800-bt.yaml`
- Document Orange Pi 4 Pro node usage for `mmc1` (WiFi) and `uart1` (BT)

## Binding Direction

- WiFi compatible set:
  - `aicsemi,aic8800d80`
  - `aicsemi,aic8800`
- BT compatible set:
  - `aicsemi,aic8800d80-bt`
  - `aicsemi,aic8800-bt`
- Keep firmware path assumption under `/lib/firmware/aic8800d80/`

## Follow-up for submission

- Move draft YAML files from docs staging into upstream dt-bindings path
- Run `make dt_binding_check` and fix schema nits
