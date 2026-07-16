// SPDX-License-Identifier: GPL-2.0
/*
 * Allwinner A733 SoC R-PIO pinctrl driver.
 *
 * The A733 R-PIO contains the L and M banks and automatically selects its
 * I/O supply from the hardware power-mode detector.  In particular, do not
 * program the generic PIO power-mode registers for these pins.
 */

#include <linux/module.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/pinctrl/pinctrl.h>
#include <linux/platform_device.h>

#include "pinctrl-sunxi.h"

static const u8 a733_r_nr_bank_pins[SUNXI_PINCTRL_MAX_BANKS] =
/*	  PL  PM */
	{ 14,  6 };

static const unsigned int a733_r_irq_bank_map[] = { 0, 1 };

static const u8 a733_r_irq_bank_muxes[SUNXI_PINCTRL_MAX_BANKS] =
/*	  PL  PM */
	{ 14, 14 };

static struct sunxi_pinctrl_desc a733_r_pinctrl_data = {
	.irq_banks = ARRAY_SIZE(a733_r_irq_bank_map),
	.irq_bank_map = a733_r_irq_bank_map,
	.irq_read_needs_mux = true,
	.pin_base = PL_BASE,
};

static int a733_r_pinctrl_probe(struct platform_device *pdev)
{
	return sunxi_pinctrl_dt_table_init(pdev, a733_r_nr_bank_pins,
					   a733_r_irq_bank_muxes,
					   &a733_r_pinctrl_data,
					   SUNXI_PINCTRL_NEW_REG_LAYOUT |
					   SUNXI_PINCTRL_AUTO_POWER_SWITCH);
}

static const struct of_device_id a733_r_pinctrl_match[] = {
	{ .compatible = "allwinner,sun60i-a733-r-pinctrl", },
	{}
};

static struct platform_driver a733_r_pinctrl_driver = {
	.probe	= a733_r_pinctrl_probe,
	.driver	= {
		.name		= "sun60i-a733-r-pinctrl",
		.of_match_table	= a733_r_pinctrl_match,
	},
};
builtin_platform_driver(a733_r_pinctrl_driver);
