#!/usr/bin/env python3
"""Comprehensive factory validation suite for sun60iw2-upstream generators.

Run this after any generator or data change to verify correctness,
determinism, and compile readiness.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check(report: list, name: str, cond: bool, detail: str = ""):
    report.append({"name": name, "pass": cond, "detail": detail})
    return cond


def run_gen(script: str) -> str:
    parts = script.split()
    result = subprocess.run(
        ["python3"] + parts,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.stdout


def main() -> int:
    checks: list[dict] = []

    # 1. JSON data validity
    for p in [
        "generators/data/ccu-main.json",
        "generators/data/ccu-main-extracted.json",
        "generators/data/pinctrl-main.json",
    ]:
        try:
            json.loads((ROOT / p).read_text())
            check(checks, f"json_valid:{Path(p).name}", True)
        except Exception as e:
            check(checks, f"json_valid:{Path(p).name}", False, str(e))

    # 2. Determinism
    ccu1 = run_gen("generators/generate_ccu.py")
    ccu2 = run_gen("generators/generate_ccu.py")
    check(checks, "ccu_determinism", ccu1 == ccu2, f"len={len(ccu1)}")

    pin1 = run_gen("generators/generate_pinctrl.py --with-pinmux=c")
    pin2 = run_gen("generators/generate_pinctrl.py --with-pinmux=c")
    check(checks, "pinctrl_determinism", pin1 == pin2, f"len={len(pin1)}")

    # 3. Committed files match fresh output
    ccu_committed = (ROOT / "drivers/clk/sunxi-ng/ccu-sun60i-a733.c").read_text()
    pin_committed = (ROOT / "drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c").read_text()
    check(checks, "ccu_committed_fresh_match", ccu_committed == ccu1)
    check(checks, "pinctrl_committed_fresh_match", pin_committed == pin1)

    # 4. Generator Python syntax
    for script in [
        "generate_ccu.py",
        "generate_pinctrl.py",
        "generate_buildsys.py",
        "generate_defconfig.py",
        "generate_bindings.py",
        "report_ccu_pipeline.py",
    ]:
        try:
            compile((ROOT / "generators" / script).read_text(), script, "exec")
            check(checks, f"syntax:{script}", True)
        except SyntaxError as e:
            check(checks, f"syntax:{script}", False, str(e))

    # 5. Extractor plugins syntax
    for plugin in ["clocks.py", "resets.py", "registers.py"]:
        try:
            compile(
                (ROOT / "generators/extractor/plugins" / plugin).read_text(),
                plugin,
                "exec",
            )
            check(checks, f"syntax:extractor/{plugin}", True)
        except SyntaxError as e:
            check(checks, f"syntax:extractor/{plugin}", False, str(e))

    # 6. Metrics sanity
    from generators.generate_ccu import Generator, merge_data, parse_binding_ids
    from generators.plugins import DOMAINS

    primary = json.loads((ROOT / "generators/data/ccu-main.json").read_text())
    extracted = json.loads(
        (ROOT / "generators/data/ccu-main-extracted.json").read_text()
    )
    binding_ids = parse_binding_ids(
        ROOT / "include/dt-bindings/clock/sun60i-a733-ccu.h"
    )
    merged = merge_data(primary, extracted, binding_ids)
    gen = Generator(merged, DOMAINS["main"])
    gen.render()
    check(
        checks,
        "generator_no_unsupported",
        len(gen.unsupported) == 0,
        str(gen.unsupported),
    )
    check(checks, "key_gate_native_all", len(set(gen.key_gate_emitted)) == 35)

    # 7. ID coverage
    merged_ids = {c["id"] for c in merged["clocks"] if "id" in c}
    extracted_clocks = [c for c in merged["clocks"] if c.get("type") != "parent_array"]
    coverage = len(merged_ids) / len(extracted_clocks) if extracted_clocks else 0.0
    check(
        checks,
        "id_coverage>75",
        coverage > 0.75,
        f"{len(merged_ids)}/{len(extracted_clocks)}",
    )

    # 8. Pinctrl structural validation
    from generators.plugins.pinmux_validator import (
        parse_c_driver,
        validate_pinctrl_structure,
        compare_to_mainline,
    )

    pinctrl_json = json.loads((ROOT / "generators/data/pinctrl-main.json").read_text())
    struct_errors = validate_pinctrl_structure(pinctrl_json)
    struct_ok = not any(e["severity"] == "error" for e in struct_errors)
    check(
        checks,
        "pinctrl_structure_valid",
        struct_ok,
        "; ".join(f"{e['name']}:{e['message']}" for e in struct_errors),
    )

    # 9. Pinctrl generated vs mainline comparison
    generated_c = parse_c_driver(
        (ROOT / "drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c").read_text()
    )
    template_c = parse_c_driver(
        (ROOT.parent / "linux/drivers/pinctrl/sunxi/pinctrl-sun55i-a523.c").read_text()
    )
    mainline_devs = compare_to_mainline(generated_c, template_c)
    mainline_ok = not any(d["severity"] == "error" for d in mainline_devs)
    check(
        checks,
        "pinctrl_mainline_pattern_match",
        mainline_ok,
        "; ".join(f"{d['name']}:{d['message']}" for d in mainline_devs),
    )

    # 10. Pinctrl JSON vs generated driver consistency
    json_banks = pinctrl_json.get("banks", {})
    gen_banks = generated_c.get("banks", {})
    banks_match = json_banks == gen_banks
    check(
        checks,
        "pinctrl_json_banks_match",
        banks_match,
        f"json={json_banks} gen={gen_banks}",
    )

    json_map = pinctrl_json.get("irq_bank_map", [])
    gen_map = generated_c.get("irq_bank_map", [])
    map_match = json_map == gen_map
    check(
        checks,
        "pinctrl_json_irq_map_match",
        map_match,
        f"json={json_map} gen={gen_map}",
    )

    json_muxes = pinctrl_json.get("irq_bank_muxes", [])
    gen_muxes = generated_c.get("irq_bank_muxes", [])
    muxes_match = json_muxes == gen_muxes
    check(
        checks,
        "pinctrl_json_irq_muxes_match",
        muxes_match,
        f"json={json_muxes} gen={gen_muxes}",
    )

    # Report
    failures = [c for c in checks if not c["pass"]]
    passed = sum(1 for c in checks if c["pass"])
    total = len(checks)

    report = {
        "status": "PASS" if not failures else "FAIL",
        "passed": passed,
        "failed": len(failures),
        "total": total,
        "checks": checks,
    }

    print(json.dumps(report, indent=2))

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f['name']}: {f.get('detail', '')}")
        return 1

    print(f"\nALL {total} CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
