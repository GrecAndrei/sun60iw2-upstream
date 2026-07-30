/* SPDX-License-Identifier: GPL-2.0-only */
/* GENERATED FILE - DO NOT EDIT MANUALLY */
/* Generated from: generators/templates/aic8800/ */

#ifndef AIC8800_FW_PROTOCOL_H
#define AIC8800_FW_PROTOCOL_H

#include <linux/types.h>
#include <net/cfg80211.h>

struct aic8800_core;
struct cfg80211_chan_def;
struct cfg80211_connect_params;
struct key_params;
struct cfg80211_scan_request;

int aic8800_protocol_init(struct aic8800_core *core);
void aic8800_protocol_deinit(struct aic8800_core *core);
int aic8800_protocol_boot(struct aic8800_core *core);
int aic8800_protocol_runtime_config(struct aic8800_core *core);
int aic8800_protocol_open(struct aic8800_core *core, const u8 *mac);
int aic8800_protocol_close(struct aic8800_core *core);
int aic8800_protocol_change_vif_type(struct aic8800_core *core,
				     enum nl80211_iftype iftype);
int aic8800_protocol_set_monitor_channel(struct aic8800_core *core,
					 struct cfg80211_chan_def *chandef);
int aic8800_protocol_scan(struct aic8800_core *core,
			  struct cfg80211_scan_request *request);
int aic8800_protocol_connect(struct aic8800_core *core,
			     struct cfg80211_connect_params *sme);
int aic8800_protocol_disconnect(struct aic8800_core *core, u16 reason);
int aic8800_protocol_add_key(struct aic8800_core *core, u8 key_index,
			     bool pairwise, const u8 *mac_addr,
			     struct key_params *params);
int aic8800_protocol_del_key(struct aic8800_core *core, u8 key_index);
int aic8800_protocol_rx(struct aic8800_core *core, const u8 *buf, size_t len);
int aic8800_protocol_wrap_tx(struct aic8800_core *core, const u8 *frame,
			     size_t frame_len, u8 **out, size_t *out_len);
int aic8800_protocol_mgmt_tx(struct aic8800_core *core, const u8 *frame,
			     size_t frame_len, bool no_cck, bool robust);
int aic8800_protocol_mpdu_tx(struct aic8800_core *core, const u8 *mpdu,
			     size_t mpdu_len, bool no_cck);

#endif
