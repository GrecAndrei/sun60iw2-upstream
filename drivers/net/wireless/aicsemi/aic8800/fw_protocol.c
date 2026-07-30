// SPDX-License-Identifier: GPL-2.0-only
// GENERATED FILE - DO NOT EDIT MANUALLY
// Generated from: generators/templates/aic8800/

#include <linux/completion.h>
#include <linux/etherdevice.h>
#include <linux/firmware.h>
#include <linux/ieee80211.h>
#include <linux/if_arp.h>
#include <linux/mutex.h>
#include <linux/slab.h>
#include <linux/spinlock.h>
#include <linux/unaligned.h>
#include <linux/workqueue.h>
#include <net/cfg80211.h>
#include <net/ieee80211_radiotap.h>
#include "core_types.h"
#include "fw_protocol.h"

#define AIC_TASK_MM		0
#define AIC_TASK_DBG		1
#define AIC_TASK_SCANU		4
#define AIC_TASK_ME		5
#define AIC_TASK_SM		6
#define AIC_MSG(task, index)	(((task) << 10) | (index))

#define AIC_MM_RESET_REQ	AIC_MSG(AIC_TASK_MM, 0)
#define AIC_MM_RESET_CFM	AIC_MSG(AIC_TASK_MM, 1)
#define AIC_MM_START_REQ	AIC_MSG(AIC_TASK_MM, 2)
#define AIC_MM_START_CFM	AIC_MSG(AIC_TASK_MM, 3)
#define AIC_MM_ADD_IF_REQ	AIC_MSG(AIC_TASK_MM, 6)
#define AIC_MM_ADD_IF_CFM	AIC_MSG(AIC_TASK_MM, 7)
#define AIC_MM_REMOVE_IF_REQ	AIC_MSG(AIC_TASK_MM, 8)
#define AIC_MM_REMOVE_IF_CFM	AIC_MSG(AIC_TASK_MM, 9)
#define AIC_MM_KEY_ADD_REQ	AIC_MSG(AIC_TASK_MM, 36)
#define AIC_MM_KEY_ADD_CFM	AIC_MSG(AIC_TASK_MM, 37)
#define AIC_MM_KEY_DEL_REQ	AIC_MSG(AIC_TASK_MM, 38)
#define AIC_MM_KEY_DEL_CFM	AIC_MSG(AIC_TASK_MM, 39)
/* Shipped aic8800_fdrv.ko rwnx_send_set_stack_start_req: id=123/124. */
#define AIC_MM_SET_STACK_START_REQ	AIC_MSG(AIC_TASK_MM, 123)
#define AIC_MM_SET_STACK_START_CFM	AIC_MSG(AIC_TASK_MM, 124)

#define AIC_DBG_MEM_READ_REQ	AIC_MSG(AIC_TASK_DBG, 0)
#define AIC_DBG_MEM_READ_CFM	AIC_MSG(AIC_TASK_DBG, 1)
#define AIC_DBG_MEM_WRITE_REQ	AIC_MSG(AIC_TASK_DBG, 2)
#define AIC_DBG_MEM_WRITE_CFM	AIC_MSG(AIC_TASK_DBG, 3)
#define AIC_DBG_BLOCK_WRITE_REQ	AIC_MSG(AIC_TASK_DBG, 11)
#define AIC_DBG_BLOCK_WRITE_CFM	AIC_MSG(AIC_TASK_DBG, 12)
#define AIC_DBG_START_APP_REQ	AIC_MSG(AIC_TASK_DBG, 13)
#define AIC_DBG_START_APP_CFM	AIC_MSG(AIC_TASK_DBG, 14)

#define AIC_SCAN_START_REQ	AIC_MSG(AIC_TASK_SCANU, 0)
#define AIC_SCAN_START_CFM	AIC_MSG(AIC_TASK_SCANU, 1)
#define AIC_SCAN_RESULT_IND	AIC_MSG(AIC_TASK_SCANU, 4)
#define AIC_SCAN_VENDOR_IE_REQ	AIC_MSG(AIC_TASK_SCANU, 7)
#define AIC_SCAN_VENDOR_IE_CFM	AIC_MSG(AIC_TASK_SCANU, 8)
#define AIC_SCAN_ACCEPT_CFM	AIC_MSG(AIC_TASK_SCANU, 9)
#define AIC_ME_CONFIG_REQ	AIC_MSG(AIC_TASK_ME, 0)
#define AIC_ME_CONFIG_CFM	AIC_MSG(AIC_TASK_ME, 1)
#define AIC_ME_CHAN_CONFIG_REQ	AIC_MSG(AIC_TASK_ME, 2)
#define AIC_ME_CHAN_CONFIG_CFM	AIC_MSG(AIC_TASK_ME, 3)
/* Shipped aic8800_fdrv.ko: ME_CONFIG_MONITOR_REQ/CFM = 5137/5138. */
#define AIC_ME_CONFIG_MONITOR_REQ	AIC_MSG(AIC_TASK_ME, 17)
#define AIC_ME_CONFIG_MONITOR_CFM	AIC_MSG(AIC_TASK_ME, 18)
#define AIC_SM_CONNECT_REQ	AIC_MSG(AIC_TASK_SM, 0)
#define AIC_SM_CONNECT_CFM	AIC_MSG(AIC_TASK_SM, 1)
#define AIC_SM_CONNECT_IND	AIC_MSG(AIC_TASK_SM, 2)
#define AIC_SM_DISCONNECT_REQ	AIC_MSG(AIC_TASK_SM, 3)
#define AIC_SM_DISCONNECT_CFM	AIC_MSG(AIC_TASK_SM, 4)
#define AIC_SM_DISCONNECT_IND	AIC_MSG(AIC_TASK_SM, 5)

#define AIC_DRIVER_TASK		100
#define AIC_CMD_TIMEOUT		msecs_to_jiffies(3000)
#define AIC_SCAN_CHANNELS	42
#define AIC_SCAN_SSIDS		3
#define AIC_FW_ADDR		0x00120000
#define AIC_FW_BLOCK		1024
#define AIC_RX_DATA_HEADER	60

/* Firmware MM_* interface types (not nl80211_iftype). */
#define AIC_MM_STA		0
#define AIC_MM_MONITOR		4

#define AIC_PHY_CHNL_BW_20	0
#define AIC_PHY_CHNL_BW_40	1
#define AIC_PHY_CHNL_BW_80	2
#define AIC_PHY_CHNL_BW_160	3
#define AIC_PHY_CHNL_BW_80P80	4

/* hostdesc.flags — matches shipped aic8800_fdrv rwnx_tx.h */
#define AIC_TXU_CNTRL_RETRY		BIT(0)
#define AIC_TXU_CNTRL_MORE_DATA		BIT(2)
#define AIC_TXU_CNTRL_MGMT		BIT(3)
#define AIC_TXU_CNTRL_MGMT_NO_CCK	BIT(4)
#define AIC_TXU_CNTRL_AMSDU		BIT(6)
#define AIC_TXU_CNTRL_MGMT_ROBUST	BIT(7)
#define AIC_TXU_CNTRL_USE_4ADDR		BIT(8)
#define AIC_TXU_CNTRL_EOSP		BIT(9)
#define AIC_TXU_CNTRL_MESH_FWD		BIT(10)
#define AIC_TXU_CNTRL_TDLS		BIT(11)

