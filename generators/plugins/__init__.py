"""Domain plugins for the CCU generator.

Each domain exports a `DOMAIN` dict that configures the generator for a
specific clock controller (main, R-domain, RTC, CPUPLL).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _binding(domain: str) -> Path:
    return (
        ROOT.parent
        / "include"
        / "dt-bindings"
        / "clock"
        / f"sun60i-a733-{domain}.h"
    )


MAIN = {
    "name": "main",
    "data_file": ROOT / "data" / "ccu-main.json",
    "extracted_file": ROOT / "data" / "ccu-main-extracted.json",
    "compat": "allwinner,sun60i-a733-ccu",
    "module_name": "sun60i-a733-ccu",
    "binding_header": "sun60i-a733-ccu.h",
    "binding_path": _binding("ccu"),
    "has_plls": True,
    "has_key_gates": True,
    "has_resets": True,
    "cross_domain_parents": False,
    "key_literals": {
        "AHB_MASTER_KEY_VALUE": "0x10000FF",
        "MBUS_MASTER_KEY_VALUE": "0x41055800",
        "MBUS_GATE_KEY_VALUE": "0x40302",
        "UPD_KEY_VALUE": "0x8000000",
    },
    "output_file": ROOT.parent / "drivers" / "clk" / "sunxi-ng" / "ccu-sun60i-a733.c",
}

R = {
    "name": "r",
    "data_file": ROOT / "data" / "ccu-r-extracted.json",
    "extracted_file": None,
    "compat": "allwinner,sun60i-a733-r-ccu",
    "module_name": "sun60i-a733-r-ccu",
    "binding_header": "sun60i-a733-r-ccu.h",
    "binding_path": _binding("r-ccu"),
    "has_plls": False,
    "has_key_gates": False,
    "has_resets": True,
    "cross_domain_parents": True,
    "key_literals": {},
    "output_file": ROOT.parent / "drivers" / "clk" / "sunxi-ng" / "ccu-sun60i-a733-r.c",
}

RTC = {
    "name": "rtc",
    "data_file": ROOT / "data" / "ccu-rtc-extracted.json",
    "extracted_file": None,
    "compat": "allwinner,sun60i-a733-rtc-ccu",
    "module_name": "sun60i-a733-rtc-ccu",
    "binding_header": "sun60i-a733-rtc.h",
    "binding_path": _binding("rtc"),
    "has_plls": False,
    "has_key_gates": True,
    "has_resets": False,
    "cross_domain_parents": True,
    "key_literals": {
        "KEY_FIELD_MAGIC_NUM_RTC": "0x16AA0000",
        "DCXO_WAKEUP_KEY_FIELD": "0x16AA",
    },
    "extra_includes": [
        "#include <linux/delay.h>",
    ],
    "extra_header_code": """
#define SUN60I_A733_RTC_KEY_FIELD_MAGIC_NUM	0x16AA0000
#define SUN60I_A733_RTC_LOSC_CTRL_REG		0x000
#define SUN60I_A733_RTC_LOSC_AUTO_SWT_STA_REG	0x004
#define SUN60I_A733_RTC_LOSC_OUT_GATING_REG	0x060
#define SUN60I_A733_RTC_XO_CTRL_REG		0x160

#define SUN60I_A733_RTC_LOSC_OSC32K_SEL		BIT(0)
#define SUN60I_A733_RTC_LOSC_EXT32K_ENABLE	BIT(4)
#define SUN60I_A733_RTC_LOSC_EXT32K_STABLE	BIT(4)
#define SUN60I_A733_RTC_LOSC_AUTO_SWITCH_ENABLE	BIT(14)
#define SUN60I_A733_RTC_LOSC_AUTO_SWITCH_MASK	(BIT(15) | BIT(14))
#define SUN60I_A733_RTC_LOSC_OUT_SRC_SEL_MASK	(0x3 << 1)
#define SUN60I_A733_RTC_DCXO_ENABLE		BIT(1)

static void sun60i_a733_rtc_ccu_update_bits(void __iomem *reg, u32 mask, u32 val)
{
	u32 regval = readl(reg);

	regval &= ~mask;
	regval |= val;
	writel(regval, reg);
}

