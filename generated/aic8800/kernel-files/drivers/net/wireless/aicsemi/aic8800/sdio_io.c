// SPDX-License-Identifier: GPL-2.0-only
// GENERATED FILE - DO NOT EDIT MANUALLY

#include <linux/delay.h>
#include <linux/mmc/card.h>
#include <linux/mmc/sdio.h>
#include <linux/mmc/sdio_func.h>
#include <linux/slab.h>
#include "sdio_io.h"

#define AIC_SDIO_BLOCK_SIZE 512
#define AIC_SDIO_FLOW_CTRL  0x03
#define AIC_SDIO_INT_STATUS 0x04
#define AIC_SDIO_BYTE_LEN   0x05
#define AIC_SDIO_RD_PORT    0x0f
#define AIC_SDIO_WR_PORT    0x10

int aic8800_sdio_io_init(struct sdio_func *func)
{
	u8 ready;
	int ret;

	sdio_claim_host(func);
	func->card->quirks |= MMC_QUIRK_LENIENT_FN0;
	ret = sdio_set_block_size(func, AIC_SDIO_BLOCK_SIZE);
	if (!ret)
		ret = sdio_enable_func(func);
	if (!ret)
		sdio_writeb(func, 0x01, 0x07, &ret);
	if (!ret)
		sdio_writeb(func, 0x11, 0x02, &ret);
	sdio_release_host(func);
	if (ret)
		return ret;
	usleep_range(10000, 12000);
	sdio_claim_host(func);
	ready = sdio_readb(func, 0x01, &ret);
	sdio_release_host(func);
	if (!ret && !(ready & 0x10))
		ret = -ETIMEDOUT;
	if (ret)
		aic8800_sdio_io_deinit(func);
	return ret;
}

void aic8800_sdio_io_deinit(struct sdio_func *func)
{
	sdio_claim_host(func);
	sdio_disable_func(func);
	sdio_release_host(func);
}

int aic8800_sdio_write(struct sdio_func *func, const u8 *data, size_t len)
{
	size_t transfer_len;
	u8 *transfer;
	u8 credits = 0;
	int attempt;
	int ret = 0;

	if (!data || !len)
		return -EINVAL;
	for (attempt = 0; attempt < 50; attempt++) {
		sdio_claim_host(func);
		credits = sdio_readb(func, AIC_SDIO_FLOW_CTRL, &ret);
		sdio_release_host(func);
		if (ret || credits)
			break;
		usleep_range(200, 400);
	}
	if (ret)
		return ret;
	if (!credits)
		return -EBUSY;
	transfer_len = roundup(len, AIC_SDIO_BLOCK_SIZE);
	transfer = kzalloc(transfer_len, GFP_KERNEL);
	if (!transfer)
		return -ENOMEM;
	memcpy(transfer, data, len);
	sdio_claim_host(func);
	ret = sdio_writesb(func, AIC_SDIO_WR_PORT, transfer, transfer_len);
	sdio_release_host(func);
	kfree(transfer);
	return ret;
}

int aic8800_sdio_read(struct sdio_func *func, u8 **data, size_t *len)
{
	u8 status;
	u8 byte_len;
	size_t transfer_len;
	u8 *transfer;
	int ret;

	sdio_claim_host(func);
	status = sdio_readb(func, AIC_SDIO_INT_STATUS, &ret);
	sdio_release_host(func);
	if (ret)
		return ret;
	if (!status)
		return -ENODATA;
	if (status == 120) {
		sdio_claim_host(func);
		byte_len = sdio_readb(func, AIC_SDIO_BYTE_LEN, &ret);
		sdio_release_host(func);
		if (ret)
			return ret;
		transfer_len = byte_len * 4;
	} else {
		transfer_len = (status & 0x7f) * AIC_SDIO_BLOCK_SIZE;
	}
	if (!transfer_len)
		return -ENODATA;
	transfer = kmalloc(transfer_len, GFP_KERNEL);
	if (!transfer)
		return -ENOMEM;
	sdio_claim_host(func);
	ret = sdio_readsb(func, transfer, AIC_SDIO_RD_PORT, transfer_len);
	sdio_release_host(func);
	if (ret) {
		kfree(transfer);
		return ret;
	}
	*data = transfer;
	*len = transfer_len;
	return 0;
}