#define AIC_TX_AC_VO			3
#define AIC_INVALID_STA			0xff
#define AIC_INVALID_TID			0xff

struct aic_mac_addr {
	__le16 word[3];
};

struct aic_mac_ssid {
	u8 length;
	u8 value[IEEE80211_MAX_SSID_LEN];
};

struct aic_chan_def {
	__le16 frequency;
	u8 band;
	u8 flags;
	s8 tx_power;
};

struct aic_mm_start_req {
	__le32 phy_config[16];
	__le32 uapsd_timeout;
	__le16 lp_clock_accuracy;
};

struct aic_mm_add_if_req {
	u8 type;
	struct aic_mac_addr address;
	bool p2p;
};

struct aic_mm_add_if_cfm {
	u8 status;
	u8 instance;
};

struct aic_me_config_req {
	u8 ht_capability[32];
	u8 vht_capability[12];
	u8 he_capability[56];
	__le16 tx_lifetime;
	u8 max_bandwidth;
	bool ht_supported;
	bool vht_supported;
	bool he_supported;
	bool he_ul_enabled;
	bool power_save;
	bool antenna_diversity;
	bool dynamic_power_save;
} __aligned(4);

struct aic_me_chan_config_req {
	struct aic_chan_def channels_2g[14];
	struct aic_chan_def channels_5g[28];
	u8 count_2g;
	u8 count_5g;
};

struct aic_mac_chan_op {
	u8 band;
	u8 type;
	__le16 prim20_freq;
	__le16 center1_freq;
	__le16 center2_freq;
	s8 tx_power;
	u8 flags;
} __packed;

struct aic_me_config_monitor_req {
	struct aic_mac_chan_op chan;
	u8 chan_set;
	u8 uf;
} __packed;

struct aic_scan_start_req {
	struct aic_chan_def channels[AIC_SCAN_CHANNELS];
	struct aic_mac_ssid ssids[AIC_SCAN_SSIDS];
	struct aic_mac_addr bssid;
	__le32 additional_ies;
	__le16 additional_ie_len;
	u8 vif_index;
	u8 channel_count;
	u8 ssid_count;
	bool no_cck;
	__le32 duration;
};

struct aic_scan_result_ind {
	__le16 length;
	__le16 frame_control;
	__le16 center_frequency;
	u8 band;
	u8 station_index;
	u8 instance;
	s8 rssi;
	__le32 payload[];
};

struct aic_scan_vendor_ie_req {
	__le16 length;
	u8 vif_index;
	u8 data[256];
};

struct aic_sm_connect_req {
	struct aic_mac_ssid ssid;
	struct aic_mac_addr bssid;
	struct aic_chan_def channel;
	__le32 flags;
	__be16 control_port_ethertype;
	__le16 ie_len;
	__le16 listen_interval;
	bool dont_wait_bcmc;
	u8 auth_type;
	u8 uapsd_queues;
	u8 vif_index;
	__le32 ie_buffer[64];
};

struct aic_sm_connect_ind {
	__le16 status_code;
	struct aic_mac_addr bssid;
	bool roamed;
	u8 vif_index;
	u8 ap_index;
	u8 channel_index;
	bool qos;
	u8 acm;
	__le16 request_ie_len;
	__le16 response_ie_len;
	__le32 assoc_ie_buffer[200];
	__le16 aid;
	u8 band;
	__le16 center_frequency;
	u8 width;
	__le32 center_frequency1;
	__le32 center_frequency2;
	__le32 ac_parameters[4];
};

struct aic_sm_disconnect_req {
	__le16 reason;
	u8 vif_index;
};

struct aic_sm_disconnect_ind {
	__le16 reason;
	u8 vif_index;
	bool ft_over_ds;
	u8 reassociation;
};

struct aic_key_material {
	u8 length;
	__le32 value[8];
};

struct aic_mm_key_add_req {
	u8 key_index;
	u8 station_index;
	struct aic_key_material key;
	u8 cipher;
	u8 instance;
	u8 spp;
	bool pairwise;
};

struct aic_mm_key_add_cfm {
	u8 status;
	u8 hardware_index;
};

struct aic_tx_descriptor {
	__le16 packet_len;
	__le16 extended_flags;
	__le32 host_id;
	struct aic_mac_addr destination;
	struct aic_mac_addr source;
	__be16 ethertype;
	u8 access_category;
	u8 tid;
	u8 vif_index;
	u8 station_index;
	__le16 flags;
};

struct aic8800_protocol {
	struct aic8800_core *core;
	/* Serializes commands because firmware supports one confirmation waiter. */
	struct mutex command_mutex;
	/* Protects confirmation and asynchronous cfg80211 request state. */
	spinlock_t state_lock;
	struct completion command_done;
	u16 expected_confirmation;
	void *confirmation;
	size_t confirmation_size;
	int command_status;
	struct cfg80211_scan_request *scan_request;
	/* cfg80211_scan_done must not run under wiphy mutex — defer it. */
	struct cfg80211_scan_request *pending_scan_done;
	struct work_struct scan_done_work;
	u8 vif_index;
	u8 ap_index;
	u8 key_hardware_index[4];
	bool interface_open;
	bool monitor_chan_set;
	struct aic_mac_chan_op monitor_chan;
};

static_assert(sizeof(struct aic_mm_start_req) == 72);
static_assert(sizeof(struct aic_me_config_req) == 112);
static_assert(sizeof(struct aic_me_chan_config_req) == 254);
static_assert(sizeof(struct aic_me_config_monitor_req) == 12);
static_assert(sizeof(struct aic_scan_start_req) == 376);
static_assert(sizeof(struct aic_scan_result_ind) == 12);
static_assert(sizeof(struct aic_scan_vendor_ie_req) == 260);
static_assert(sizeof(struct aic_sm_connect_req) == 320);
static_assert(sizeof(struct aic_tx_descriptor) == 28);

static void aic8800_scan_done_workfn(struct work_struct *work)
{
	struct aic8800_protocol *protocol =
		container_of(work, struct aic8800_protocol, scan_done_work);
	struct cfg80211_scan_request *request;
	struct cfg80211_scan_info info = { .aborted = true };
	unsigned long flags;

	spin_lock_irqsave(&protocol->state_lock, flags);
	request = protocol->pending_scan_done;
	protocol->pending_scan_done = NULL;
	spin_unlock_irqrestore(&protocol->state_lock, flags);
	if (request)
		cfg80211_scan_done(request, &info);
}

static void aic8800_abort_scan_deferred(struct aic8800_protocol *protocol)
{
	struct cfg80211_scan_request *request;
	unsigned long flags;

	spin_lock_irqsave(&protocol->state_lock, flags);
	request = protocol->scan_request;
	protocol->scan_request = NULL;
	if (request) {
		/*
		 * change_virtual_intf / other cfg80211 ops hold the wiphy
		 * mutex. cfg80211_scan_done() must not run there — queue it.
		 */
		if (!protocol->pending_scan_done)
			protocol->pending_scan_done = request;
		else
			request = NULL;
	}
	spin_unlock_irqrestore(&protocol->state_lock, flags);
	if (request)
		schedule_work(&protocol->scan_done_work);
}