static void sun60i_a733_rtc_ccu_update_key_bits(void __iomem *reg, u32 mask,
						 u32 val)
{
	u32 regval = readl(reg);

	regval &= ~mask;
	regval |= val;
	regval |= SUN60I_A733_RTC_KEY_FIELD_MAGIC_NUM;
	writel(regval, reg);
}

static bool sun60i_a733_rtc_ccu_ext32k_is_stable(void __iomem *reg)
{
	int tries;
	int stable_reads = 0;
	u32 val;

	for (tries = 0; tries < 100 && stable_reads < 4; tries++) {
		val = readl(reg);
		if (val & SUN60I_A733_RTC_LOSC_EXT32K_STABLE)
			stable_reads = 0;
		else
			stable_reads++;

		udelay(3);
	}

	return stable_reads == 4;
}

static void sun60i_a733_rtc_ccu_clock_source_init(struct device *dev,
						  void __iomem *reg)
{
	u32 val;

	sun60i_a733_rtc_ccu_update_bits(reg + SUN60I_A733_RTC_XO_CTRL_REG,
					 SUN60I_A733_RTC_DCXO_ENABLE,
					 SUN60I_A733_RTC_DCXO_ENABLE);

	sun60i_a733_rtc_ccu_update_key_bits(reg + SUN60I_A733_RTC_LOSC_CTRL_REG,
					     SUN60I_A733_RTC_LOSC_AUTO_SWITCH_MASK,
					     SUN60I_A733_RTC_LOSC_AUTO_SWITCH_ENABLE);

	val = readl(reg + SUN60I_A733_RTC_LOSC_CTRL_REG);
	if (!(val & SUN60I_A733_RTC_LOSC_EXT32K_ENABLE)) {
		sun60i_a733_rtc_ccu_update_key_bits(reg + SUN60I_A733_RTC_LOSC_CTRL_REG,
						     SUN60I_A733_RTC_LOSC_EXT32K_ENABLE,
						     SUN60I_A733_RTC_LOSC_EXT32K_ENABLE);

		if (!sun60i_a733_rtc_ccu_ext32k_is_stable(
			    reg + SUN60I_A733_RTC_LOSC_AUTO_SWT_STA_REG))
			dev_warn(dev,
				 "ext-32k not stable, osc32k will fall back to iosc-div32k\\n");
	}

	sun60i_a733_rtc_ccu_update_key_bits(reg + SUN60I_A733_RTC_LOSC_CTRL_REG,
					     SUN60I_A733_RTC_LOSC_OSC32K_SEL,
					     SUN60I_A733_RTC_LOSC_OSC32K_SEL);

	sun60i_a733_rtc_ccu_update_bits(reg + SUN60I_A733_RTC_LOSC_OUT_GATING_REG,
					 SUN60I_A733_RTC_LOSC_OUT_SRC_SEL_MASK, 0);
}
""",
    "probe_preamble": "	sun60i_a733_rtc_ccu_clock_source_init(&pdev->dev, reg);",
    "probe_reg_setup": """	struct resource *res;

	res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
	if (!res)
		return -EINVAL;

	reg = devm_ioremap(&pdev->dev, res->start, resource_size(res));
	if (IS_ERR(reg))
		return PTR_ERR(reg);

""",
    "registration": "core_initcall_if_builtin",
    "output_file": ROOT.parent
    / "drivers"
    / "clk"
    / "sunxi-ng"
    / "ccu-sun60i-a733-rtc.c",
}

CPUPLL = {
    "name": "cpupll",
    "data_file": ROOT / "data" / "ccu-cpupll-extracted.json",
    "extracted_file": None,
    "compat": "allwinner,sun60i-a733-cpupll-ccu",
    "module_name": "sun60i-a733-cpupll-ccu",
    "binding_header": "sun60i-a733-cpupll-ccu.h",
    "binding_path": _binding("cpupll-ccu"),
    "has_plls": True,
    "has_key_gates": False,
    "has_resets": False,
    "cross_domain_parents": True,
    "key_literals": {},
    "output_file": ROOT.parent
    / "drivers"
    / "clk"
    / "sunxi-ng"
    / "ccu-sun60i-a733-cpupll.c",
}

DOMAINS = {
    "main": MAIN,
    "r": R,
    "rtc": RTC,
    "cpupll": CPUPLL,
}
