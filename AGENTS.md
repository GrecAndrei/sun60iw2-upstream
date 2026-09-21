# Agent guide

## Scope

This repository is the reviewable source for the Allwinner A733 / Orange Pi 4
Pro upstream port. The workspace debug worktree is
`../../kernels/a733-debug/`; do not silently copy its changes into this
repository or describe them as integrated support.

### Patch-series boundary

There is no active reproducible Linux patch series. The historical Linux v7.0
artifacts are isolated under `patches/archive/linux-v7.0/`; `0001-*` has
malformed hunk counts. Standalone drafts live under `patches/wip/` and are not
evidence of a complete sequence. `scripts/apply-patches.sh` intentionally
refuses the old implicit application behavior.

The currently integrated reference is `../../kernels/a733-v7.1.3/` on
`debug/a733-v7.1.3`, whose committed v7.1.3 baseline starts at `9568f851f`.
Use it for comparison and integration builds. Create a future active series
only after regenerating the *entire* sequence from a clean target release and
verifying apply, build, and hardware evidence. Keep that work separate from
the AIC8800 skeleton.

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
python3 scripts/check-repository-layout.py
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
