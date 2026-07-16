# Development workflow

## Edit the correct layer

Generated files carry a generated-file banner. Change structured values under
`generators/data/`, the AIC8800 generator, or its two template-only protocol
sources under `generators/templates/aic8800/`, then regenerate. Hand-written
DTS, dt-bindings, scripts, and patch metadata may be edited directly.

## Required local checks

After generator or data changes:

```bash
python3 scripts/validate-factory.py
python3 scripts/refresh-documentation.py
python3 scripts/refresh-documentation.py --check
```

The factory result is authoritative even when it fails. Fix or explicitly
document failed checks before treating generated output as ready for integration.

## Integration discipline

Use a disposable or reviewable Linux tree for exports and compile checks. The
local `../../kernels/a733-debug/` tree is a separate detached worktree; first
reproduce any useful change in this source repository, then create a patch or
generated output before relying on it.

## Commit and review

Keep generated input and output in the same review. Use Linux subsystem commit
subjects, explain the reason for the change, and run the relevant build or
hardware test before making a success claim.
