// SPDX-License-Identifier: GPL-2.0-only
// GENERATED FILE - DO NOT EDIT MANUALLY

#include <linux/etherdevice.h>
#include <linux/module.h>
#include "core_types.h"
#include "cfg80211_core.h"
#include "netdev_core.h"

int aic8800_core_register(struct aic8800_core *core)
{
	int ret;

	if (!core || !core->dev || !core->protocol)
		return -EINVAL;
	core->link_up = false;
	eth_zero_addr(core->bssid);
	ret = aic8800_cfg80211_register(core);
	if (ret)
		return ret;
	ret = aic8800_netdev_register(core);
	if (ret)
		aic8800_cfg80211_unregister(core);
	return ret;
}
EXPORT_SYMBOL_GPL(aic8800_core_register);

void aic8800_core_unregister(struct aic8800_core *core)
{
	if (!core)
		return;
	aic8800_netdev_unregister(core);
	aic8800_cfg80211_unregister(core);
}
EXPORT_SYMBOL_GPL(aic8800_core_unregister);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("AIC8800D80 fullmac core");
