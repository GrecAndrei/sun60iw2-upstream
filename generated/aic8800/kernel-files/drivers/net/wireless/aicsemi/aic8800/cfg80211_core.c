// SPDX-License-Identifier: GPL-2.0-only
// GENERATED FILE - DO NOT EDIT MANUALLY

#include <linux/ieee80211.h>
#include <net/cfg80211.h>
#include "cfg80211_core.h"
#include "fw_protocol.h"

#define AIC_CHAN2(_channel, _freq) { .band = NL80211_BAND_2GHZ, \
	.center_freq = (_freq), .hw_value = (_channel), .max_power = 20 }
#define AIC_CHAN5(_channel, _freq) { .band = NL80211_BAND_5GHZ, \
	.center_freq = (_freq), .hw_value = (_channel), .max_power = 20 }

static struct ieee80211_rate aic8800_rates[] = {
	{ .bitrate = 10, .hw_value = 0 }, { .bitrate = 20, .hw_value = 1 },
	{ .bitrate = 55, .hw_value = 2 }, { .bitrate = 110, .hw_value = 3 },
	{ .bitrate = 60, .hw_value = 4 }, { .bitrate = 90, .hw_value = 5 },
	{ .bitrate = 120, .hw_value = 6 }, { .bitrate = 180, .hw_value = 7 },
	{ .bitrate = 240, .hw_value = 8 }, { .bitrate = 360, .hw_value = 9 },
	{ .bitrate = 480, .hw_value = 10 }, { .bitrate = 540, .hw_value = 11 },
};

static struct ieee80211_channel aic8800_2ghz_channels[] = {
	AIC_CHAN2(1, 2412), AIC_CHAN2(2, 2417), AIC_CHAN2(3, 2422),
	AIC_CHAN2(4, 2427), AIC_CHAN2(5, 2432), AIC_CHAN2(6, 2437),
	AIC_CHAN2(7, 2442), AIC_CHAN2(8, 2447), AIC_CHAN2(9, 2452),
	AIC_CHAN2(10, 2457), AIC_CHAN2(11, 2462), AIC_CHAN2(12, 2467),
	AIC_CHAN2(13, 2472), AIC_CHAN2(14, 2484),
};

static struct ieee80211_channel aic8800_5ghz_channels[] = {
	AIC_CHAN5(36, 5180), AIC_CHAN5(40, 5200),
	AIC_CHAN5(44, 5220), AIC_CHAN5(48, 5240),
	AIC_CHAN5(52, 5260), AIC_CHAN5(56, 5280),
	AIC_CHAN5(60, 5300), AIC_CHAN5(64, 5320),
	AIC_CHAN5(100, 5500), AIC_CHAN5(104, 5520),
	AIC_CHAN5(108, 5540), AIC_CHAN5(112, 5560),
	AIC_CHAN5(116, 5580), AIC_CHAN5(120, 5600),
	AIC_CHAN5(124, 5620), AIC_CHAN5(128, 5640),
	AIC_CHAN5(132, 5660), AIC_CHAN5(136, 5680),
	AIC_CHAN5(140, 5700), AIC_CHAN5(144, 5720),
	AIC_CHAN5(149, 5745), AIC_CHAN5(153, 5765),
	AIC_CHAN5(157, 5785), AIC_CHAN5(161, 5805),
	AIC_CHAN5(165, 5825), AIC_CHAN5(169, 5845),
	AIC_CHAN5(173, 5865), AIC_CHAN5(177, 5885),
};

static struct ieee80211_supported_band aic8800_band_2ghz = {
	.channels = aic8800_2ghz_channels, .n_channels = ARRAY_SIZE(aic8800_2ghz_channels),
	.bitrates = aic8800_rates, .n_bitrates = ARRAY_SIZE(aic8800_rates),
};

static struct ieee80211_supported_band aic8800_band_5ghz = {
	.channels = aic8800_5ghz_channels, .n_channels = ARRAY_SIZE(aic8800_5ghz_channels),
	.bitrates = &aic8800_rates[4], .n_bitrates = ARRAY_SIZE(aic8800_rates) - 4,
};