static u8 aic8800_crc8(const u8 *data, size_t len)
{
	u8 crc = 0;
	size_t index;

	for (index = 0; index < len; index++) {
		u8 value = data[index];
		int bit;

		for (bit = 0; bit < 8; bit++) {
			u8 mix = (crc ^ value) & 0x80;

			crc <<= 1;
			if (mix)
				crc ^= 0x07;
			value <<= 1;
		}
	}

	return crc;
}

static int aic8800_send_message(struct aic8800_protocol *protocol, u16 id,
				u16 destination, const void *parameters,
				size_t parameter_len)
{
	struct aic8800_core *core = protocol->core;
	size_t lmac_len = 8 + parameter_len;
	size_t frame_len = 8 + lmac_len;
	u8 *frame;
	int ret;

	if (!core->tx_command || parameter_len > U16_MAX)
		return -EOPNOTSUPP;

	frame = kzalloc(frame_len, GFP_KERNEL);
	if (!frame)
		return -ENOMEM;

	put_unaligned_le16(lmac_len + 4, frame);
	frame[2] = 0x11;
	frame[3] = aic8800_crc8(frame, 3);
	put_unaligned_le16(id, frame + 8);
	put_unaligned_le16(destination, frame + 10);
	put_unaligned_le16(AIC_DRIVER_TASK, frame + 12);
	put_unaligned_le16(parameter_len, frame + 14);
	if (parameter_len)
		memcpy(frame + 16, parameters, parameter_len);

	ret = core->tx_command(core, frame, frame_len);
	kfree(frame);
	return ret;
}

static int aic8800_command(struct aic8800_protocol *protocol, u16 id,
			   u16 destination, const void *parameters,
			   size_t parameter_len, u16 confirmation_id,
			   void *confirmation, size_t confirmation_size)
{
	struct completion *done = &protocol->command_done;
	unsigned long flags;
	long waited;
	int ret;

	mutex_lock(&protocol->command_mutex);
	reinit_completion(&protocol->command_done);

	spin_lock_irqsave(&protocol->state_lock, flags);
	protocol->expected_confirmation = confirmation_id;
	protocol->confirmation = confirmation;
	protocol->confirmation_size = confirmation_size;
	protocol->command_status = -ETIMEDOUT;
	spin_unlock_irqrestore(&protocol->state_lock, flags);

	ret = aic8800_send_message(protocol, id, destination, parameters,
				   parameter_len);
	if (ret)
		goto clear;

	waited = wait_for_completion_interruptible_timeout(done, AIC_CMD_TIMEOUT);
	if (waited < 0)
		ret = waited;
	else if (!waited)
		ret = -ETIMEDOUT;
	else
		ret = protocol->command_status;

clear:
	spin_lock_irqsave(&protocol->state_lock, flags);
	protocol->expected_confirmation = 0;
	protocol->confirmation = NULL;
	protocol->confirmation_size = 0;
	spin_unlock_irqrestore(&protocol->state_lock, flags);
	mutex_unlock(&protocol->command_mutex);
	return ret;
}

static void aic8800_complete_command(struct aic8800_protocol *protocol,
				     u16 id, const u8 *parameters,
				     size_t parameter_len)
{
	unsigned long flags;
	bool complete_command = false;

	spin_lock_irqsave(&protocol->state_lock, flags);
	if (protocol->expected_confirmation == id) {
		if (protocol->confirmation && protocol->confirmation_size)
			memcpy(protocol->confirmation, parameters,
			       min(parameter_len, protocol->confirmation_size));
		protocol->command_status = 0;
		protocol->expected_confirmation = 0;
		complete_command = true;
	}
	spin_unlock_irqrestore(&protocol->state_lock, flags);

	if (complete_command)
		complete(&protocol->command_done);
}

static int aic8800_mem_read(struct aic8800_protocol *protocol, u32 address,
			    u32 *value)
{
	struct {
		__le32 address;
	} request = { cpu_to_le32(address) };
	struct {
		__le32 address;
		__le32 value;
	} confirmation = {};
	int ret;

	ret = aic8800_command(protocol, AIC_DBG_MEM_READ_REQ, AIC_TASK_DBG,
			      &request, sizeof(request), AIC_DBG_MEM_READ_CFM,
			      &confirmation, sizeof(confirmation));
	if (!ret)
		*value = le32_to_cpu(confirmation.value);
	return ret;
}

static int aic8800_mem_write(struct aic8800_protocol *protocol, u32 address,
			     u32 value)
{
	struct {
		__le32 address;
		__le32 value;
	} request = { cpu_to_le32(address), cpu_to_le32(value) };

	return aic8800_command(protocol, AIC_DBG_MEM_WRITE_REQ, AIC_TASK_DBG,
			       &request, sizeof(request), AIC_DBG_MEM_WRITE_CFM,
			       NULL, 0);
}

static int aic8800_write_firmware(struct aic8800_protocol *protocol,
				  const struct firmware *firmware)
{
	struct {
		__le32 address;
		__le32 size;
		u8 data[AIC_FW_BLOCK];
	} *request;
	size_t offset;
	int ret = 0;

	request = kzalloc_obj(*request, GFP_KERNEL);
	if (!request)
		return -ENOMEM;

	for (offset = 0; offset < firmware->size; offset += AIC_FW_BLOCK) {
		size_t count = min_t(size_t, AIC_FW_BLOCK,
				     firmware->size - offset);

		request->address = cpu_to_le32(AIC_FW_ADDR + offset);
		request->size = cpu_to_le32(count);
		memcpy(request->data, firmware->data + offset, count);
		if (count < AIC_FW_BLOCK)
			memset(request->data + count, 0, AIC_FW_BLOCK - count);

		ret = aic8800_command(protocol, AIC_DBG_BLOCK_WRITE_REQ,
				      AIC_TASK_DBG, request, sizeof(*request),
				      AIC_DBG_BLOCK_WRITE_CFM, NULL, 0);
		if (ret)
			break;
	}

	kfree(request);
	return ret;
}

static int aic8800_configure_firmware_patch(struct aic8800_protocol *protocol)
{
	u32 config_base;
	u32 patch_structure;
	u32 patch_buffer = 0x0016f800;
	u32 version;
	int ret;
	int index;

	ret = aic8800_mem_read(protocol, AIC_FW_ADDR + 0x198, &config_base);
	if (ret)
		return ret;
	ret = aic8800_mem_read(protocol, AIC_FW_ADDR + 0x1a0,
			       &patch_structure);
	if (ret)
		return ret;
	ret = aic8800_mem_read(protocol, AIC_FW_ADDR + 0x1c, &version);
	if (ret)
		return ret;
	if (version > 0x06090100) {
		ret = aic8800_mem_read(protocol, AIC_FW_ADDR + 0x1a4,
				       &patch_buffer);
		if (ret)
			return ret;
	}

	ret = aic8800_mem_write(protocol, patch_structure, 0x48435450);
	if (ret)
		return ret;
	ret = aic8800_mem_write(protocol, patch_structure + 4, patch_buffer);
	if (ret)
		return ret;
	ret = aic8800_mem_write(protocol, patch_structure + 8, 0x50544348);
	if (ret)
		return ret;
	ret = aic8800_mem_write(protocol, patch_structure + 12, 0);
	if (ret)
		return ret;
	for (index = 0; index < 4; index++) {
		ret = aic8800_mem_write(protocol,
					patch_structure + 48 + index * 4, 0);
		if (ret)
			return ret;
	}

	dev_dbg(protocol->core->dev, "firmware config base %#x version %#x\n",
		config_base, version);
	return 0;
}

