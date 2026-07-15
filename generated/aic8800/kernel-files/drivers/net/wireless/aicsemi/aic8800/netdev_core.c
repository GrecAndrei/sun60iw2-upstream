// SPDX-License-Identifier: GPL-2.0-only
// GENERATED FILE - DO NOT EDIT MANUALLY

#include <linux/etherdevice.h>
#include <linux/netdevice.h>
#include <net/cfg80211.h>
#include "fw_protocol.h"
#include "netdev_core.h"

struct aic8800_vif {
	struct wireless_dev wdev;
	struct aic8800_core *core;
};

static int aic8800_ndo_open(struct net_device *ndev)
{
	struct aic8800_vif *vif = netdev_priv(ndev);
	int ret;

	ret = aic8800_protocol_open(vif->core, ndev->dev_addr);
	if (ret)
		return ret;
	netif_carrier_off(ndev);
	netif_start_queue(ndev);
	return 0;
}

static int aic8800_ndo_stop(struct net_device *ndev)
{
	struct aic8800_vif *vif = netdev_priv(ndev);

	netif_stop_queue(ndev);
	netif_carrier_off(ndev);
	return aic8800_protocol_close(vif->core);
}

static netdev_tx_t aic8800_ndo_start_xmit(struct sk_buff *skb,
					  struct net_device *ndev)
{
	struct aic8800_vif *vif = netdev_priv(ndev);
	int ret;

	if (!vif->core->link_up || !vif->core->tx_frame) {
		ndev->stats.tx_dropped++;
		dev_kfree_skb_any(skb);
		return NETDEV_TX_OK;
	}
	ret = vif->core->tx_frame(vif->core, skb->data, skb->len);
	if (ret == -ENOSPC)
		return NETDEV_TX_BUSY;
	if (ret) {
		ndev->stats.tx_dropped++;
	} else {
		ndev->stats.tx_packets++;
		ndev->stats.tx_bytes += skb->len;
	}
	dev_kfree_skb_any(skb);
	return NETDEV_TX_OK;
}

static const struct net_device_ops aic8800_netdev_ops = {
	.ndo_open = aic8800_ndo_open,
	.ndo_stop = aic8800_ndo_stop,
	.ndo_start_xmit = aic8800_ndo_start_xmit,
	.ndo_set_mac_address = eth_mac_addr,
	.ndo_validate_addr = eth_validate_addr,
};

int aic8800_netdev_register(struct aic8800_core *core)
{
	struct net_device *ndev;
	struct aic8800_vif *vif;
	u8 mac[ETH_ALEN];
	int ret;

	ndev = alloc_etherdev(sizeof(*vif));
	if (!ndev)
		return -ENOMEM;
	vif = netdev_priv(ndev);
	vif->core = core;
	vif->wdev.wiphy = core->wiphy;
	vif->wdev.netdev = ndev;
	vif->wdev.iftype = NL80211_IFTYPE_STATION;
	ndev->ieee80211_ptr = &vif->wdev;
	ndev->netdev_ops = &aic8800_netdev_ops;
	SET_NETDEV_DEV(ndev, core->dev);
	strscpy(ndev->name, "wlan%d", IFNAMSIZ);
	ret = eth_platform_get_mac_address(core->dev, mac);
	if (!ret && is_valid_ether_addr(mac))
		eth_hw_addr_set(ndev, mac);
	else
		eth_hw_addr_random(ndev);
	ret = cfg80211_register_netdevice(ndev);
	if (ret) {
		free_netdev(ndev);
		return ret;
	}
	core->ndev = ndev;
	return 0;
}

void aic8800_netdev_unregister(struct aic8800_core *core)
{
	if (!core || !core->ndev)
		return;
	cfg80211_unregister_netdevice(core->ndev);
	core->ndev = NULL;
}
