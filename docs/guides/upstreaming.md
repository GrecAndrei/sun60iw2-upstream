# Upstreaming Guide

## Overview

This document explains how to get sun60iw2/A733 code merged into the official Linux kernel (torvalds/linux.git).

---

## The Upstream Process

```
Your Code
    |
    v
linux-sunxi mailing list review
    |
    v
Acked-by / Reviewed-by from maintainers
    |
    v
Merged into sunxi.git (maintainer tree)
    |
    v
Pull request to torvalds/linux.git
    |
    v
In mainline Linux!
```

---

## Mailing List

- **List:** `linux-sunxi@lists.linux.dev`
- **Subscribe:** https://subspace.kernel.org/lists.html#linux-sunxi
- **Archives:** https://lore.kernel.org/linux-sunxi/

---

## Patch Series Structure

A typical upstream series looks like:

```
[PATCH 0/7] Add initial Allwinner A733 SoC support
  [PATCH 1/7] dt-bindings: clock: Add Allwinner A733 CCU bindings
  [PATCH 2/7] dt-bindings: pinctrl: Add Allwinner A733 pinctrl bindings
  [PATCH 3/7] dt-bindings: reset: Add Allwinner A733 reset bindings
  [PATCH 4/7] clk: sunxi-ng: Add Allwinner A733 CCU driver
  [PATCH 5/7] pinctrl: sunxi: Add Allwinner A733 pinctrl driver
  [PATCH 6/7] arm64: dts: allwinner: Add base A733 Device Tree
  [PATCH 7/7] arm64: dts: allwinner: Add Orange Pi 4 Pro board support
```

### Rules

- **Order:** Dependencies first (bindings → drivers → DT)
- **Size:** Each patch should be <100KB, ideally <50KB
- **Logic:** One logical change per patch
- **Bisectable:** Every patch should compile and not break bisect

---

## Cover Letter

The `[PATCH 0/N]` email should explain:

1. What SoC/board is being added
2. What works and what doesn't
3. Dependencies on other series
4. Testing done

Example:

```
Subject: [PATCH 0/7] Add initial Allwinner A733 SoC support

Hi all,

This series adds initial support for the Allwinner A733 (sun60iw2p1)
SoC and the Orange Pi 4 Pro board.

The A733 is a new high-performance SoC with:
- 6x Cortex-A55 + 2x Cortex-A76
- Imagination BXM-4-64 GPU
- 3 TOPS NPU
- Dual PMIC (AXP515 + AXP8191)

This series includes:
- Clock controller (main + R-domain)
- Pinctrl (main + R-domain)
- Base device tree
- Orange Pi 4 Pro board device tree

What's NOT included (future work):
- Display/DRM (DE v352)
- GPU/NPU drivers
- PCIe controller
- VIN/ISP/Camera

Tested on Orange Pi 4 Pro (8GB).

Depends on: [PATCH v2] clk: sunxi-ng: sun55i-a523 fixes

Regards,
Alexander Grec
```

---

## Submitting Patches

### Using git send-email

```bash
# Configure git send-email
git config sendemail.smtpServer smtp.gmail.com
git config sendemail.smtpServerPort 587
git config sendemail.smtpEncryption tls
git config sendemail.smtpUser your.email@gmail.com

# Generate patches
git format-patch --cover-letter -o patches/ main..wip/ccu

# Edit cover letter
$EDITOR patches/0000-cover-letter.patch

# Send
git send-email --to linux-sunxi@lists.linux.dev --cc robh+dt@kernel.org --cc krzysztof.kozlowski+dt@linaro.org patches/
```

### Maintainers to CC

For sunxi patches:

- **DT bindings:** Rob Herring <robh+dt@kernel.org>, Krzysztof Kozlowski <krzysztof.kozlowski+dt@linaro.org>
- **Clocks:** Michael Turquette <mturquette@baylibre.com>, Stephen Boyd <sboyd@kernel.org>
- **Pinctrl:** Linus Walleij <linus.walleij@linaro.org>
- **ARM SoC:** Andre Przywara <andre.przywara@arm.com>, Jernej Skrabec <jernej.skrabec@gmail.com>
- **Thermal:** Zhang Rui <rui.zhang@intel.com>
- **MMC:** Ulf Hansson <ulf.hansson@linaro.org>
- **Net:** Heiner Kallweit <hkallweit1@gmail.com>, Andrew Lunn <andrew@lunn.ch>

---

## Review Cycle

### What to Expect

- First response: 1-7 days
- Full review: 1-4 weeks
- Multiple revisions (v2, v3, ...) are normal

### Handling Feedback

1. **Read carefully** - understand what the reviewer wants
2. **Don't argue** - ask for clarification if needed
3. **Make changes** - update your code
4. **Send v2** with changelog:

```
Subject: [PATCH v2 0/7] Add initial Allwinner A733 SoC support

Changes since v1:
- Fixed PLL_DDR parent in ccu-sun60i-a733.c (Andre)
- Added missing reset line for MMC2 (Jernej)
- Fixed typo in pinctrl function name (Linus)
- Rebased on v7.1-rc1
```

### Common Review Comments

| Comment | Meaning | Fix |
|---------|---------|-----|
| "Use tabs not spaces" | Indentation | Fix with `scripts/Lindent` |
| "Line over 80 chars" | Too long | Break the line |
| "Missing binding doc" | No DT binding | Add `Documentation/devicetree/bindings/...` |
| "Sort alphabetically" | Ordering | Sort clocks, resets, compatibles |
| "Use existing macro" | Reinventing wheel | Use `GENMASK`, `FIELD_PREP`, etc. |
| "This should be a separate patch" | Too much in one | Split it |

---

## Getting Maintained

Once merged into sunxi.git, the ARM SoC maintainers will create a pull request to Linus. This happens during the merge window (~2 weeks after rc1).

### Merge Windows

- **v7.x merge window:** ~2 weeks after v7.(x-1) release
- **Example:** v7.1 merge window opens after v7.0 release

### Tracking

Follow your patches on:
- https://lore.kernel.org/linux-sunxi/
- https://git.kernel.org/pub/scm/linux/kernel/git/sunxi/linux.git/log/

---

## Code of Conduct

- Be patient - reviewers are volunteers
- Be respectful - no entitlement
- Be thorough - test before submitting
- Be persistent - v3, v4, v5 are normal

---

## Resources

- [Linux Kernel Patch Submission](https://www.kernel.org/doc/html/latest/process/submitting-patches.html)
- [Linux Kernel Coding Style](https://www.kernel.org/doc/html/latest/process/coding-style.html)
- [Device Tree Bindings](https://www.kernel.org/doc/html/latest/devicetree/bindings/)
- [linux-sunxi wiki](https://linux-sunxi.org/Linux_mainlining)
