# A733 CPU thermals and DVFS

Goal: real cpufreq cooling on Orange Pi 4 Pro (little A55 + big A76), not
DT scaffolding alone.

## What is in source

- SoC thermal zones and THS calibration wiring:
  `arch/arm64/boot/dts/allwinner/sun60i-a733.dtsi`
- Conservative OPP tables:
  `arch/arm64/boot/dts/allwinner/sun60i-a733-cpu-opp.dtsi`
- Board supplies and `cpu-supply`:
  `arch/arm64/boot/dts/allwinner/sun60i-a733-orangepi-4-pro.dts`
  (DCDC5 little, DCDC3 big)
- Integration `.config` must have at least:
  `CONFIG_THERMAL`, `CONFIG_THERMAL_OF`, `CONFIG_THERMAL_GOV_STEP_WISE`,
  `CONFIG_CPU_THERMAL`, `CONFIG_SUN8I_THERMAL`, `CONFIG_CPUFREQ_DT`,
  `CONFIG_NVMEM_SUNXI_SID`
- IPA (`THERMAL_GOV_POWER_ALLOCATOR`) needs `ENERGY_MODEL`; this port uses
  **step_wise**. `sustainable-power` in DT is reserved for a later IPA pass.

Voltages are the **maximum non-zero vendor bin** per OPP so DVFS is safe
without A733 speed-bin support in `sun50i-cpufreq-nvmem`. Do not copy the
vendor `allwinner,sun50i-operating-points` multi-bin VF tables into this
tree.

Out of scope for this pass: GPU/NPU cooling devices, fan, DSU/NPU OPP,
vendor idle/skin sensors 5–7.

## Trip policy (vendor-aligned)

| Zone | Sensor | Passive | Critical | Coolers |
|---|---|---|---|---|
| `cpu-l-thermal` | THS 3 | 70 °C / 90 °C, hyst 2 °C | 110 °C | cpu0–5 |
| `cpu-b-thermal` | THS 0 | same | 110 °C | cpu6–7 |
| ddr / npu / gpu | 1 / 2 / 4 | — | 110 °C | none yet |

## Board check after flash

```sh
/root/thermal-check.sh
# or:
# ls /sys/class/thermal/
# cat /sys/devices/system/cpu/cpufreq/policy*/scaling_available_frequencies
# for d in /sys/class/regulator/regulator.*; do
#   n=$(cat "$d/name"); case $n in *dcdc3*|*dcdc5*) echo $n $(cat $d/microvolts);; esac
# done
```

Expect two cpufreq policies, sane zone temperatures, and visible
`axp8191-dcdc3` / `axp8191-dcdc5`. Stress the CPUs and confirm
`scaling_cur_freq` steps down near the 90 °C target trip.

## Risk notes

- Declaring a bad DCDC rail can abort the whole AXP regulator probe (seen
  with DCDC1). CPU rails use existing AXP8191 linear ranges.
- CPU rails are `regulator-always-on` so `regulator_init_complete()` cannot
  drop them when the use count hits zero.
- Undervolt risk is mitigated by max-bin OPP voltages (higher idle power
  than a correct efuse bin).