int aic8800_protocol_init(struct aic8800_core *core)
{
	struct aic8800_protocol *protocol;

	if (!core)
		return -EINVAL;
	/*
	 * Non-devm: boot uses function-1 as transport while bound to
	 * function-2. A managed alloc on function-1 would survive the
	 * function-2 probe teardown and block the runtime 0x0082 bind
	 * with "Resources present before probing".
	 */
	protocol = kzalloc(sizeof(*protocol), GFP_KERNEL);
	if (!protocol)
		return -ENOMEM;

	protocol->core = core;
	protocol->vif_index = 0xff;
	protocol->ap_index = 0xff;
	mutex_init(&protocol->command_mutex);
	spin_lock_init(&protocol->state_lock);
	init_completion(&protocol->command_done);
	INIT_WORK(&protocol->scan_done_work, aic8800_scan_done_workfn);
	core->protocol = protocol;
	return 0;
}

void aic8800_protocol_deinit(struct aic8800_core *core)
{
	struct aic8800_protocol *protocol;
	struct cfg80211_scan_request *request = NULL;
	struct cfg80211_scan_request *pending = NULL;
	struct cfg80211_scan_info info = { .aborted = true };
	unsigned long flags;

	if (!core || !core->protocol)
		return;
	protocol = core->protocol;
	cancel_work_sync(&protocol->scan_done_work);
	spin_lock_irqsave(&protocol->state_lock, flags);
	request = protocol->scan_request;
	pending = protocol->pending_scan_done;
	protocol->scan_request = NULL;
	protocol->pending_scan_done = NULL;
	protocol->command_status = -ENODEV;
	protocol->expected_confirmation = 0;
	spin_unlock_irqrestore(&protocol->state_lock, flags);
	complete_all(&protocol->command_done);
	if (request)
		cfg80211_scan_done(request, &info);
	if (pending)
		cfg80211_scan_done(pending, &info);
	core->protocol = NULL;
	kfree(protocol);
}

int aic8800_protocol_boot(struct aic8800_core *core)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct {
		__le32 boot_address;
		__le32 boot_type;
	} start = { cpu_to_le32(AIC_FW_ADDR), cpu_to_le32(1) };
	int ret;

	ret = aic8800_core_request_firmware(core);
	if (ret)
		return ret;
	ret = aic8800_write_firmware(protocol, core->fw_data);
	if (ret)
		goto release;
	ret = aic8800_configure_firmware_patch(protocol);
	if (ret)
		goto release;
	ret = aic8800_command(protocol, AIC_DBG_START_APP_REQ, AIC_TASK_DBG,
			      &start, sizeof(start), AIC_DBG_START_APP_CFM,
			      NULL, 0);
release:
	aic8800_core_release_firmware(core);
	return ret;
}

static void aic8800_fill_channels(struct aic_me_chan_config_req *request)
{
	int index;

	for (index = 0; index < 14; index++) {
		request->channels_2g[index].frequency =
			cpu_to_le16(index == 13 ? 2484 : 2412 + index * 5);
		request->channels_2g[index].band = NL80211_BAND_2GHZ;
		request->channels_2g[index].tx_power = 20;
	}
	request->count_2g = 14;
	for (index = 0; index < 28; index++) {
		static const u8 channels[] = {
			36, 40, 44, 48, 52, 56, 60, 64,
			100, 104, 108, 112, 116, 120, 124, 128,
			132, 136, 140, 144, 149, 153, 157, 161,
			165, 169, 173, 177,
		};

		request->channels_5g[index].frequency =
			cpu_to_le16(5000 + channels[index] * 5);
		request->channels_5g[index].band = NL80211_BAND_5GHZ;
		request->channels_5g[index].tx_power = 20;
	}
	request->count_5g = 28;
}

int aic8800_protocol_runtime_config(struct aic8800_core *core)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_me_config_req config = {};
	struct aic_me_chan_config_req channels = {};
	struct {
		u8 is_stack_start;
		u8 efuse_valid;
		u8 set_vendor_info;
		u8 conf_filter_null;
	} stack = { .is_stack_start = 1 };
	int ret;

	/*
	 * Shipped aic8800_fdrv.ko rwnx_cfg80211_init order for D80:
	 * set_stack_start → reset → me_config → me_chan_config.
	 * Open then does mm_start + add_if. Skipping this leaves scan empty.
	 */
	ret = aic8800_command(protocol, AIC_MM_SET_STACK_START_REQ, AIC_TASK_MM,
			      &stack, sizeof(stack), AIC_MM_SET_STACK_START_CFM,
			      NULL, 0);
	if (ret)
		return ret;
	ret = aic8800_command(protocol, AIC_MM_RESET_REQ, AIC_TASK_MM,
			      NULL, 0, AIC_MM_RESET_CFM, NULL, 0);
	if (ret)
		return ret;
	config.tx_lifetime = cpu_to_le16(0xffff);
	ret = aic8800_command(protocol, AIC_ME_CONFIG_REQ, AIC_TASK_ME,
			      &config, sizeof(config), AIC_ME_CONFIG_CFM,
			      NULL, 0);
	if (ret)
		return ret;
	aic8800_fill_channels(&channels);
	return aic8800_command(protocol, AIC_ME_CHAN_CONFIG_REQ, AIC_TASK_ME,
			       &channels, sizeof(channels),
			       AIC_ME_CHAN_CONFIG_CFM, NULL, 0);
}

static u8 aic8800_chan_bw(enum nl80211_chan_width width)
{
	switch (width) {
	case NL80211_CHAN_WIDTH_40:
		return AIC_PHY_CHNL_BW_40;
	case NL80211_CHAN_WIDTH_80:
		return AIC_PHY_CHNL_BW_80;
	case NL80211_CHAN_WIDTH_160:
		return AIC_PHY_CHNL_BW_160;
	case NL80211_CHAN_WIDTH_80P80:
		return AIC_PHY_CHNL_BW_80P80;
	default:
		return AIC_PHY_CHNL_BW_20;
	}
}

static int aic8800_send_config_monitor(struct aic8800_protocol *protocol,
				       bool chan_set,
				       const struct aic_mac_chan_op *chan)
{
	struct aic_me_config_monitor_req request = {};

	if (chan_set && chan) {
		request.chan = *chan;
		request.chan_set = 1;
	}
	return aic8800_command(protocol, AIC_ME_CONFIG_MONITOR_REQ, AIC_TASK_ME,
			       &request, sizeof(request),
			       AIC_ME_CONFIG_MONITOR_CFM, NULL, 0);
}

