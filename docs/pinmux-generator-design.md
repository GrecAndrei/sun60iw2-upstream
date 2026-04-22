# Pinmux Function Table Generator Design

## Summary

This document designs a generator that produces pinmux function tables from
structured JSON data.  It covers the schema, generator architecture, mapping to
mainline sunxi patterns, and a minimal prototype.

## Background & Problem

The existing `generate_pinctrl.py` only emits **bank sizes, IRQ maps and probe
glue**.  It does **not** capture *which functions each pin supports*.  In
mainline sunxi pinctrl there are two ways to express this:

1. **Explicit C arrays** (e.g. `pinctrl-sun50i-h616.c`) – huge hand-written
   `SUNXI_PIN()` tables.
2. **DT-driven tables** (e.g. `pinctrl-sun55i-a523.c`, `pinctrl-sun60i-a733.c`)
   – `sunxi_pinctrl_dt_table_init()` builds the tables at runtime from Device
   Tree child nodes that contain `pins`, `function` and `allwinner,pinmux`.

For sun60i-a733 mainline currently uses approach #2, but the pinmux data still
has to come from *somewhere* (today: manual DT editing).  A structured JSON
source lets us **generate both** the legacy C arrays *and* the DT pinctrl
nodes, while keeping a single source of truth.

## JSON Schema

### File: `generators/data/pinmux-functions.json`

```json
{
  "_comment": "Pinmux function descriptions for sun60i-a733",
  "soc": "sun60i-a733",
  "banks": {
    "PA": 0,
    "PB": 11,
    "PC": 17,
    "PD": 22,
    "PE": 11,
    "PF": 6,
    "PG": 6,
    "PH": 0,
    "PI": 0,
    "PJ": 28,
    "PK": 26
  },
  "irq": {
    "bank_mux": [0, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14],
    "bank_map": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  },
  "name_map": {
    "twi": "i2c",
    "sdc": "mmc",
    "spif": "spi",
    "ndfc": "nand",
    "dpss": "lcd0"
  },
  "pins": [
    {
      "bank": "PB",
      "pin": 0,
      "functions": [
        {"mux": 2, "name": "uart2",    "signal": "TX"},
        {"mux": 3, "name": "uart0",    "signal": "TX"},
        {"mux": 4, "name": "spi2",     "signal": "CLK"},
        {"mux": 5, "name": "dsi",      "signal": "D0"},
        {"mux": 6, "name": "lcd0",     "signal": "D0"},
        {"mux": 7, "name": "jtag",     "signal": "TMS"}
      ]
    },
    {
      "bank": "PB",
      "pin": 1,
      "functions": [
        {"mux": 2, "name": "uart2",    "signal": "RX"},
        {"mux": 3, "name": "uart0",    "signal": "RX"},
        {"mux": 4, "name": "spi2",     "signal": "MOSI"},
        {"mux": 6, "name": "lcd0",     "signal": "D1"},
        {"mux": 7, "name": "jtag",     "signal": "TDI"}
      ]
    },
    {
      "bank": "PC",
      "pin": 0,
      "functions": [
        {"mux": 2, "name": "nand",     "signal": "WE"},
        {"mux": 3, "name": "mmc2",     "signal": "DS"},
        {"mux": 4, "name": "mmc3",     "signal": "DS"}
      ]
    }
  ]
}
```

### Schema Fields

| Key           | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| `soc`         | string | SoC identifier (used in generated names)             |
| `banks`       | object | Bank → number-of-pins map (same as pinctrl-main.json)|
| `irq`         | object | `bank_mux` and `bank_map` arrays                     |
| `name_map`    | object | Vendor→mainline name substitutions (optional)        |
| `pins`        | array  | One entry per *populated* pin (holes omitted)        |
| `pins[].bank` | string | Bank letter (`PA`..`PK`)                             |
| `pins[].pin`  | int    | Pin number within the bank                           |
| `pins[].functions` | array | Non-GPIO, non-IRQ functions                         |
| `functions[].mux`  | int   | Multiplexer value (hex in C, decimal in JSON)       |
| `functions[].name` | string| Mainline function name (`uart0`, `i2c1`, `mmc2`…)   |
| `functions[].signal`| string| Human-readable signal label (optional, for docs)    |

