#!/usr/bin/env python3
"""
Thermal sensor chip descriptor generator for sun8i_thermal.c

Reads generators/data/thermal-main.json and emits a patched
sun8i_thermal.c with the new chip definitions merged in.

Usage:
    python3 generators/generate_thermal.py \
        --input linux/drivers/thermal/sun8i_thermal.c \
        --output generators/output/sun8i_thermal.c
"""

import argparse
import json
import re
import sys
from pathlib import Path


def generate_calc_temp(chip):
    ct = chip["calc_temp"]
    name = chip["name"]
    prefix = name.upper()

    if ct["type"] == "piecewise":
        return f"""\
#define {prefix}_SENSOR_DATA_CODE\t({ct["threshold_reg"]})
#define {prefix}_OFFSET_BELOW\t({ct["below"]["offset"]})
#define {prefix}_SCALE_BELOW\t({ct["below"]["scale"]})
#define {prefix}_OFFSET_ABOVE\t({ct["above"]["offset"]})
#define {prefix}_SCALE_ABOVE\t({ct["above"]["scale"]})

static int {name}_calc_temp(struct ths_device *tmdev,
\t\t\t       int id, int reg)
{{
\tif (reg > {prefix}_SENSOR_DATA_CODE)
\t\treturn (reg + {prefix}_OFFSET_BELOW) * {prefix}_SCALE_BELOW;
\telse
\t\treturn (reg + {prefix}_OFFSET_ABOVE) * {prefix}_SCALE_ABOVE;
}}
"""
    raise ValueError(f"Unknown calc_temp type: {ct['type']}")


def generate_calibrate(chip):
    cal = chip["calibrate"]
    name = chip["name"]
    prefix = name.upper()

    if cal["type"] == "custom":
        sensor_cases = "\n".join(
            f"\t\tcase {s['id']}:\n\t\t\treg = {s['reg_extract']};\n\t\t\tbreak;"
            for s in cal["sensors"]
        )
        return f"""\
static int {name}_ths_calibrate(struct ths_device *tmdev,
\t\t\t\t u16 *caldata, int callen)
{{
\tstruct device *dev = tmdev->dev;
\tu32 ths_cal[{cal["efuse_words"]}];
\tint i, ft_temp;

\tif (!caldata[0] || callen < {cal["efuse_size"]})
\t\treturn -EINVAL;

\tths_cal[0] = caldata[0] | (caldata[1] << 16);
\tths_cal[1] = caldata[2] | (caldata[3] << 16);
\tths_cal[2] = caldata[4] | (caldata[5] << 16);

\tft_temp = ths_cal[0] & FT_TEMP_MASK;
\tif (!ft_temp)
\t\treturn -EINVAL;

\tfor (i = 0; i < tmdev->chip->sensor_num; i++) {{
\t\tint sensor_reg, sensor_temp, cdata, offset;

\t\tswitch (i) {{
{sensor_cases}
\t\tdefault:
\t\t\tcontinue;
\t\t}}

\t\tsensor_temp = {name}_calc_temp(tmdev, i, sensor_reg);

\t\tcdata = CALIBRATE_DEFAULT -
\t\t\t((sensor_temp - ft_temp * 100) / {cal["scale_divisor"]});
\t\tif (cdata & ~TEMP_CALIB_MASK) {{
\t\t\tdev_warn(dev, \"sensor%d is not calibrated.\\n\", i);
\t\t\tcontinue;
\t\t}}

\t\toffset = (i % 2) * 16;
\t\tregmap_update_bits(tmdev->regmap,
\t\t\t\t   SUN50I_H6_THS_TEMP_CALIB + (i / 2 * 4),
\t\t\t\t   TEMP_CALIB_MASK << offset,
\t\t\t\t   cdata << offset);
\t}}

\treturn 0;
}}
"""
    raise ValueError(f"Unknown calibrate type: {cal['type']}")


def generate_init(chip):
    init = chip["init"]
    name = chip["name"]

    if init["type"] == "h6_style":
        return f"""\
static int {name}_thermal_init(struct ths_device *tmdev)
{{
\tint val;

\tregmap_write(tmdev->regmap, SUN50I_THS_CTRL0,
\t\t     SUN50I_THS_CTRL0_T_ACQ({init["acq"]}) |
\t\t     SUN50I_THS_CTRL0_T_SAMPLE_PER({init["sample_per"]}));
\tregmap_write(tmdev->regmap, SUN50I_H6_THS_MFC,
\t\t     SUN50I_THS_FILTER_EN |
\t\t     SUN50I_THS_FILTER_TYPE({init["filter_type"]}));
\tregmap_write(tmdev->regmap, SUN50I_H6_THS_PC,
\t\t     SUN50I_H6_THS_PC_TEMP_PERIOD({init["pc_period"]}));
\tval = {init["enable_sensors"]};
\tregmap_write(tmdev->regmap, SUN50I_H6_THS_ENABLE, val);
\tval = {init["dic_sensors"]};
\tregmap_write(tmdev->regmap, SUN50I_H6_THS_DIC, val);

\treturn 0;
}}
"""
    raise ValueError(f"Unknown init type: {init['type']}")


