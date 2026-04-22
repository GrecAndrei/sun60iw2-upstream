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
# DT-table mode (default) - uses sunxi_pinctrl_dt_table_init()
python3 generators/generate_pinctrl.py > drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c

# C-array mode - explicit SUNXI_PIN tables with sunxi_pinctrl_init_with_flags()
python3 generators/generate_pinctrl.py --with-pinmux=c > drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c

# DT-node mode - emits pinmux nodes for device tree
python3 generators/generate_pinctrl.py --with-pinmux=dt > output/pinmux-dt.txt
```

**What it generates:**
- Pin bank size arrays (DT mode) or explicit `SUNXI_PIN()` tables (C-array mode)
- IRQ bank mapping arrays
- Probe function using `sunxi_pinctrl_dt_table_init()` (DT) or `sunxi_pinctrl_init_with_flags()` (C-array)
- Platform driver registration
- Pinmux validation via `plugins/pinmux_validator.py`

**Hand-written parts:**
- JSON data file (human-readable hardware description)
- Generator script itself (only ~80 lines of Python)

### `generate_ccu.py`

Unified domain-aware CCU generator. Reads JSON data and generates clock
controller drivers for any domain via `--domain` flag.

```bash
# Generate main CCU
python3 generators/generate_ccu.py --domain main > drivers/clk/sunxi-ng/ccu-sun60i-a733.c

# Generate R-domain, RTC, CPUPLL CCUs
python3 generators/generate_ccu.py --domain r > drivers/clk/sunxi-ng/ccu-sun60i-a733-r.c
python3 generators/generate_ccu.py --domain rtc > drivers/clk/sunxi-ng/ccu-sun60i-a733-rtc.c
python3 generators/generate_ccu.py --domain cpupll > drivers/clk/sunxi-ng/ccu-sun60i-a733-cpupll.c

# Metrics-only mode (no C output)
python3 generators/generate_ccu.py --report --no-output
```

**What it generates:**
- PLL definitions (NKMP, NM types)
- Divider clocks (SUNXI_CCU_M / SUNXI_CCU_M_DATA_WITH_MUX*)
- Gate clocks (SUNXI_CCU_GATE, with explicit key-gate fallback markers)
- Parent clock data arrays (`struct clk_parent_data`)
- clk_hw_onecell_data table
- Reset definitions
- `sunxi_ccu_desc` + probe function (`devm_sunxi_ccu_probe`)

**Hand-written parts:**
- JSON clock definitions (reg offsets, bit positions, parent relationships)
- Generator script logic

### `generate_thermal.py`

Reads `data/thermal-main.json` and patches `sun8i_thermal.c` with new chip
descriptors, calc_temp functions, calibrate functions, init functions, and
OF match entries.

```bash
python3 generators/generate_thermal.py \
    --input ../linux/drivers/thermal/sun8i_thermal.c \
    --output generators/output/sun8i_thermal.c
```

**What it generates:**
- `MAX_SENSOR_NUM` bump (if needed)
- Piecewise-linear `calc_temp` functions
- Custom `calibrate` functions for efuse-based calibration
- `init` functions using H6-style register macros
- `ths_thermal_chip` structs
- OF match table entries
- Optional IRQ support in probe (for chips without dedicated THS interrupt)

**Hand-written parts:**
- JSON chip definitions (sensor count, register bases, calibration layout)
- Generator script logic

### `generate_dma.py`

Reads `data/dma.json` and emits the C struct and OF match entry for
`sun6i-dma.c` patches.

```bash
python3 generators/generate_dma.py > generators/output/dma_patch.c
```

**What it generates:**
- `sun6i_dma_config` struct with burst lengths, address widths, flags
- DT snippet for `sun60i-a733.dtsi`
- UART DMA request line references

### `report_ccu_pipeline.py`

Compares canonical-only coverage vs merged (canonical + extracted) coverage.
This is the ROI gauge for the CCU automation pipeline.

```bash
python3 generators/report_ccu_pipeline.py
```

**Report output includes:**
- Extractable clocks and supported clocks
- ID coverage (canonical + inferred)
- Emitted common/hw coverage
- Key-gate native emission count and unresolved fallback count
- Canonical-vs-merged deltas

## Compile-Gated Workflow (Required)

Metrics alone are not sufficient. Every major generator change must pass a real
kernel compile gate.

1. Regenerate driver:
   ```bash
   python3 generators/generate_ccu.py > drivers/clk/sunxi-ng/ccu-sun60i-a733.c
   ```
2. Run metrics:
   ```bash
   python3 generators/generate_ccu.py --report --no-output
   python3 generators/report_ccu_pipeline.py
   ```
3. Validate in Linux tree (object + directory build):
   ```bash
   make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/clk/sunxi-ng/ccu-sun60i-a733.o
   make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- drivers/clk/sunxi-ng/ W=1
   ```

If compile fails, treat it as a pipeline bug and fix generator/data ordering
before any further feature work.

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

## Plugin Architecture

The generator framework uses a plugin system for domain-specific extraction
and emission:

```
generators/plugins/
├── __init__.py              # Domain configs (main/r/rtc/cpupll)
├── pinmux_extractor.py      # Extract pinmux from vendor C
├── pinmux_emitter.py        # Emit C/DT pinmux tables
└── pinmux_validator.py      # Validate pinmux structure
```

**Adding a new domain:** Edit `plugins/__init__.py` to add the domain config,
then use `generate_ccu.py --domain <name>`.

## Validation

Always run the validation suite after generator changes:

```bash
python3 scripts/validate-factory.py
```

This checks:
- JSON data validity
- Generator determinism (regenerating produces identical output)
- Committed files match fresh output
- Python syntax validation
- Pinctrl structural validation (bank sizes, IRQ maps, pin ranges)
- Mainline pattern matching
- ID coverage metrics

## Rules

1. **Never edit generated C files manually.** Always edit the JSON data and
   regenerate.
2. **Commit both JSON data and generated C.** This allows building without
   Python, while keeping the source of truth in JSON.
3. **Verify generated code compiles** before committing.
