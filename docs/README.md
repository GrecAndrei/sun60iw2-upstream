# Documentation contract

The documentation is intentionally split between durable process guidance and
live, generated evidence.

| Document | Purpose | Update mechanism |
|---|---|---|
| [`status.md`](status.md) | Git state, build-artifact metadata, DTS declarations, and factory-validation result. | `python3 scripts/refresh-documentation.py` |
| [`architecture.md`](architecture.md) | Source ownership and generation boundaries. | Update when structure changes. |
| [`hardware.md`](hardware.md) | Current DTS declarations and the distinction between source and debug trees. | Update with DTS ownership changes. |
| [`development.md`](development.md) | Editing, generation, and validation rules. | Update with workflow changes. |
| [`aic8800.md`](aic8800.md) | AIC8800 source, generated outputs, and test boundaries. | Update with generator or export workflow changes. |
| [`guides/`](guides) | Build, test, and patch workflow. | Update with script behavior. |
| [`guides/bootloader.md`](guides/bootloader.md) | Legacy U-Boot packaging, guarded flash, and UART acceptance procedure. | Update with bootloader script or layout changes. |
| [`guides/wifi-sdio-bringup.md`](guides/wifi-sdio-bringup.md) | Evidence-led A733 SDIO Wi-Fi validation procedure. | Update with each validated state transition. |

Refresh the live report after source, generator, DTS, or integration changes:

```bash
python3 scripts/refresh-documentation.py
python3 scripts/refresh-documentation.py --check
```

`docs/archive/` and the workspace-level `archive/` retain old material for
comparison. They are explicitly non-authoritative and must not be cited as
current status or operating instructions.

The workspace layout is documented at
[`../../README.md`](../../README.md): source and wiki live in `projects/`,
kernel worktrees in `kernels/`, and comparison inputs in `references/`.