### Design Decisions

1. **gpio_in / gpio_out are implicit** – every pin always gets
   `SUNXI_FUNCTION(0x0, "gpio_in")` and `SUNXI_FUNCTION(0x1, "gpio_out")`.
   They are *not* repeated in JSON.

2. **IRQ is implicit** – generated from `irq.bank_mux` and `irq.bank_map`.
   No need to list `SUNXI_FUNCTION_IRQ_BANK()` per pin in JSON.

3. **Holes are omitted** – pins that do not exist on a package are simply
   absent from the `pins` array.  The generator inserts `/* Hole */` comments
   when producing C arrays.

4. **`name_map` decouples vendor names from mainline names** – vendor BSP uses
   `twi0`, `sdc2`, `spif`, etc.  Mainline uses `i2c0`, `mmc2`, `spi`.
   A lookup table keeps the JSON clean and makes upstreaming reviews easier.

## Generator Architecture

### Target Outputs

The generator (`generate_pinmux.py`) reads `pinmux-functions.json` and can
emit **three** artifacts:

| Mode | Flag | Purpose |
|------|------|---------|
| `c_array` | `--mode=c` | Explicit `sunxi_desc_pin[]` array (h616-style) |
| `dt_nodes`| `--mode=dt` | Device-Tree `*-pins` nodes for DT-table drivers |
| `report`  | `--mode=report` | Human-readable markdown table for docs/review |

### Generator Flow

```
JSON Load ──► Normalize ──► Name Map ──► Sort by (bank, pin)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         C Emitter      DT Emitter      Report Emitter
```

#### 1. Normalise
- Expand `banks` dict into ordered list.
- Validate that every `pins[]` entry has `bank` / `pin` inside the declared
  bank size.
- Apply `name_map` substitutions.
- Sort by bank index then pin number.

#### 2. C Array Emitter (`--mode=c`)

Iterates bank-by-bank, pin-by-pin.

```c
static const struct sunxi_desc_pin a733_pins[] = {
    /* Bank B */
    SUNXI_PIN(SUNXI_PINCTRL_PIN(B, 0),
          SUNXI_FUNCTION(0x0, "gpio_in"),
          SUNXI_FUNCTION(0x1, "gpio_out"),
          SUNXI_FUNCTION(0x2, "uart2"),		/* TX */
          SUNXI_FUNCTION(0x3, "uart0"),		/* TX */
          SUNXI_FUNCTION(0x4, "spi2"),		/* CLK */
          SUNXI_FUNCTION(0x5, "dsi"),		/* D0 */
          SUNXI_FUNCTION(0x6, "lcd0"),		/* D0 */
          SUNXI_FUNCTION(0x7, "jtag"),		/* TMS */
          SUNXI_FUNCTION_IRQ_BANK(0xe, 0, 0)),	/* PB_EINT0 */
    SUNXI_PIN(SUNXI_PINCTRL_PIN(B, 1),
          ...
    /* Hole */
    SUNXI_PIN(SUNXI_PINCTRL_PIN(C, 0),
          ...
};
```

Notes:
- `SUNXI_FUNCTION_IRQ_BANK` uses the `irq.bank_mux` value (e.g. `0xe`) and the
  remapped bank index from `irq.bank_map`.
- Comments preserve the `signal` field so readers know which UART TX/RX or
  SPI signal is meant.

#### 3. DT Node Emitter (`--mode=dt`)

Produces nodes compatible with `sunxi_pinctrl_dt_table_init()`:

