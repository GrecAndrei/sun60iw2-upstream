# Generator workflow

The generators produce kernel source from structured data. Their output is
tracked so a Linux tree can be built without running Python, but the data and
generator implementation remain authoritative.

| Generator | Input | Output |
|---|---|---|
| `generate_ccu.py` | `data/ccu-*.json` | `drivers/clk/sunxi-ng/ccu-sun60i-a733*.c` |
| `generate_pinctrl.py` | `data/pinctrl-main.json` | `drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c` |
| `generate_defconfig.py` | built-in board feature specification | `configs/sun60iw2*_defconfig` |
| `generate_thermal.py` | `data/thermal-main.json` plus pinned `data/upstream/sun8i_thermal.c` | `output/sun8i_thermal.c` |
| `generate_aic8800_upstream.py` | `data/aic8800-upstream.json` | AIC8800 skeleton in `drivers/` and review material in `generated/aic8800/` |

## Normal cycle

1. Change data or generator code.
2. Regenerate the affected output.
3. Run `python3 scripts/check-repository-layout.py` from the repository root.
4. Run `python3 scripts/validate-factory.py`.
5. Run `python3 scripts/refresh-documentation.py`.
6. Review source and generated output together.

The thermal template is pinned from the Linux v7.1.3 integration baseline
(`9568f851f`) so regeneration does not depend on mutable comparison worktrees.
The generator tolerates templates where A733 support is already upstream and
validates that it never duplicates definitions.

The factory validator checks JSON syntax, generator determinism, generated-file
freshness, binding coverage, and selected structural assumptions. A failed
freshness check means the output no longer represents its source and must not
be treated as current.

The extractor's semantic map is local project data, not an independent source
of hardware truth. Verify extracted facts against the relevant source and
mainline kernel interfaces before encoding them into generated output.
