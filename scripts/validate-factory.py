#!/usr/bin/env python3
"""Comprehensive factory validation suite for sun60iw2-upstream generators.

Run this after any generator or data change to verify correctness,
determinism, and compile readiness.
"""

import json
import collections
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESET_DEFINE_RE = re.compile(r"^#define\s+RST_([A-Z0-9_]+)\s+\d+", re.M)


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


def run_ccu_domain(domain: str) -> str:
    return run_gen(f"generators/generate_ccu.py --domain {domain}")


def main() -> int:
    checks: list[dict] = []
    ccu_domains = {
        "main": "drivers/clk/sunxi-ng/ccu-sun60i-a733.c",
        "r": "drivers/clk/sunxi-ng/ccu-sun60i-a733-r.c",
        "rtc": "drivers/clk/sunxi-ng/ccu-sun60i-a733-rtc.c",
        "cpupll": "drivers/clk/sunxi-ng/ccu-sun60i-a733-cpupll.c",
    }

    # 1. JSON data validity
    for p in [
        "generators/data/ccu-main.json",
        "generators/data/ccu-main-extracted.json",
        "generators/data/ccu-r-extracted.json",
        "generators/data/ccu-rtc-extracted.json",
        "generators/data/ccu-cpupll-extracted.json",
        "generators/data/pinctrl-main.json",
    ]:
        try:
            json.loads((ROOT / p).read_text())
            check(checks, f"json_valid:{Path(p).name}", True)
        except Exception as e:
            check(checks, f"json_valid:{Path(p).name}", False, str(e))

    # 2. Determinism
    ccu_outputs = {}
    for domain in ccu_domains:
        out1 = run_ccu_domain(domain)
        out2 = run_ccu_domain(domain)
        ccu_outputs[domain] = out1
        check(
            checks,
            f"ccu_determinism:{domain}",
            out1 == out2,
            f"len={len(out1)}",
        )

    pin1 = run_gen("generators/generate_pinctrl.py --with-pinmux=c")
    pin2 = run_gen("generators/generate_pinctrl.py --with-pinmux=c")
    check(checks, "pinctrl_determinism", pin1 == pin2, f"len={len(pin1)}")

    # 3. Committed files match fresh output
    for domain, path in ccu_domains.items():
        ccu_committed = (ROOT / path).read_text()
        check(
            checks,
            f"ccu_committed_fresh_match:{domain}",
            ccu_committed == ccu_outputs[domain],
        )
    pin_committed = (ROOT / "drivers/pinctrl/sunxi/pinctrl-sun60i-a733.c").read_text()
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
    from generators.generate_ccu import (
        Generator,
        SUPPORTED_TYPES,
        is_helper,
        merge_data,
        parse_binding_ids,
    )
    from generators.plugins import DOMAINS

    for domain, cfg in DOMAINS.items():
        binding_path = cfg.get("binding_path")
        check(
            checks,
            f"binding_path_exists:{domain}",
            bool(binding_path and binding_path.exists()),
            str(binding_path),
        )

    primary = json.loads((ROOT / "generators/data/ccu-main.json").read_text())
    extracted = json.loads((ROOT / "generators/data/ccu-main-extracted.json").read_text())
    binding_ids = parse_binding_ids(ROOT / "include/dt-bindings/clock/sun60i-a733-ccu.h")
    merged = merge_data(primary, extracted, binding_ids)
    for domain, cfg in DOMAINS.items():
        data = merged if domain == "main" else json.loads(cfg["data_file"].read_text())
        gen = Generator(data, cfg)
        gen.render()
        check(
            checks,
            f"generator_no_unsupported:{domain}",
            len(gen.unsupported) == 0,
            str(gen.unsupported),
        )
        if cfg.get("has_resets"):
            reset_path = ROOT / "include" / "dt-bindings" / "reset" / cfg["binding_header"]
            reset_ids = {
                m.group(1) for m in RESET_DEFINE_RE.finditer(reset_path.read_text())
            }
            reset_data_ids = {item["id"] for item in data.get("resets", []) if item.get("id")}
            check(
                checks,
                f"reset_binding_coverage:{domain}",
                reset_data_ids == reset_ids,
                f"missing={sorted(reset_ids - reset_data_ids)} extra={sorted(reset_data_ids - reset_ids)}",
            )
        if domain == "main":
            check(checks, "key_gate_native_all", len(set(gen.key_gate_emitted)) == 35)

    # 7. RTC bootstrap dependency safety
    rtc_data = json.loads((ROOT / "generators/data/ccu-rtc-extracted.json").read_text())
    r_data = json.loads((ROOT / "generators/data/ccu-r-extracted.json").read_text())
    r_clock_names = {
        c["name"] for c in r_data["clocks"] if c.get("type") != "parent_array"
    }
    rtc_r_deps = []
    for clock in rtc_data["clocks"]:
        if clock.get("type") == "parent_array":
            continue
        parents = []
        if "parent" in clock:
            parents.append(clock["parent"])
        parents.extend(clock.get("parents", []))
        bad = sorted({p for p in parents if p in r_clock_names})
        if bad:
            rtc_r_deps.append(f"{clock['name']}<-{','.join(bad)}")
    check(
        checks,
        "rtc_bootstrap_has_no_r_ccu_parents",
        not rtc_r_deps,
        "; ".join(rtc_r_deps),
    )

    # 8. DTS fixed-clock names must not collide with generated provider names
    dtsi_text = (
        ROOT / "arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi"
    ).read_text()
    fixed_clock_names = set(
        re.findall(r'clock-output-names = "([^"]+)";', dtsi_text)
    )
    generated_clock_names = set()
    domain_data = {
        "main": merged,
        "r": json.loads((ROOT / "generators/data/ccu-r-extracted.json").read_text()),
        "rtc": rtc_data,
        "cpupll": json.loads(
            (ROOT / "generators/data/ccu-cpupll-extracted.json").read_text()
        ),
    }
    for data in domain_data.values():
        for clock in data["clocks"]:
            if clock.get("type") != "parent_array":
                generated_clock_names.add(clock["name"])
    fixed_clock_collisions = sorted(fixed_clock_names & generated_clock_names)
    check(
        checks,
        "dtsi_fixed_clock_names_do_not_collide_with_generated_clocks",
        not fixed_clock_collisions,
        ", ".join(fixed_clock_collisions),
    )

    main_fw_names = set(re.findall(r'\.fw_name = "([^"]+)"', ccu_outputs["main"]))
    main_external_fw_names = sorted(
        main_fw_names & {"hosc", "osc32k", "iosc", "rtc32k", "sys24M", "dcxo"}
    )
    ccu_node_match = re.search(
        r"ccu: clock-controller@2002000 \{.*?clock-names = (?P<clock_names>[^;]+);",
        dtsi_text,
        re.S,
    )
    ccu_node_clock_names = (
        set(re.findall(r'"([^"]+)"', ccu_node_match.group("clock_names")))
        if ccu_node_match
        else set()
    )
    missing_main_ccu_inputs = sorted(
        set(main_external_fw_names) - ccu_node_clock_names
    )
    check(
        checks,
        "main_ccu_external_fw_names_are_provided_in_dtsi",
        not missing_main_ccu_inputs,
        ", ".join(missing_main_ccu_inputs),
    )

    main_clock_names = {
        c["name"]
        for c in merged["clocks"]
        if c.get("type") != "parent_array" and not is_helper(c.get("name", ""))
    }
    main_external_inputs = {"hosc", "osc32k", "iosc", "rtc32k", "sys24M", "dcxo"}
    unresolved_main_parents = []
    for clock in merged["clocks"]:
        if clock.get("type") == "parent_array" or is_helper(clock.get("name", "")):
            continue
        parents = []
        if "parent" in clock:
            parents.append(clock["parent"])
        parents.extend(clock.get("parents", []))
        bad = sorted(
            {
                parent
                for parent in parents
                if parent not in main_clock_names and parent not in main_external_inputs
            }
        )
        if bad:
            unresolved_main_parents.append(f"{clock['name']}<-{','.join(bad)}")
    check(
        checks,
        "main_clock_parent_names_resolve",
        not unresolved_main_parents,
        "; ".join(unresolved_main_parents),
    )

    internal_fw_name_missing_fallback = []
    for line in ccu_outputs["main"].splitlines():
        match = re.search(r'\.fw_name = "([^"]+)"', line)
        if not match:
            continue
        parent = match.group(1)
        if parent in main_clock_names and parent not in main_external_inputs:
            if f'.name = "{parent}"' not in line:
                internal_fw_name_missing_fallback.append(parent)
    check(
        checks,
        "main_internal_fw_name_parents_have_name_fallback",
        not internal_fw_name_missing_fallback,
        ", ".join(sorted(set(internal_fw_name_missing_fallback))),
    )

    mux_parent_overflow = []
    for clock in merged["clocks"]:
        if clock.get("type") == "parent_array" or is_helper(clock.get("name", "")):
            continue
        mux_width = clock.get("mux_width")
        parents = clock.get("parents", [])
        if mux_width is None or not parents:
            continue
        max_parents = 1 << int(mux_width)
        if len(parents) > max_parents:
            mux_parent_overflow.append(
                f"{clock['name']}:{len(parents)}>{max_parents}"
            )
    check(
        checks,
        "main_mux_parent_counts_fit_mux_width",
        not mux_parent_overflow,
        "; ".join(mux_parent_overflow),
    )

    # 9. ID coverage
    merged_ids = {c["id"] for c in merged["clocks"] if "id" in c}
    extracted_clocks = [c for c in merged["clocks"] if c.get("type") != "parent_array"]
    coverage = len(merged_ids) / len(extracted_clocks) if extracted_clocks else 0.0
    check(
        checks,
        "id_coverage>75",
        coverage > 0.75,
        f"{len(merged_ids)}/{len(extracted_clocks)}",
    )

    merged_id_names = collections.defaultdict(list)
    for clock in merged["clocks"]:
        if clock.get("type") != "parent_array" and clock.get("id"):
            merged_id_names[clock["id"]].append(clock["name"])
    duplicate_ids = sorted(
        f"{clk_id}<-{','.join(names)}"
        for clk_id, names in merged_id_names.items()
        if len(names) > 1
    )
    check(
        checks,
        "main_clock_ids_are_unique",
        not duplicate_ids,
        "; ".join(duplicate_ids),
    )

    # 9b. Main CCU exports must cover supported IDs and DTS consumers
    fresh_main_ids = set(re.findall(r"\[CLK_([A-Z0-9_]+)\]", ccu_outputs["main"]))
    main_supported_ids = sorted(
        {
            c["id"]
            for c in merged["clocks"]
            if c.get("id")
            and c.get("type") in SUPPORTED_TYPES
            and not is_helper(c.get("name", ""))
        }
    )
    main_missing_supported = sorted(set(main_supported_ids) - fresh_main_ids)
    check(
        checks,
        "main_supported_clock_ids_are_exported",
        not main_missing_supported,
        ", ".join(main_missing_supported),
    )

    dts_consumed_main_ids = set()
    for path in (ROOT / "arch/arm64/boot/dts/allwinner").glob("sun60i-a733*.dts*"):
        dts_consumed_main_ids.update(
            re.findall(r"&ccu\s+CLK_([A-Z0-9_]+)", path.read_text())
        )
    missing_dts_ids = sorted(dts_consumed_main_ids - fresh_main_ids)
    check(
        checks,
        "main_dts_consumed_clock_ids_are_exported",
        not missing_dts_ids,
        ", ".join(missing_dts_ids),
    )

    # 10. Pinctrl structural validation
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

    # 11. Pinctrl generated vs mainline comparison
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

    # 12. Pinctrl JSON vs generated driver consistency
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
