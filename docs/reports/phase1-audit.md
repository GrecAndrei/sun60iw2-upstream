# Phase 1 Audit Report (SSEE)

- Repo: `/home/runner/work/sun60iw2-upstream/sun60iw2-upstream`
- Checks passed: **8/8**
- Extracted clocks from CCU driver: **3**
- Extracted resets from CCU driver: **1**
- Clock IDs from dt-bindings: **319**
- Reset IDs from dt-bindings: **120**
- Extracted DTSI nodes: **28**
- Extracted board DTS nodes: **1**

## Bringup Checklist
- [x] Base DTSI exists
- [x] Board DTS exists
- [x] CCU driver exists
- [x] Board enables uart0 (`&uart0 { status = "okay"; }`)
- [x] Board defines serial stdout-path
- [x] SoC DTSI has CCU node
- [x] SoC DTSI has main pinctrl node
- [x] SoC DTSI has uart0 node

## Extraction Validation
- CCU clock extraction errors: 1
- CCU reset extraction errors: 0
- Clock bindings extraction errors: 0
- Reset bindings extraction errors: 0
- DTSI extraction errors: 0
- Board DTS extraction errors: 0
