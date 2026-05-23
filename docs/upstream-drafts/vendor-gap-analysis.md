# AIC8800D80 Vendor Gap Analysis

Extracted from `orange-pi-6.6-sun60iw2/bsp/drivers/net/wireless/aic8800/`

## Critical Gaps (will block hardware bringup)

1. **Firmware start is IPC-based, not register write**
   - Vendor sends `DBG_START_APP_REQ` message over SDIO TX FIFO
   - Message format: 16-byte header + 8-byte param (bootaddr + boottype)
   - Header includes CRC8 (polynomial 0x107) for 8800D80
   - We currently do a placeholder `sdio_writesb` to a config register

2. **V3 register set needs full init sequence**
   - Block size must be set to 512 before enabling func1
   - Must write 0x01 to byte-mode-enable reg (0x07) to disable byte mode
   - Must write 0x11 to wakeup reg (0x02) to wake chip
   - Must check sleep reg (0x01) bit 4 to confirm chip ready
   - Must enable func0 CCCR interrupt (write 0x07 to CCCR 0x04)

3. **RX path needs int_status register parsing**
   - Read MISC_INT_STATUS_REG (0x04) first to get data size
   - intstatus encodes block count and byte/block mode
   - Only then read rd_fifo_addr (0x0F)

4. **TX needs flow control**
   - Read flow_ctrl_reg (0x03) before TX to get available buffer count
   - Must not send when buffers < DATA_FLOW_CTRL_THRESH (2)

5. **TX frame format requires 4-byte header**
   - [0-1] LE length, [2] type (0x01), [3] CRC8
   - Padded to 512-byte blocks with 4-byte zero tail

## SDIO ID Info

- Bootloader mode: VID=0xc8a1 PID=0x0182 (BSP driver matches this)
- Normal mode: VID=0xc8a1 PID=0x0082 (production driver matches this)
- Chip re-enumerates from bootloader PID to normal PID after firmware starts

## Key Constants Verified

| Constant | Value | Source |
|----------|-------|--------|
| RAM_FMAC_FW_ADDR | 0x00120000 | aic_bsp_8800d80.c:20 |
| RD_FIFO_ADDR_V3 | 0x0F | aicsdio.h:47 |
| WR_FIFO_ADDR_V3 | 0x10 | aicsdio.h:48 |
| BYTEMODE_LEN_REG_V3 | 0x05 | aicsdio.h:41 |
| FLOW_CTRL_Q1_REG_V3 | 0x03 | aicsdio.h:39 |
| MISC_INT_STATUS_REG_V3 | 0x04 | aicsdio.h:40 |
| INTR_ENABLE_REG_V3 | 0x00 | aicsdio.h:36 |
| INTR_PENDING_REG_V3 | 0x01 | aicsdio.h:37 |
| INTR_TO_DEVICE_REG_V3 | 0x02 | aicsdio.h:38 |
| BYTEMODE_ENABLE_REG_V3 | 0x07 | aicsdio.h:43 |
| BLOCK_SIZE | 512 | aicsdio.h:20 |