int aic8800_protocol_open(struct aic8800_core *core, const u8 *mac)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_mm_start_req start = {};
	struct aic_mm_add_if_req request = {};
	struct aic_mm_add_if_cfm confirmation = {};
	enum nl80211_iftype iftype = NL80211_IFTYPE_STATION;
	int ret;

	if (core->ndev && core->ndev->ieee80211_ptr)
		iftype = core->ndev->ieee80211_ptr->iftype;

	ret = aic8800_command(protocol, AIC_MM_START_REQ, AIC_TASK_MM,
			      &start, sizeof(start), AIC_MM_START_CFM, NULL, 0);
	if (ret)
		return ret;
	request.type = (iftype == NL80211_IFTYPE_MONITOR) ?
		AIC_MM_MONITOR : AIC_MM_STA;
	memcpy(&request.address, mac, ETH_ALEN);
	ret = aic8800_command(protocol, AIC_MM_ADD_IF_REQ, AIC_TASK_MM,
			      &request, sizeof(request), AIC_MM_ADD_IF_CFM,
			      &confirmation, sizeof(confirmation));
	if (ret)
		return ret;
	if (confirmation.status)
		return -EIO;
	protocol->vif_index = confirmation.instance;
	protocol->interface_open = true;
	if (iftype == NL80211_IFTYPE_MONITOR && protocol->monitor_chan_set) {
		ret = aic8800_send_config_monitor(protocol, true,
						  &protocol->monitor_chan);
		if (ret)
			return ret;
	}
	return 0;
}

int aic8800_protocol_set_monitor_channel(struct aic8800_core *core,
					 struct cfg80211_chan_def *chandef)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_mac_chan_op chan = {};
	s8 tx_power;

	if (!protocol || !chandef || !chandef->chan)
		return -EINVAL;

	tx_power = chandef->chan->max_power;
	if (tx_power > 127)
		tx_power = 127;
	chan.band = chandef->chan->band;
	chan.type = aic8800_chan_bw(chandef->width);
	chan.prim20_freq = cpu_to_le16(chandef->chan->center_freq);
	chan.center1_freq = cpu_to_le16(chandef->center_freq1);
	chan.center2_freq = cpu_to_le16(chandef->center_freq2);
	chan.tx_power = tx_power;
	protocol->monitor_chan = chan;
	protocol->monitor_chan_set = true;

	if (!protocol->interface_open)
		return 0;
	return aic8800_send_config_monitor(protocol, true, &chan);
}

int aic8800_protocol_close(struct aic8800_core *core)
{
	struct aic8800_protocol *protocol = core->protocol;
	u8 instance = protocol->vif_index;
	int ret = 0;

	if (protocol->interface_open)
		ret = aic8800_command(protocol, AIC_MM_REMOVE_IF_REQ, AIC_TASK_MM,
				      &instance, sizeof(instance),
				      AIC_MM_REMOVE_IF_CFM, NULL, 0);
	protocol->interface_open = false;
	protocol->vif_index = 0xff;
	protocol->ap_index = 0xff;
	core->link_up = false;
	return ret;
}

/*
 * Shipped aic8800_fdrv change_iface: if the VIF is already up, cancel scan,
 * REMOVE_IF, then ADD_IF with the new type — do not refuse with -EBUSY.
 */
int aic8800_protocol_change_vif_type(struct aic8800_core *core,
				     enum nl80211_iftype iftype)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_mm_add_if_req request = {};
	struct aic_mm_add_if_cfm confirmation = {};
	const u8 *mac;
	u8 instance;
	int ret;

	if (!protocol)
		return -ENODEV;
	if (iftype != NL80211_IFTYPE_STATION &&
	    iftype != NL80211_IFTYPE_MONITOR)
		return -EOPNOTSUPP;
	if (!protocol->interface_open)
		return 0;

	/* Never cfg80211_scan_done() here — we hold the wiphy mutex. */
	aic8800_abort_scan_deferred(protocol);

	if (core->ndev) {
		netif_tx_stop_all_queues(core->ndev);
		netif_carrier_off(core->ndev);
	}

	instance = protocol->vif_index;
	ret = aic8800_command(protocol, AIC_MM_REMOVE_IF_REQ, AIC_TASK_MM,
			      &instance, sizeof(instance),
			      AIC_MM_REMOVE_IF_CFM, NULL, 0);
	protocol->interface_open = false;
	protocol->vif_index = 0xff;
	protocol->ap_index = 0xff;
	core->link_up = false;
	if (ret)
		return ret;

	if (!core->ndev)
		return -ENODEV;
	mac = core->ndev->dev_addr;
	request.type = (iftype == NL80211_IFTYPE_MONITOR) ?
		AIC_MM_MONITOR : AIC_MM_STA;
	memcpy(&request.address, mac, ETH_ALEN);
	ret = aic8800_command(protocol, AIC_MM_ADD_IF_REQ, AIC_TASK_MM,
			      &request, sizeof(request), AIC_MM_ADD_IF_CFM,
			      &confirmation, sizeof(confirmation));
	if (ret)
		return ret;
	if (confirmation.status)
		return -EIO;

	protocol->vif_index = confirmation.instance;
	protocol->interface_open = true;
	if (iftype == NL80211_IFTYPE_MONITOR && protocol->monitor_chan_set) {
		ret = aic8800_send_config_monitor(protocol, true,
						  &protocol->monitor_chan);
		if (ret)
			return ret;
	}
	netif_tx_start_all_queues(core->ndev);
	return 0;
}

