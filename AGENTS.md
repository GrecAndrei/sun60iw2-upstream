# Agent guide

## Scope

This repository is the reviewable source for the Allwinner A733 / Orange Pi 4
Pro upstream port. The workspace debug worktree is
`../../kernels/a733-debug/`; do not silently copy its changes into this
repository or describe them as integrated support.

### Legacy patch-series boundary

`patches/0001-*` through `patches/0006-*` are historical Linux v7.0-era
artifacts, not the current boot baseline. They have not been rebased to Linux
v7.1.3: `0001` has malformed hunk counts and does not apply to a clean v7.1.3
tree. `0007-*` is in-progress work, not evidence that the sequence is fixed.

The currently integrated reference is `../../kernels/a733-v7.1.3/` on
`debug/a733-v7.1.3`, whose committed v7.1.3 baseline starts at `9568f851f`.
Use it for comparison and integration builds. Do not use
`scripts/apply-patches.sh` to create a bootable baseline until the *entire*
series has been regenerated from a clean v7.1.3 tree and verified by applying
and building it there. Keep that rebase separate from the AIC8800 skeleton.

## Generated-source rule

Never hand-edit a file marked `GENERATED FILE`.

- CCU and pinctrl: edit `generators/data/`, regenerate, then validate.
- AIC8800: edit `generators/data/aic8800-upstream.json`, run
  `scripts/generate-aic8800-upstream.sh`, and review both `drivers/` and
  `generated/aic8800/` outputs.

Commit source data and generated output together.

## Vendor and upstream rules

- The vendor tree is reference-only. Do not copy BSP code, BSP-only APIs, or
  vendor logging/framework layers.
- Follow existing mainline sunxi patterns and Linux coding conventions.
- Keep the AIC8800 draft skeleton separate from the standalone boot-baseline
  patch series until it is independently reviewable.

## Required verification

After generator, DTS, binding, or patch-series changes run:

```bash
python3 scripts/validate-factory.py
python3 scripts/refresh-documentation.py
python3 scripts/refresh-documentation.py --check
```

Factory failures are real state; do not retain or add documentation that says
validation passed while they exist. Hardware-success claims require an exact
Image/DTB and captured console evidence.

## Documentation

`docs/status.md` is generated from live workspace state. Keep permanent docs
limited to ownership and procedure, refresh the generated report after relevant
changes, and move superseded material to `docs/archive/` rather than leaving it
in active guidance.

## Git

Work on a feature branch and do not push directly to `main`. Preserve existing
worktree changes unless the user explicitly asks to replace them.
