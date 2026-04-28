# Ethernet PHY Reset Matrix (Orange Pi 4 Pro)

Goal: isolate PHY reset wiring by testing three DTB variants while keeping kernel/Image fixed.

## Built DTB variants

- `sun60i-a733-orangepi-4-pro.pa14-reset.dtb`
  - `reset-gpios = <&pio 0 14 GPIO_ACTIVE_LOW>;`
- `sun60i-a733-orangepi-4-pro.ph16-reset.dtb`
  - `reset-gpios = <&pio 7 16 GPIO_ACTIVE_LOW>;`
- `sun60i-a733-orangepi-4-pro.no-reset.dtb`
  - no `reset-gpios`

Location:

- `/home/grec-alexander/Documents/porting/sun60iw2-upstream/.tmp/`

## Test sequence

Use the same Image for all tests:

- `/home/grec-alexander/Documents/porting/linux/arch/arm64/boot/Image`

For each variant, flash DTB only, boot board, capture logs:

```bash
cd /home/grec-alexander/Documents/porting/sun60iw2-upstream
sudo ./scripts/update-sd-boot.sh \
  --image /home/grec-alexander/Documents/porting/linux/arch/arm64/boot/Image \
  --dtb /home/grec-alexander/Documents/porting/sun60iw2-upstream/.tmp/sun60i-a733-orangepi-4-pro.pa14-reset.dtb \
  -y
```

Repeat by replacing DTB path with:

- `.../sun60i-a733-orangepi-4-pro.ph16-reset.dtb`
- `.../sun60i-a733-orangepi-4-pro.no-reset.dtb`

## Log capture on target

```bash
dmesg | grep -Ei 'gmac|stmmac|mdio|phy|A733DBG'
```

Success criterion:

- at least one `A733DBG MDIO ... VALID` entry or non-`all_ff=32` summary.

Decision:

- If one variant returns valid PHY ID, keep that reset config in board DTS.
- If all three stay `all_ff=32`, reset is not the blocker and next focus is pinmux/function-level mismatch.