int aic8800_protocol_scan(struct aic8800_core *core,
			  struct cfg80211_scan_request *scan)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_scan_start_req request = {};
	unsigned long flags;
	int index;
	int ret;

	if (!protocol->interface_open || scan->n_ssids > AIC_SCAN_SSIDS ||
	    scan->n_channels > AIC_SCAN_CHANNELS || scan->ie_len > 256)
		return -EOPNOTSUPP;
	if (core->ndev && core->ndev->ieee80211_ptr &&
	    core->ndev->ieee80211_ptr->iftype == NL80211_IFTYPE_MONITOR)
		return -EOPNOTSUPP;
	if (scan->ie_len) {
		struct aic_scan_vendor_ie_req vendor_ie = {
			.length = cpu_to_le16(scan->ie_len),
			.vif_index = protocol->vif_index,
		};

		memcpy(vendor_ie.data, scan->ie, scan->ie_len);
		ret = aic8800_command(protocol, AIC_SCAN_VENDOR_IE_REQ,
				      AIC_TASK_SCANU, &vendor_ie,
				      sizeof(vendor_ie), AIC_SCAN_VENDOR_IE_CFM,
				      NULL, 0);
		if (ret)
			return ret;
	}
	for (index = 0; index < scan->n_channels; index++) {
		request.channels[index].frequency =
			cpu_to_le16(scan->channels[index]->center_freq);
		request.channels[index].band = scan->channels[index]->band;
		if (scan->channels[index]->flags & IEEE80211_CHAN_NO_IR)
			request.channels[index].flags |= BIT(0);
		if (scan->channels[index]->flags & IEEE80211_CHAN_DISABLED)
			request.channels[index].flags |= BIT(1);
		if (scan->channels[index]->flags & IEEE80211_CHAN_RADAR)
			request.channels[index].flags |= BIT(2);
		request.channels[index].tx_power = scan->channels[index]->max_power;
	}
	for (index = 0; index < scan->n_ssids; index++) {
		request.ssids[index].length = scan->ssids[index].ssid_len;
		memcpy(request.ssids[index].value, scan->ssids[index].ssid,
		       scan->ssids[index].ssid_len);
	}
	memset(&request.bssid, 0xff, ETH_ALEN);
	request.vif_index = protocol->vif_index;
	request.channel_count = scan->n_channels;
	request.ssid_count = scan->n_ssids;

	spin_lock_irqsave(&protocol->state_lock, flags);
	if (protocol->scan_request) {
		spin_unlock_irqrestore(&protocol->state_lock, flags);
		return -EBUSY;
	}
	protocol->scan_request = scan;
	spin_unlock_irqrestore(&protocol->state_lock, flags);
	ret = aic8800_send_message(protocol, AIC_SCAN_START_REQ, AIC_TASK_SCANU,
				   &request, sizeof(request));
	if (ret) {
		spin_lock_irqsave(&protocol->state_lock, flags);
		protocol->scan_request = NULL;
		spin_unlock_irqrestore(&protocol->state_lock, flags);
	}
	return ret;
}

int aic8800_protocol_connect(struct aic8800_core *core,
			     struct cfg80211_connect_params *sme)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_sm_connect_req request = {};
	u8 status = 0;
	int index;

	if (!protocol->interface_open || sme->ssid_len > IEEE80211_MAX_SSID_LEN ||
	    sme->ie_len > sizeof(request.ie_buffer))
		return -EINVAL;
	request.ssid.length = sme->ssid_len;
	memcpy(request.ssid.value, sme->ssid, sme->ssid_len);
	if (sme->bssid)
		memcpy(&request.bssid, sme->bssid, ETH_ALEN);
	else
		memset(&request.bssid, 0xff, ETH_ALEN);
	if (sme->channel) {
		request.channel.frequency = cpu_to_le16(sme->channel->center_freq);
		request.channel.band = sme->channel->band;
		if (sme->channel->flags & IEEE80211_CHAN_NO_IR)
			request.channel.flags |= BIT(0);
		if (sme->channel->flags & IEEE80211_CHAN_DISABLED)
			request.channel.flags |= BIT(1);
		if (sme->channel->flags & IEEE80211_CHAN_RADAR)
			request.channel.flags |= BIT(2);
	} else {
		request.channel.frequency = cpu_to_le16(U16_MAX);
	}
	for (index = 0; index < sme->crypto.n_ciphers_pairwise; index++)
		if (sme->crypto.ciphers_pairwise[index] == WLAN_CIPHER_SUITE_WEP40 ||
		    sme->crypto.ciphers_pairwise[index] == WLAN_CIPHER_SUITE_WEP104 ||
		    sme->crypto.ciphers_pairwise[index] == WLAN_CIPHER_SUITE_TKIP)
			request.flags |= cpu_to_le32(BIT(2));
	if (sme->crypto.control_port)
		request.flags |= cpu_to_le32(BIT(0));
	if (sme->crypto.control_port_no_encrypt)
		request.flags |= cpu_to_le32(BIT(1));
	if (sme->crypto.wpa_versions)
		request.flags |= cpu_to_le32(BIT(3));
	if (sme->mfp != NL80211_MFP_NO)
		request.flags |= cpu_to_le32(BIT(4));
	if (sme->crypto.control_port_ethertype)
		request.control_port_ethertype =
			sme->crypto.control_port_ethertype;
	else
		request.control_port_ethertype = cpu_to_be16(ETH_P_PAE);
	request.ie_len = cpu_to_le16(sme->ie_len);
	request.listen_interval = cpu_to_le16(5);
	switch (sme->auth_type) {
	case NL80211_AUTHTYPE_AUTOMATIC:
	case NL80211_AUTHTYPE_OPEN_SYSTEM:
		request.auth_type = WLAN_AUTH_OPEN;
		break;
	case NL80211_AUTHTYPE_SHARED_KEY:
		request.auth_type = WLAN_AUTH_SHARED_KEY;
		break;
	case NL80211_AUTHTYPE_FT:
		request.auth_type = WLAN_AUTH_FT;
		break;
	case NL80211_AUTHTYPE_SAE:
		request.auth_type = WLAN_AUTH_SAE;
		break;
	default:
		return -EOPNOTSUPP;
	}
	request.vif_index = protocol->vif_index;
	memcpy(request.ie_buffer, sme->ie, sme->ie_len);
	return aic8800_command(protocol, AIC_SM_CONNECT_REQ, AIC_TASK_SM,
			       &request, sizeof(request), AIC_SM_CONNECT_CFM,
			       &status, sizeof(status)) ?: (status ? -EIO : 0);
}

int aic8800_protocol_disconnect(struct aic8800_core *core, u16 reason)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_sm_disconnect_req request = {
		.reason = cpu_to_le16(reason),
		.vif_index = protocol->vif_index,
	};

	return aic8800_command(protocol, AIC_SM_DISCONNECT_REQ, AIC_TASK_SM,
			       &request, sizeof(request), AIC_SM_DISCONNECT_CFM,
			       NULL, 0);
}

static int aic8800_cipher(u32 cipher)
{
	switch (cipher) {
	case WLAN_CIPHER_SUITE_WEP40: return 0;
	case WLAN_CIPHER_SUITE_TKIP: return 1;
	case WLAN_CIPHER_SUITE_CCMP: return 2;
	case WLAN_CIPHER_SUITE_WEP104: return 3;
	case WLAN_CIPHER_SUITE_AES_CMAC: return 5;
	default: return -EOPNOTSUPP;
	}
}

int aic8800_protocol_add_key(struct aic8800_core *core, u8 key_index,
			     bool pairwise, const u8 *mac_addr,
			     struct key_params *params)
{
	struct aic8800_protocol *protocol = core->protocol;
	struct aic_mm_key_add_req request = {};
	struct aic_mm_key_add_cfm confirmation = {};
	int cipher = aic8800_cipher(params->cipher);
	int ret;

	if (cipher < 0 || key_index >= ARRAY_SIZE(protocol->key_hardware_index) ||
	    params->key_len > sizeof(request.key.value))
		return cipher < 0 ? cipher : -EINVAL;
	request.key_index = key_index;
	request.station_index = pairwise ? protocol->ap_index : 0xff;
	request.key.length = params->key_len;
	memcpy(request.key.value, params->key, params->key_len);
	request.cipher = cipher;
	request.instance = protocol->vif_index;
	request.pairwise = pairwise;
	ret = aic8800_command(protocol, AIC_MM_KEY_ADD_REQ, AIC_TASK_MM,
			      &request, sizeof(request), AIC_MM_KEY_ADD_CFM,
			      &confirmation, sizeof(confirmation));
	if (ret)
		return ret;
	if (confirmation.status)
		return -EIO;
	protocol->key_hardware_index[key_index] = confirmation.hardware_index;
	return 0;
}