def generate_chip_struct(chip):
    name = chip["name"]
    return f"""\
static const struct ths_thermal_chip {name}_ths = {{
\t.sensor_num = {chip["sensor_num"]},
\t.has_bus_clk_reset = {"true" if chip["has_bus_clk_reset"] else "false"},
\t.has_mod_clk = {"true" if chip["has_mod_clk"] else "false"},
\t.ft_deviation = {chip["ft_deviation"]},
\t.temp_data_base = {chip["temp_data_base"]},
\t.calibrate = {name}_ths_calibrate,
\t.init = {name}_thermal_init,
\t.irq_ack = {chip["irq_ack"]},
\t.calc_temp = {name}_calc_temp,
}};
"""


def generate_of_match_entry(chip):
    return f'\t{{ .compatible = "{chip["compatible"]}", .data = &{chip["name"]}_ths }},'


def patch_driver(orig_text, chips):
    text = orig_text

    # 1. Increase MAX_SENSOR_NUM if needed
    max_needed = max(c["sensor_num"] for c in chips)
    current_max = int(re.search(r"#define MAX_SENSOR_NUM\s+(\d+)", text).group(1))
    if max_needed > current_max:
        text = text.replace(
            f"#define MAX_SENSOR_NUM\t{current_max}",
            f"#define MAX_SENSOR_NUM\t{max_needed}",
        )

    # 2. Insert calc_temp functions before the first existing calc_temp
    calc_temp_code = "\n".join(generate_calc_temp(c) for c in chips)
    # Find a good insertion point: before sun8i_ths_calc_temp or sun50i_h5_calc_temp
    match = re.search(r"(static int sun8i_ths_calc_temp\()", text)
    if match:
        pos = match.start()
        text = text[:pos] + calc_temp_code + "\n" + text[pos:]

    # 3. Insert calibrate functions before sun8i_h3_ths_calibrate
    calibrate_code = "\n".join(generate_calibrate(c) for c in chips)
    match = re.search(r"(static int sun8i_h3_ths_calibrate\()", text)
    if match:
        pos = match.start()
        text = text[:pos] + calibrate_code + "\n" + text[pos:]

    # 4. Insert init functions before sun8i_h3_thermal_init
    init_code = "\n".join(generate_init(c) for c in chips)
    match = re.search(r"(static int sun8i_h3_thermal_init\()", text)
    if match:
        pos = match.start()
        text = text[:pos] + init_code + "\n" + text[pos:]

    # 5. Insert chip structs before the first existing chip struct
    chip_code = "\n".join(generate_chip_struct(c) for c in chips)
    match = re.search(r"(static const struct ths_thermal_chip sun8i_a83t_ths =)", text)
    if match:
        pos = match.start()
        text = text[:pos] + chip_code + "\n" + text[pos:]

    # 6. Insert OF match entries before sentinel
    match_code = "\n".join(generate_of_match_entry(c) for c in chips)
    sentinel = re.search(r"(\t\{ /\* sentinel \*/ \},)", text)
    if sentinel:
        pos = sentinel.start()
        text = text[:pos] + match_code + "\n" + text[pos:]

    # 7. Make interrupt optional (only patch once)
    if "platform_get_irq_optional" not in text:
        text = text.replace(
            """\tirq = platform_get_irq(pdev, 0);
\tif (irq < 0)
\t\treturn irq;""",
            """\tirq = platform_get_irq_optional(pdev, 0);
\tif (irq == -ENXIO)
\t\tirq = 0;
\telse if (irq < 0)
\t\treturn irq;""",
        )
        text = text.replace(
            """\tret = devm_request_threaded_irq(dev, irq, NULL,
\t\t\t\t\tsun8i_irq_thread,
\t\t\t\t\tIRQF_ONESHOT, "ths", tmdev);
\tif (ret)
\t\treturn ret;""",
            """\tif (irq) {
\t\tret = devm_request_threaded_irq(dev, irq, NULL,
\t\t\t\t\t\tsun8i_irq_thread,
\t\t\t\t\t\tIRQF_ONESHOT, "ths", tmdev);
\t\tif (ret)
\t\t\treturn ret;
\t}""",
        )

    return text


def main():
    parser = argparse.ArgumentParser(description="Generate thermal driver patches")
    parser.add_argument(
        "--data",
        default="generators/data/thermal-main.json",
        help="Path to thermal chip JSON data",
    )
    parser.add_argument(
        "--input",
        default="../linux/drivers/thermal/sun8i_thermal.c",
        help="Path to original sun8i_thermal.c",
    )
    parser.add_argument(
        "--output",
        default="generators/output/sun8i_thermal.c",
        help="Path to write patched driver",
    )
    args = parser.parse_args()

    data = json.load(open(args.data))
    orig = Path(args.input).read_text()
    patched = patch_driver(orig, data["chips"])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(patched)
    print(f"Patched driver written to {args.output}")


if __name__ == "__main__":
    main()