static const u32 aic8800_ciphers[] = {
	WLAN_CIPHER_SUITE_WEP40, WLAN_CIPHER_SUITE_WEP104,
	WLAN_CIPHER_SUITE_TKIP, WLAN_CIPHER_SUITE_CCMP,
	WLAN_CIPHER_SUITE_AES_CMAC,
};

static struct aic8800_core *aic8800_wiphy_core(struct wiphy *wiphy)
{
	return *(struct aic8800_core **)wiphy_priv(wiphy);
}

static int aic8800_scan(struct wiphy *wiphy, struct cfg80211_scan_request *req)
{
	return aic8800_protocol_scan(aic8800_wiphy_core(wiphy), req);
}

static int aic8800_connect(struct wiphy *wiphy, struct net_device *dev,
			   struct cfg80211_connect_params *sme)
{
	return aic8800_protocol_connect(aic8800_wiphy_core(wiphy), sme);
}

static int aic8800_disconnect(struct wiphy *wiphy, struct net_device *dev,
			      u16 reason)
{
	return aic8800_protocol_disconnect(aic8800_wiphy_core(wiphy), reason);
}

static int aic8800_add_key(struct wiphy *wiphy, struct net_device *dev,
			   int link_id, u8 index, bool pairwise, const u8 *mac,
			   struct key_params *params)
{
	return aic8800_protocol_add_key(aic8800_wiphy_core(wiphy), index,
					pairwise, mac, params);
}

static int aic8800_del_key(struct wiphy *wiphy, struct net_device *dev,
			   int link_id, u8 index, bool pairwise, const u8 *mac)
{
	return aic8800_protocol_del_key(aic8800_wiphy_core(wiphy), index);
}

static int aic8800_change_vif(struct wiphy *wiphy, struct net_device *dev,
			      enum nl80211_iftype type, struct vif_params *params)
{
	return type == NL80211_IFTYPE_STATION ? 0 : -EOPNOTSUPP;
}

static const struct cfg80211_ops aic8800_cfg80211_ops = {
	.scan = aic8800_scan, .connect = aic8800_connect,
	.disconnect = aic8800_disconnect, .add_key = aic8800_add_key,
	.del_key = aic8800_del_key, .change_virtual_intf = aic8800_change_vif,
};

int aic8800_cfg80211_register(struct aic8800_core *core)
{
	struct wiphy *wiphy;
	int ret;

	wiphy = wiphy_new(&aic8800_cfg80211_ops, sizeof(struct aic8800_core *));
	if (!wiphy)
		return -ENOMEM;
	*(struct aic8800_core **)wiphy_priv(wiphy) = core;
	set_wiphy_dev(wiphy, core->dev);
	wiphy->max_scan_ssids = 3;
	wiphy->max_scan_ie_len = 256;
	wiphy->signal_type = CFG80211_SIGNAL_TYPE_MBM;
	wiphy->interface_modes = BIT(NL80211_IFTYPE_STATION);
	wiphy->bands[NL80211_BAND_2GHZ] = &aic8800_band_2ghz;
	wiphy->bands[NL80211_BAND_5GHZ] = &aic8800_band_5ghz;
	wiphy->cipher_suites = aic8800_ciphers;
	wiphy->n_cipher_suites = ARRAY_SIZE(aic8800_ciphers);
	strscpy(wiphy->fw_version, "aic8800d80-fullmac", sizeof(wiphy->fw_version));
	ret = wiphy_register(wiphy);
	if (ret)
		wiphy_free(wiphy);
	else
		core->wiphy = wiphy;
	return ret;
}

void aic8800_cfg80211_unregister(struct aic8800_core *core)
{
	if (!core || !core->wiphy)
		return;
	wiphy_unregister(core->wiphy);
	wiphy_free(core->wiphy);
	core->wiphy = NULL;
}
