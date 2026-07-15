# sun60iw2-upstream

This is the source repository for an upstream-quality Linux port of the
Allwinner A733 SoC and Orange Pi 4 Pro board. It owns Device Tree sources,
generator inputs, generated driver sources, defconfigs, and a boot-baseline
patch series.

The live, evidence-based state is generated at
[`docs/status.md`](docs/status.md). Do not infer validation or hardware success
from historical notes, generated-artifact timestamps, or the presence of a
local debug tree.

## Repository layout

| Path | Ownership |
|---|---|
| `arch/`, `drivers/`, `include/` | Kernel changes and generated driver outputs. |
| `generators/data/` | Structured source data for generated CCU, pinctrl, and AIC8800 artifacts. |
| `generators/templates/aic8800/` | Maintainable source templates for the native AIC8800 driver. |
| `generators/` | Deterministic generator and extraction code. |
| `generated/aic8800/` | Generated AIC8800 bindings, DTS fragment, kernel snapshot, and debt inventory. |
| `patches/` | Standalone Git-format boot-baseline patches. |
| `configs/` | Defconfigs installed by `scripts/apply-patches.sh`. |
| `docs/` | Maintained process documentation; `status.md` is generated. |
| `.tmp/validation/` | Local, ignored validation evidence written by AIC8800 checks. |

## Start of work

```bash
python3 scripts/refresh-documentation.py
python3 scripts/refresh-documentation.py --check
python3 scripts/validate-factory.py
```

Read [`docs/README.md`](docs/README.md) for the documentation contract and
[`AGENTS.md`](AGENTS.md) before editing generated files.

## Core rules

- Edit generator data or templates, then regenerate; do not hand-edit generated
  C or AIC8800 outputs.
- Use the vendor kernel only as a reference for observable behavior and
  register maps. Do not import BSP implementation.
- Treat `../../kernels/a733-debug/` as a separate experimental worktree, not a
  patch source.
- Keep boot-baseline patches reproducible independently of AIC8800 driver work.