int aic8800_protocol_del_key(struct aic8800_core *core, u8 key_index)
{
	struct aic8800_protocol *protocol = core->protocol;
	u8 hardware_index;

	if (key_index >= ARRAY_SIZE(protocol->key_hardware_index))
		return -EINVAL;
	hardware_index = protocol->key_hardware_index[key_index];
	return aic8800_command(protocol, AIC_MM_KEY_DEL_REQ, AIC_TASK_MM,
			       &hardware_index, sizeof(hardware_index),
			       AIC_MM_KEY_DEL_CFM, NULL, 0);
}

static void aic8800_scan_done(struct aic8800_protocol *protocol, bool aborted)
{
	struct cfg80211_scan_request *request;
	struct cfg80211_scan_info info = { .aborted = aborted };
	unsigned long flags;

	spin_lock_irqsave(&protocol->state_lock, flags);
	request = protocol->scan_request;
	protocol->scan_request = NULL;
	spin_unlock_irqrestore(&protocol->state_lock, flags);
	if (request)
		cfg80211_scan_done(request, &info);
}

static void aic8800_scan_result(struct aic8800_protocol *protocol,
				const u8 *parameters, size_t length)
{
	const struct aic_scan_result_ind *result = (const void *)parameters;
	struct cfg80211_inform_bss data = {};
	struct cfg80211_bss *bss;
	size_t frame_len;
	u16 frequency;

	if (length < sizeof(*result))
		return;
	frame_len = le16_to_cpu(result->length);
	if (frame_len > length - sizeof(*result) ||
	    frame_len < offsetof(struct ieee80211_mgmt, u.beacon.variable))
		return;
	frequency = le16_to_cpu(result->center_frequency);
	data.chan = ieee80211_get_channel(protocol->core->wiphy, frequency);
	if (!data.chan)
		return;
	data.signal = result->rssi * 100;
	bss = cfg80211_inform_bss_frame_data(protocol->core->wiphy, &data,
					     (void *)result->payload,
					     frame_len, GFP_ATOMIC);
	if (bss)
		cfg80211_put_bss(protocol->core->wiphy, bss);
}

static void aic8800_connect_indication(struct aic8800_protocol *protocol,
				       const u8 *parameters, size_t length)
{
	const struct aic_sm_connect_ind *indication = (const void *)parameters;
	struct aic8800_core *core = protocol->core;
	size_t request_len;
	size_t response_len;
	const u8 *ies;
	u16 status;

	if (length < offsetof(struct aic_sm_connect_ind, assoc_ie_buffer))
		return;
	request_len = le16_to_cpu(indication->request_ie_len);
	response_len = le16_to_cpu(indication->response_ie_len);
	ies = (const u8 *)indication->assoc_ie_buffer;
	if (request_len + response_len > sizeof(indication->assoc_ie_buffer) ||
	    offsetof(struct aic_sm_connect_ind, assoc_ie_buffer) +
	    request_len + response_len > length)
		return;
	status = le16_to_cpu(indication->status_code);
	if (status == WLAN_STATUS_SUCCESS) {
		protocol->ap_index = indication->ap_index;
		memcpy(core->bssid, &indication->bssid, ETH_ALEN);
		core->link_up = true;
		netif_carrier_on(core->ndev);
	}
	cfg80211_connect_result(core->ndev, (const u8 *)&indication->bssid,
				ies, request_len, ies + request_len, response_len,
				status, GFP_ATOMIC);
}

static void aic8800_disconnect_indication(struct aic8800_protocol *protocol,
					  const u8 *parameters, size_t length)
{
	const struct aic_sm_disconnect_ind *indication = (const void *)parameters;
	struct aic8800_core *core = protocol->core;

	if (length < sizeof(*indication))
		return;
	core->link_up = false;
	protocol->ap_index = 0xff;
	netif_carrier_off(core->ndev);
	cfg80211_disconnected(core->ndev, le16_to_cpu(indication->reason),
			      NULL, 0, false, GFP_ATOMIC);
}

static void aic8800_handle_message(struct aic8800_protocol *protocol, u16 id,
				   const u8 *parameters, size_t length)
{
	aic8800_complete_command(protocol, id, parameters, length);
	switch (id) {
	case AIC_SCAN_RESULT_IND:
		aic8800_scan_result(protocol, parameters, length);
		break;
	case AIC_SCAN_START_CFM:
		aic8800_scan_done(protocol, length >= 2 && parameters[1]);
		break;
	case AIC_SCAN_ACCEPT_CFM:
		break;
	case AIC_SM_CONNECT_IND:
		aic8800_connect_indication(protocol, parameters, length);
		break;
	case AIC_SM_DISCONNECT_IND:
		aic8800_disconnect_indication(protocol, parameters, length);
		break;
	default:
		break;
	}
}

static int aic8800_rx_command(struct aic8800_protocol *protocol,
			      const u8 *frame, size_t length)
{
	u16 parameter_len;
	u16 id;

	if (length < 12)
		return -EINVAL;
	id = get_unaligned_le16(frame);
	parameter_len = get_unaligned_le16(frame + 6);
	if (parameter_len > length - 12)
		return -EINVAL;
	aic8800_handle_message(protocol, id, frame + 12, parameter_len);
	return 0;
}

static int aic8800_rx_monitor(struct aic8800_core *core, const u8 *frame,
			      size_t length)
{
	struct ieee80211_radiotap_header *rtap;
	struct sk_buff *skb;
	size_t rtap_len = sizeof(*rtap);

	if (!core->ndev || length < sizeof(struct ieee80211_hdr_3addr))
		return -EINVAL;
	skb = netdev_alloc_skb(core->ndev, rtap_len + length);
	if (!skb)
		return -ENOMEM;
	skb_reserve(skb, rtap_len);
	skb_put_data(skb, frame, length);
	rtap = skb_push(skb, rtap_len);
	memset(rtap, 0, rtap_len);
	rtap->it_len = cpu_to_le16(rtap_len);
	skb_reset_mac_header(skb);
	skb->dev = core->ndev;
	skb->ip_summed = CHECKSUM_UNNECESSARY;
	skb->pkt_type = PACKET_OTHERHOST;
	skb->protocol = htons(ETH_P_802_2);
	core->ndev->stats.rx_packets++;
	core->ndev->stats.rx_bytes += skb->len;
	core->rx_frames++;
	netif_rx(skb);
	return 0;
}

