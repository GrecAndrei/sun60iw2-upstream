# Agent guide

## Scope

This repository is the reviewable source for the Allwinner A733 / Orange Pi 4
Pro upstream port. The workspace debug worktree is
`../../kernels/a733-debug/`; do not silently copy its changes into this
repository or describe them as integrated support.

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
