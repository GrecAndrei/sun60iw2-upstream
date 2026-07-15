/* SPDX-License-Identifier: GPL-2.0-only */
/* GENERATED FILE - DO NOT EDIT MANUALLY */
/* Generated from: generators/templates/aic8800/ */

#ifndef AIC8800_CORE_TYPES_H
#define AIC8800_CORE_TYPES_H

#include <linux/device.h>
#include <linux/firmware.h>
#include <linux/if_ether.h>
#include <linux/types.h>

struct wiphy;
struct net_device;
struct sk_buff;
struct aic8800_core;
struct aic8800_protocol;

struct aic8800_fw_hooks {
	int (*pre_load)(struct aic8800_core *core, const char *name);
	void (*post_load)(struct aic8800_core *core, const char *name, int ret);
	int (*pre_unload)(struct aic8800_core *core);
	void (*post_unload)(struct aic8800_core *core, int ret);
	int (*pre_start)(struct aic8800_core *core, const char *name);
	void (*post_start)(struct aic8800_core *core, const char *name, int ret);
};

typedef int (*aic8800_tx_frame_t)(struct aic8800_core *core,
				  const u8 *data, size_t len);
typedef int (*aic8800_tx_command_t)(struct aic8800_core *core,
				    const u8 *data, size_t len);

struct aic8800_core {
	struct device *dev;
	const char *fw_name;
	const struct firmware *fw_data;
	struct wiphy *wiphy;
	struct net_device *ndev;
	void *bus_priv;
	struct aic8800_protocol *protocol;
	const struct aic8800_fw_hooks *fw_hooks;
	char fw_override[128];
	char fw_loaded[128];
	aic8800_tx_frame_t tx_frame;
	aic8800_tx_command_t tx_command;
	u64 irq_count;
	u64 rx_batches;
	u64 rx_frames;
	u64 rx_empty;
	u64 rx_malformed;
	u64 rx_errors;
	u64 tx_frames;
	u64 tx_retries;
	u64 tx_errors;
	u64 tx_q_full;
	u64 rx_drop_malformed;
	u64 tx_drop_queue_full;
	bool link_up;
	u8 bssid[ETH_ALEN];
};

int aic8800_core_register(struct aic8800_core *core);
void aic8800_core_unregister(struct aic8800_core *core);
int aic8800_core_request_firmware(struct aic8800_core *core);
int aic8800_core_release_firmware(struct aic8800_core *core);
int aic8800_core_set_fw_override(struct aic8800_core *core, const char *name);
void aic8800_core_clear_fw_override(struct aic8800_core *core);
const char *aic8800_core_get_fw_active_name(struct aic8800_core *core);
void aic8800_core_set_fw_hooks(struct aic8800_core *core,
			       const struct aic8800_fw_hooks *hooks);

#endif
