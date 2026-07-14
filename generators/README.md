# Generator workflow

The generators produce kernel source from structured data. Their output is
tracked so a Linux tree can be built without running Python, but the data and
generator implementation remain authoritative.

| Generator | Input | Output |
|---|---|---|
| `generate_ccu.py` | `data/ccu-*.json` | `drivers/clk/sunxi-ng/ccu-sun60i-a733*.c` |
| `generate_pinctrl.py` | `data/pinctrl-main.json` | `drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c` |
| `generate_aic8800_upstream.py` | `data/aic8800-upstream.json` | AIC8800 skeleton in `drivers/` and review material in `generated/aic8800/` |

## Normal cycle

1. Change data or generator code.
2. Regenerate the affected output.
3. Run `python3 scripts/validate-factory.py` from the repository root.
4. Run `python3 scripts/refresh-documentation.py`.
5. Review source and generated output together.

The factory validator checks JSON syntax, generator determinism, generated-file
freshness, binding coverage, and selected structural assumptions. A failed
freshness check means the output no longer represents its source and must not
be treated as current.

The extractor's semantic map is local project data, not an independent source
of hardware truth. Verify extracted facts against the relevant source and
mainline kernel interfaces before encoding them into generated output.
