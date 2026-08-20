# Architecture and ownership

## Source layers

`generators/data/` owns structured values for generated artifacts. The CCU and
main-PIO pinctrl generators produce the corresponding files under `drivers/`.
The small A733 R-PIO driver is hand-maintained because it uses the generic
DT-table path: only its verified L/M-bank geometry and automatic-voltage flag
are SoC-specific. The
AIC8800 generator renders its JSON-driven driver sources directly and uses the
two template-only firmware-protocol sources under `generators/templates/aic8800/`.
It produces the tracked driver under `drivers/` and the review snapshot under
`generated/aic8800/`.

Device Tree source, dt-bindings, defconfigs, and patches are hand-maintained.
When a DTS node references a generated provider, update the corresponding
binding/data/generator output together and run factory validation.

## Workspace boundaries

The source repository is separate from local kernel trees:

- `../../kernels/a733-v7.1.3/` is the primary integration build and flash
  target for Orange Pi 4 Pro bring-up (Wi-Fi, thermals, systemd rootfs).
- `../../kernels/mainline-v7/` is the mainline v7.0 comparison / export tree.
  `scripts/apply-patches.sh` applies only Git-format patch files and installs
  the two defconfigs.
- `../../kernels/a733-debug/` is a detached experimental worktree. Do not
  treat it as reviewable source until changes are reproduced here and
  exported as patches.

`../../references/orangepi-vendor-linux-6.6/` and
`../../references/aic8800-bsp-snapshot/` are reference-only. Any new
implementation must use upstream Linux interfaces and coding patterns.

## Generated AIC8800 material

`generated/aic8800/` holds bindings, a DTS fragment, a kernel-file snapshot,
and the BSP-dependency inventory. The standalone boot patch series intentionally
does not install the experimental AIC8800 driver. See
[`aic8800.md`](aic8800.md).
