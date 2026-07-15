// SPDX-License-Identifier: GPL-2.0-only
// GENERATED FILE - DO NOT EDIT MANUALLY

#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/mmc/sdio_func.h>
#include <linux/module.h>
#include <linux/netdevice.h>
#include <linux/regulator/consumer.h>
#include <linux/skbuff.h>
#include <linux/workqueue.h>
#include "core_types.h"
#include "fw_protocol.h"
#include "sdio_io.h"

#define AIC_VENDOR_ID      0x5449
#define AIC_BOOT_DEVICE_ID 0x0182
#define AIC_WIFI_DEVICE_ID 0x0082
#define AIC_TX_QUEUE_MAX   128

struct aic8800_sdio {
	struct aic8800_core core;
	struct sdio_func *func;
	struct regulator *vddio;
	struct gpio_desc *reset_gpio;
	struct sk_buff_head tx_queue;
	struct work_struct tx_work;
	struct work_struct rx_work;
	bool irq_claimed;
	bool core_registered;
	bool stopping;
};

static int aic8800_sdio_power_on(struct aic8800_sdio *sdio)
{
	int ret;

	if (sdio->vddio) {
		ret = regulator_enable(sdio->vddio);
		if (ret)
			return ret;
	}
	if (sdio->reset_gpio) {
		gpiod_set_value_cansleep(sdio->reset_gpio, 1);
		msleep(20);
		gpiod_set_value_cansleep(sdio->reset_gpio, 0);
		msleep(20);
	}
	return 0;
}

static void aic8800_sdio_power_off(struct aic8800_sdio *sdio)
{
	if (sdio->reset_gpio)
		gpiod_set_value_cansleep(sdio->reset_gpio, 1);
	if (sdio->vddio)
		regulator_disable(sdio->vddio);
}

static int aic8800_sdio_command(struct aic8800_core *core,
				const u8 *data, size_t len)
{
	struct aic8800_sdio *sdio = core->bus_priv;

	return aic8800_sdio_write(sdio->func, data, len);
}

static int aic8800_sdio_frame(struct aic8800_core *core,
			      const u8 *data, size_t len)
{
	struct aic8800_sdio *sdio = core->bus_priv;
	struct sk_buff *skb;

	if (skb_queue_len(&sdio->tx_queue) >= AIC_TX_QUEUE_MAX)
		return -ENOSPC;
	skb = alloc_skb(len, GFP_ATOMIC);
	if (!skb)
		return -ENOMEM;
	skb_put_data(skb, data, len);
	skb_queue_tail(&sdio->tx_queue, skb);
	schedule_work(&sdio->tx_work);
	return 0;
}

static void aic8800_sdio_tx_work(struct work_struct *work)
{
	struct aic8800_sdio *sdio = container_of(work, struct aic8800_sdio,
						 tx_work);
	struct sk_buff *skb;

	while (!sdio->stopping && (skb = skb_dequeue(&sdio->tx_queue))) {
		u8 *frame;
		size_t frame_len;
		int ret;

		ret = aic8800_protocol_wrap_tx(&sdio->core, skb->data, skb->len,
					       &frame, &frame_len);
		if (!ret) {
			ret = aic8800_sdio_write(sdio->func, frame, frame_len);
			kfree(frame);
		}
		if (ret)
			sdio->core.tx_errors++;
		else
			sdio->core.tx_frames++;
		dev_kfree_skb_any(skb);
	}
	if (sdio->core.ndev && netif_queue_stopped(sdio->core.ndev) &&
	    skb_queue_len(&sdio->tx_queue) < AIC_TX_QUEUE_MAX / 2)
		netif_wake_queue(sdio->core.ndev);
}

static void aic8800_sdio_rx_work(struct work_struct *work)
{
	struct aic8800_sdio *sdio = container_of(work, struct aic8800_sdio,
						 rx_work);
	int budget;

	for (budget = 0; !sdio->stopping && budget < 32; budget++) {
		size_t len;
		u8 *data;
		int ret = aic8800_sdio_read(sdio->func, &data, &len);

		if (ret == -ENODATA)
			break;
		if (ret) {
			sdio->core.rx_errors++;
			break;
		}
		sdio->core.rx_batches++;
		aic8800_protocol_rx(&sdio->core, data, len);
		kfree(data);
	}
}

static void aic8800_sdio_irq(struct sdio_func *func)
{
	struct aic8800_sdio *sdio = sdio_get_drvdata(func);
	u8 pending;
	int ret;

	if (!sdio)
		return;
	sdio->core.irq_count++;
	pending = sdio_readb(func, 0x01, &ret);
	if (!ret)
		sdio_writeb(func, pending & ~0x01, 0x01, &ret);
	if (!sdio->stopping)
		schedule_work(&sdio->rx_work);
}

