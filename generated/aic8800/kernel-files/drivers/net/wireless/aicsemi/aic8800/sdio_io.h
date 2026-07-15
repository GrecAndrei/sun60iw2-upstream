/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef AIC8800_SDIO_IO_H
#define AIC8800_SDIO_IO_H
#include <linux/mmc/sdio_func.h>
int aic8800_sdio_io_init(struct sdio_func *func);
void aic8800_sdio_io_deinit(struct sdio_func *func);
int aic8800_sdio_write(struct sdio_func *func, const u8 *data, size_t len);
int aic8800_sdio_read(struct sdio_func *func, u8 **data, size_t *len);
#endif
