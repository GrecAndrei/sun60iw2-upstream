# Code Generators

This directory contains Python scripts that generate repetitive C kernel driver
code from structured JSON data files. This minimizes manual C coding and
reduces the chance of bugs.

## Why Code Generation?

Linux sunxi drivers (pinctrl, clocks, etc.) are 90% data tables and 10% logic.
The data tables are large, repetitive, and error-prone when written by hand.
By defining the hardware in JSON and generating the C, we:

- Eliminate copy-paste errors in 1000+ line files
- Make the hardware description easy to read and verify
- Allow rapid iteration when register maps change
- Keep the actual C glue code small and reviewable

## Generators

### `generate_pinctrl.py`

Reads `data/pinctrl-main.json` and generates the main pinctrl driver.

```bash
python3 generators/generate_pinctrl.py > drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c
```

**What it generates:**
- Pin bank size arrays
- IRQ bank mapping arrays  
- Probe function using `sunxi_pinctrl_dt_table_init()`
- Platform driver registration

**Hand-written parts:**
- JSON data file (human-readable hardware description)
- Generator script itself (only ~80 lines of Python)

### `generate_ccu.py`

Reads `data/ccu-main.json` and generates the Clock Controller Unit driver.

```bash
python3 generators/generate_ccu.py > drivers/clk/sunxi-ng/ccu-sun60i-a733.c
```

**What it generates:**
- PLL definitions (NKMP, NM types)
- Divider clocks (SUNXI_CCU_M_HWS)
- Gate clocks (SUNXI_CCU_GATE_HWS)
- Parent clock hw arrays
- clk_hw_onecell_data table
- Reset definitions
- Probe function

**Hand-written parts:**
- JSON clock definitions (reg offsets, bit positions, parent relationships)
- Generator script (~200 lines of Python)

## Data Files

### `data/pinctrl-main.json`

```json
{
  "banks": {
    "PA": 0, "PB": 11, "PC": 17, ...
  },
  "irq_bank_map": [0, 1, 2, ...],
  "irq_bank_muxes": [0, 14, 14, ...],
  "flags": ["new_reg_layout", "eleven_banks"]
}
```

### `data/ccu-main.json`

```json
{
  "clocks": [
    {
      "name": "pll-periph0",
      "type": "nm",
      "reg": "0x020",
      "id": "PLL_PERI0"
    },
    {
      "name": "uart0",
      "type": "gate",
      "parent": "apb1",
      "reg": "0x000",
      "bit": 1,
      "id": "UART0"
    }
  ],
  "resets": [
    {
      "id": "BUS_UART0",
      "reg": "0x000",
      "bit": 0
    }
  ]
}
```

## Adding New Clocks

To add a new clock:

1. Edit `data/ccu-main.json`
2. Add a new entry to the `clocks` array:
   ```json
   {
     "name": "my-clock",
     "type": "gate",
     "parent": "apb1",
     "reg": "0x100",
     "bit": 5,
     "id": "MY_CLOCK"
   }
   ```
3. Add the corresponding ID to `include/dt-bindings/clock/sun60i-a733-ccu.h`
4. Re-run the generator

## Adding New Resets

Same process as clocks, but add to the `resets` array and update
`include/dt-bindings/reset/sun60i-a733-ccu.h`.

## Future Generators

Planned generators:
- `generate_r_ccu.py` - R-domain CCU
- `generate_rtc_ccu.py` - RTC CCU  
- `generate_cpupll.py` - CPU PLL CCU
- `generate_thermal.py` - Thermal sensor chip descriptor
- `generate_pinmux_data.py` - Pinmux function tables

## Rules

1. **Never edit generated C files manually.** Always edit the JSON data and
   regenerate.
2. **Commit both JSON data and generated C.** This allows building without
   Python, while keeping the source of truth in JSON.
3. **Verify generated code compiles** before committing.
