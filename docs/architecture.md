# Architecture and ownership

## Source layers

`generators/data/` is the source of truth for generated artifacts. The CCU and
pinctrl generators produce the corresponding files under `drivers/`; the
AIC8800 generator produces both the tracked skeleton under `drivers/` and the
review material under `generated/aic8800/`.

Device Tree source, dt-bindings, defconfigs, and patches are hand-maintained.
When a DTS node references a generated provider, update the corresponding
binding/data/generator output together and run factory validation.

## Workspace boundaries

The source repository is separate from two local kernel trees:

- `../../kernels/mainline-v7/` is the mainline v7.0 integration tree.
  `scripts/apply-patches.sh` applies only Git-format patch files and installs
  the two defconfigs.
- `../../kernels/a733-debug/` is a detached local debug worktree with
  experimental changes absent from this repository. Do not treat it as
  reviewable source until the changes have been reproduced here and exported
  as patches.

`../../references/orangepi-vendor-linux-6.6/` and
`../../references/aic8800-bsp-snapshot/` are reference-only. Any new
implementation must use upstream Linux interfaces and coding patterns.

## Generated AIC8800 material

`generated/aic8800/` holds bindings, a DTS fragment, a kernel-file snapshot,
and the BSP-dependency inventory. The standalone boot patch series intentionally
does not install that experimental AIC8800 skeleton. See
[`aic8800.md`](aic8800.md).