```dts
uart0_pb_pins: uart0-pb-pins {
    pins = "PB0", "PB1";
    function = "uart0";
    allwinner,pinmux = <3>;
};

spi2_pb_pins: spi2-pb-pins {
    pins = "PB0", "PB1", "PB2";
    function = "spi2";
    allwinner,pinmux = <4>;
};
```

The emitter groups pins by **(function, mux)** tuple so that a single DT node
can cover multiple pins when they share the same mux value.

#### 4. Report Emitter (`--mode=report`)

Markdown table for documentation and review:

| Pin | gpio_in | gpio_out | uart0 | uart2 | spi2 | … |
|-----|---------|----------|-------|-------|------|---|
| PB0 | 0x0     | 0x1      | 0x3   | 0x2   | 0x4  | … |
| PB1 | 0x0     | 0x1      | 0x3   | 0x2   | —    | … |

## Comparison to Mainline `sun55i-a523` Pattern

| Aspect | `sun55i-a523` (current) | Proposed Generator |
|--------|------------------------|--------------------|
| Pinmux source | Device Tree only | JSON (single source of truth) |
| C arrays | None (DT-table init) | Optional `--mode=c` output |
| Validation | Manual DT review | Automated report + JSON schema validation |
| Naming | Hand-written in DT | Centralised `name_map` |
| Upstreaming effort | High (lots of DT hand-work) | Medium (generate + review) |

The generator **does not replace** the DT-table approach for sun60i-a733;
rather it **feeds** it.  The JSON becomes the canonical description from which
both C arrays *and* DT nodes can be derived.

## Feasibility & Prototype

A minimal prototype is **low effort** (~2–3 hours):

1. JSON schema is flat; no complex nesting.
2. C output is purely textual macro expansion.
3. DT output is simple grouping by `(function, mux)`.

### Prototype Files

- `generators/data/pinmux-example.json` – subset of PB0..PB2, PC0..PC2
- `generators/generate_pinmux.py` – reads JSON, prints `--mode=c` / `--mode=dt`

See the prototype outputs below.

## Estimated Effort & Blockers

### Full Implementation (~1–2 days)

- [ ] Parse full vendor BSP `pinctrl-sun60iw2.c` into JSON (can reuse SSEE
      extractor framework).
- [ ] Add `name_map` for every vendor→mainline naming difference.
- [ ] Implement `--mode=c`, `--mode=dt`, `--mode=report` emitters.
- [ ] Add JSON schema validation (e.g. `jsonschema` or hand-rolled checks).
- [ ] Integrate with `generate_pinctrl.py` so that a single invocation can
      produce the complete driver when `--with-pinmux` is requested.

### Blockers

| Blocker | Severity | Mitigation |
|---------|----------|------------|
| Vendor BSP has **duplicate mux values** for different signals on the same pin (e.g. `PB7` has two `0x2` entries: `owa_do` and `//owa_mclk`). | Medium | Keep only the active one; comment-out or drop the duplicate. Document in JSON with `"status": "deprecated"`. |
| Vendor names (`twi`, `sdc`) differ from mainline (`i2c`, `mmc`). | Low | `name_map` layer handles this automatically. |
| Vendor uses `0xe` for IRQ, mainline explicit drivers use `0x6`. | Low | `irq.bank_mux` array already encodes this; generator uses whatever is in JSON. |
| Large pin count (~200+ pins) makes manual JSON authoring impractical. | Medium | Must automate extraction from vendor BSP using SSEE. This is a **separate** tool; the generator assumes JSON already exists. |
| sun60i-a733 mainline driver uses DT-table init, so explicit C arrays are **not required** for this SoC. | Low | The generator is reusable for other SoCs (e.g. if we back-port sun60i-a733 to an older kernel, or support sun55iw6, etc.). |

## Conclusion

The proposed JSON schema is simple, upstreamable, and decouples the *semantic*
pinmux description from the *presentation* (C array vs DT nodes).  A minimal
prototype is feasible immediately; full automation depends on completing the
SSEE-based vendor→JSON extractor.

---

*Generated as part of the sun60iw2-upstream porting project.*