static int aic8800_rx_data(struct aic8800_core *core, const u8 *frame,
			   size_t length)
{
	struct sk_buff *skb;

	if (!core->ndev || length < sizeof(struct ieee80211_hdr))
		return -EINVAL;
	if (core->ndev->ieee80211_ptr &&
	    core->ndev->ieee80211_ptr->iftype == NL80211_IFTYPE_MONITOR)
		return aic8800_rx_monitor(core, frame, length);
	skb = netdev_alloc_skb_ip_align(core->ndev, length);
	if (!skb)
		return -ENOMEM;
	skb_put_data(skb, frame, length);
	if (ieee80211_data_to_8023(skb, core->ndev->dev_addr,
				   NL80211_IFTYPE_STATION)) {
		dev_kfree_skb_any(skb);
		return -EINVAL;
	}
	skb->dev = core->ndev;
	skb->protocol = eth_type_trans(skb, core->ndev);
	core->ndev->stats.rx_packets++;
	core->ndev->stats.rx_bytes += skb->len;
	core->rx_frames++;
	netif_rx(skb);
	return 0;
}

int aic8800_protocol_rx(struct aic8800_core *core, const u8 *buffer, size_t len)
{
	struct aic8800_protocol *protocol = core->protocol;
	size_t offset = 0;
	int handled = 0;

	while (len - offset >= 4) {
		const u8 *frame = buffer + offset;
		size_t packet_len = get_unaligned_le16(frame);
		u8 type = frame[2] & 0x7f;
		size_t advance;
		int ret;

		if (type == 0x11 || type == 0x12 || type == 0x13) {
			advance = ALIGN(packet_len, 4) + 4;
			if (packet_len > len - offset - 4 || advance > len - offset)
				return handled ? handled : -EINVAL;
			if (type == 0x11)
				ret = aic8800_rx_command(protocol, frame + 4, packet_len);
			else
				ret = 0;
		} else {
			advance = ALIGN(packet_len + AIC_RX_DATA_HEADER, 4);
			if (packet_len > len - offset - AIC_RX_DATA_HEADER ||
			    advance > len - offset)
				return handled ? handled : -EINVAL;
			ret = aic8800_rx_data(core, frame + AIC_RX_DATA_HEADER,
					      packet_len);
		}
		if (ret)
			core->rx_malformed++;
		else
			handled++;
		offset += advance;
	}
	return handled;
}

static int aic8800_build_host_tx(struct aic8800_core *core,
				 const u8 *payload, size_t payload_len,
				 u16 flags, u8 tid, u8 station_index,
				 const u8 *da, const u8 *sa, __be16 ethertype,
				 u8 access_category, u8 **out, size_t *out_len)
{
	struct aic_tx_descriptor *descriptor;
	size_t packet_len;
	u8 *buffer;

	if (!core || !core->protocol || !payload || !payload_len ||
	    payload_len > U16_MAX)
		return -EINVAL;

	packet_len = sizeof(*descriptor) + payload_len;
	buffer = kzalloc(packet_len, GFP_ATOMIC);
	if (!buffer)
		return -ENOMEM;

	descriptor = (void *)buffer;
	descriptor->packet_len = cpu_to_le16(payload_len);
	descriptor->host_id = 0;
	if (da)
		memcpy(&descriptor->destination, da, ETH_ALEN);
	if (sa)
		memcpy(&descriptor->source, sa, ETH_ALEN);
	descriptor->ethertype = ethertype;
	descriptor->access_category = access_category;
	descriptor->tid = tid;
	descriptor->vif_index = core->protocol->vif_index;
	descriptor->station_index = station_index;
	descriptor->flags = cpu_to_le16(flags);
	memcpy(buffer + sizeof(*descriptor), payload, payload_len);

	*out = buffer;
	*out_len = packet_len;
	return 0;
}

static int aic8800_submit_host_tx(struct aic8800_core *core, u8 *buffer,
				  size_t buffer_len)
{
	int ret;

	if (!core->tx_frame) {
		kfree(buffer);
		return -EOPNOTSUPP;
	}

	ret = core->tx_frame(core, buffer, buffer_len);
	kfree(buffer);
	return ret;
}

int aic8800_protocol_wrap_tx(struct aic8800_core *core, const u8 *frame,
			     size_t frame_len, u8 **out, size_t *out_len)
{
	const struct ethhdr *ethernet = (const void *)frame;

	if (frame_len < ETH_HLEN)
		return -EINVAL;

	return aic8800_build_host_tx(core, frame + ETH_HLEN,
				     frame_len - ETH_HLEN, 0, 0,
				     core->protocol->ap_index,
				     ethernet->h_dest, ethernet->h_source,
				     ethernet->h_proto, 1, out, out_len);
}

int aic8800_protocol_mgmt_tx(struct aic8800_core *core, const u8 *frame,
			     size_t frame_len, bool no_cck, bool robust)
{
	struct ieee80211_hdr *hdr = (void *)frame;
	u8 *buffer;
	size_t buffer_len;
	u16 flags = AIC_TXU_CNTRL_MGMT;
	int ret;

	if (!frame || frame_len < sizeof(*hdr))
		return -EINVAL;
	if (!ieee80211_is_mgmt(hdr->frame_control))
		return -EINVAL;

	if (no_cck)
		flags |= AIC_TXU_CNTRL_MGMT_NO_CCK;
	if (robust)
		flags |= AIC_TXU_CNTRL_MGMT_ROBUST;

	ret = aic8800_build_host_tx(core, frame, frame_len, flags,
				    AIC_INVALID_TID, AIC_INVALID_STA,
				    ieee80211_get_DA(hdr),
				    ieee80211_get_SA(hdr),
				    0, AIC_TX_AC_VO, &buffer, &buffer_len);
	if (ret)
		return ret;

	return aic8800_submit_host_tx(core, buffer, buffer_len);
}

/*
 * Probe path: ship an arbitrary 802.11 MPDU with TXU_CNTRL_MGMT set.
 * Firmware treats that flag as "host-built MPDU" (vendor raw_frame stub
 * did the same). Use this from monitor inject to test non-mgmt FC values.
 */
int aic8800_protocol_mpdu_tx(struct aic8800_core *core, const u8 *mpdu,
			     size_t mpdu_len, bool no_cck)
{
	struct ieee80211_hdr *hdr = (void *)mpdu;
	u8 *buffer;
	size_t buffer_len;
	u16 flags = AIC_TXU_CNTRL_MGMT;
	int ret;

	if (!mpdu || mpdu_len < sizeof(*hdr))
		return -EINVAL;

	if (no_cck)
		flags |= AIC_TXU_CNTRL_MGMT_NO_CCK;

	dev_dbg(core->dev, "mpdu_tx fc=0x%04x len=%zu flags=0x%x\n",
		le16_to_cpu(hdr->frame_control), mpdu_len, flags);

	ret = aic8800_build_host_tx(core, mpdu, mpdu_len, flags,
				    AIC_INVALID_TID, AIC_INVALID_STA,
				    ieee80211_get_DA(hdr),
				    ieee80211_get_SA(hdr),
				    0, AIC_TX_AC_VO, &buffer, &buffer_len);
	if (ret)
		return ret;

	return aic8800_submit_host_tx(core, buffer, buffer_len);
}

EXPORT_SYMBOL_GPL(aic8800_protocol_init);
EXPORT_SYMBOL_GPL(aic8800_protocol_deinit);
EXPORT_SYMBOL_GPL(aic8800_protocol_boot);
EXPORT_SYMBOL_GPL(aic8800_protocol_rx);
