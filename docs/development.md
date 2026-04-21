# Development Guidelines

## Code Style

All code MUST follow the [Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html).

### Key Rules

- **Indentation:** Tabs (width 8), not spaces
- **Line length:** 80 columns soft limit, 100 columns hard limit
- **Braces:** K&R style, opening brace on same line
- **Naming:** `snake_case` for variables/functions, `UPPER_CASE` for macros
- **Comments:** Use `/* */` for block comments, `//` only for temporary/debug

### Example

```c
static int sun60iw2_ccu_probe(struct platform_device *pdev)
{
	struct clk_hw_onecell_data *hw_data;
	struct device_node *np = pdev->dev.of_node;
	void __iomem *reg;
	int ret;

	reg = devm_platform_ioremap_resource(pdev, 0);
	if (IS_ERR(reg))
		return PTR_ERR(reg);

	hw_data = devm_kzalloc(&pdev->dev,
			       struct_size(hw_data, hws, CLK_MAX),
			       GFP_KERNEL);
	if (!hw_data)
		return -ENOMEM;

	/* Initialize all clocks */
	ret = sun60iw2_ccu_init_clocks(reg, hw_data);
	if (ret)
		return ret;

	ret = devm_of_clk_add_hw_provider(&pdev->dev, of_clk_hw_onecell_get,
					  hw_data);
	if (ret)
		return ret;

	return 0;
}
```

---

## Device Tree Guidelines

### Bindings

- Use standard bindings from `Documentation/devicetree/bindings/`
- If a binding doesn't exist, write one in `Documentation/devicetree/bindings/`
- All new compatibles must be documented

### Structure

```dts
/ {
	model = "Orange Pi 4 Pro";
	compatible = "xunlong,orangepi-4-pro", "allwinner,sun60i-a733";

	aliases {
		serial0 = &uart0;
	};

	chosen {
		stdout-path = "serial0:115200n8";
	};
};

&uart0 {
	status = "okay";
};
```

### Required Properties

- `compatible` strings must be ordered: most specific first, least specific last
- `reg` properties must match the hardware exactly
- `clocks` and `resets` must reference the CCU
- `pinctrl` must reference valid pin groups

---

## Upstream Workflow

### Patch Series Format

Each patch series must:

1. Start with a cover letter explaining the series
2. Each patch must have a proper commit message
3. Follow `git format-patch` output
4. Include `Signed-off-by:` tag (DCO)

### Commit Message Format

```
subsystem: Short description (50 chars)

Longer explanation of what and why. Wrap at 72 chars.

Include hardware details, register references, and testing notes.

Signed-off-by: Your Name <your@email.com>
```

Example:
```
arm64: dts: allwinner: Add base A733 Device Tree

Add the base sun60i-a733.dtsi with CPU, memory, and basic
peripheral nodes for the Allwinner A733 SoC.

Based on the vendor device tree and verified against the
sun55i-a523 mainline device tree.

Signed-off-by: Your Name <your@email.com>
```

### Submitting Patches

1. **Test** on real hardware
2. **Run checkpatch.pl:** `./scripts/checkpatch.pl --strict 0001-*.patch`
3. **Send to linux-sunxi:** `git send-email --to linux-sunxi@lists.linux.dev *.patch`
4. **Wait for review** (usually 1-4 weeks)
5. **Address feedback** and send v2, v3, etc.

---

## File Organization

### Driver Files

```
drivers/clk/sunxi-ng/
  ccu-sun60i-a733.c       # Main CCU
  ccu-sun60i-a733.h       # Private headers
  ccu-sun60i-a733-r.c     # R-CCU
  ccu-sun60i-a733-r.h
  ccu-sun60i-a733-rtc.c   # RTC CCU
  ccu-sun60i-a733-rtc.h

drivers/pinctrl/sunxi/
  pinctrl-sun60i-a733.c   # Main pinctrl
  pinctrl-sun60i-a733-r.c # R-pinctrl

drivers/thermal/
  sun8i_thermal.c         # Add sun60iw2 support
```

### Device Tree Files

```
arch/arm64/boot/dts/allwinner/
  sun60i-a733.dtsi                    # Base SoC DTSI
  sun60i-a733-orangepi-4-pro.dts      # Orange Pi 4 Pro board
  sun60i-a733-orangepi-zero3w.dts     # Orange Pi Zero 3W board (if we get one)
```

### Header Files

```
include/dt-bindings/clock/
  sun60i-a733-ccu.h
  sun60i-a733-r-ccu.h
  sun60i-a733-rtc.h
  sun60i-a733-cpupll-ccu.h

include/dt-bindings/reset/
  sun60i-a733-ccu.h
  sun60i-a733-r-ccu.h

include/dt-bindings/power/
  sun60i-a733-power.h
```

---

## Testing Requirements

Before submitting any patch:

- [ ] Code compiles with `make ARCH=arm64`
- [ ] No warnings with `W=1`
- [ ] checkpatch.pl passes with `--strict`
- [ ] Tested on real Orange Pi 4 Pro hardware
- [ ] UART output visible
- [ ] If replacing vendor code, feature parity documented

---

## Git Workflow

### Branches

- `main` - mirrors upstream Linux, apply patches here
- `wip/pinctrl` - work in progress branches
- `wip/clk`
- `wip/thermal`
- etc.

### Commits

- One logical change per commit
- No "fixup" commits in PRs
- Rebase before submitting

### Example workflow

```bash
# Start new feature
git checkout -b wip/ccu-main

# Work...
$EDITOR drivers/clk/sunxi-ng/ccu-sun60i-a733.c

# Commit with proper message
git add drivers/clk/sunxi-ng/ccu-sun60i-a733.c
git commit -m "clk: sunxi-ng: Add Allwinner A733 main CCU support

Add the main Clock Controller Unit driver for the Allwinner A733
(sun60iw2) SoC.

The A733 has four CCUs: main, R-domain, RTC, and CPUPLL. This
patch adds the main CCU with 333 clocks including PLLs, muxes,
dividers, and gates.

Signed-off-by: Your Name <your@email.com>"

# Export patches for review
git format-patch main
```

---

## Communication

- **GitHub Issues:** Task tracking, hardware questions, bug reports
- **GitHub Discussions:** General chat, design decisions
- **linux-sunxi mailing list:** Patch submission, upstream coordination
- **IRC/Matrix:** #linux-sunxi on OFTC / Matrix

---

## License

All contributions must be licensed under GPL-2.0+.

By contributing, you agree to the [Developer Certificate of Origin](https://developercertificate.org/):

```
Signed-off-by: Your Name <your@email.com>
```