static int aic8800_sdio_probe(struct sdio_func *func,
			      const struct sdio_device_id *id)
{
	struct aic8800_sdio *sdio;
	int ret;

	sdio = devm_kzalloc(&func->dev, sizeof(*sdio), GFP_KERNEL);
	if (!sdio)
		return -ENOMEM;
	sdio->func = func;
	sdio->core.dev = &func->dev;
	sdio->core.bus_priv = sdio;
	sdio->core.fw_name = "aic8800d80/fmacfw_8800d80.bin";
	sdio->core.tx_command = aic8800_sdio_command;
	sdio->core.tx_frame = aic8800_sdio_frame;
	sdio->vddio = devm_regulator_get_optional(&func->dev, "vddio");
	if (IS_ERR(sdio->vddio)) {
		if (PTR_ERR(sdio->vddio) == -ENODEV)
			sdio->vddio = NULL;
		else
			return PTR_ERR(sdio->vddio);
	}
	sdio->reset_gpio = devm_gpiod_get_optional(&func->dev, "reset",
						   GPIOD_OUT_LOW);
	if (IS_ERR(sdio->reset_gpio))
		return PTR_ERR(sdio->reset_gpio);
	INIT_WORK(&sdio->tx_work, aic8800_sdio_tx_work);
	INIT_WORK(&sdio->rx_work, aic8800_sdio_rx_work);
	skb_queue_head_init(&sdio->tx_queue);
	sdio_set_drvdata(func, sdio);
	ret = aic8800_sdio_power_on(sdio);
	if (ret)
		goto clear_data;
	ret = aic8800_protocol_init(&sdio->core);
	if (ret)
		goto power_off;
	ret = aic8800_sdio_io_init(func);
	if (ret)
		goto protocol_deinit;
	sdio_claim_host(func);
	ret = sdio_claim_irq(func, aic8800_sdio_irq);
	if (!ret) {
		sdio->irq_claimed = true;
		sdio_writeb(func, 0x07, 0x00, &ret);
	}
	sdio_release_host(func);
	if (ret)
		goto io_deinit;
	if (id->device == AIC_BOOT_DEVICE_ID) {
		ret = aic8800_protocol_boot(&sdio->core);
		if (!ret)
			dev_info(&func->dev, "firmware started; waiting for SDIO re-enumeration\n");
	} else {
		ret = aic8800_protocol_runtime_config(&sdio->core);
		if (!ret)
			ret = aic8800_core_register(&sdio->core);
		if (!ret)
			sdio->core_registered = true;
	}
	if (!ret)
		return 0;
	sdio_claim_host(func);
	sdio_release_irq(func);
	sdio_release_host(func);
	sdio->irq_claimed = false;
io_deinit:
	aic8800_sdio_io_deinit(func);
protocol_deinit:
	aic8800_protocol_deinit(&sdio->core);
power_off:
	aic8800_sdio_power_off(sdio);
clear_data:
	sdio_set_drvdata(func, NULL);
	return ret;
}

static void aic8800_sdio_remove(struct sdio_func *func)
{
	struct aic8800_sdio *sdio = sdio_get_drvdata(func);

	if (!sdio)
		return;
	sdio->stopping = true;
	if (sdio->irq_claimed) {
		sdio_claim_host(func);
		sdio_release_irq(func);
		sdio_release_host(func);
	}
	cancel_work_sync(&sdio->rx_work);
	cancel_work_sync(&sdio->tx_work);
	skb_queue_purge(&sdio->tx_queue);
	if (sdio->core_registered)
		aic8800_core_unregister(&sdio->core);
	aic8800_protocol_deinit(&sdio->core);
	aic8800_sdio_io_deinit(func);
	aic8800_sdio_power_off(sdio);
	sdio_set_drvdata(func, NULL);
}

static const struct sdio_device_id aic8800_sdio_ids[] = {
	{ SDIO_DEVICE(AIC_VENDOR_ID, AIC_BOOT_DEVICE_ID) },
	{ SDIO_DEVICE(AIC_VENDOR_ID, AIC_WIFI_DEVICE_ID) },
	{ }
};
MODULE_DEVICE_TABLE(sdio, aic8800_sdio_ids);

static struct sdio_driver aic8800_sdio_driver = {
	.name = "aic8800_sdio",
	.id_table = aic8800_sdio_ids,
	.probe = aic8800_sdio_probe,
	.remove = aic8800_sdio_remove,
};
module_sdio_driver(aic8800_sdio_driver);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("AIC8800D80 SDIO fullmac transport");
