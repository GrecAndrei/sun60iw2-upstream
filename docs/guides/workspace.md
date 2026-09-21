# Workspace and repository boundaries

The A733 effort is a workspace containing several repositories and large local
outputs. Directory placement communicates authority; do not treat neighboring
trees as interchangeable copies.

## Authority order

1. `projects/sun60iw2-upstream/` — reviewable source, generators, maintained
   documentation, and generated outputs.
2. `kernels/a733-v7.1.3/` — current integration build. It proves what is
   integrated on its branch, not what has been upstreamed.
3. `artifacts/` — local binaries, logs, root filesystems, backups, and test
   material. An artifact is evidence only when its revision/checksum and test
   record are known. The hashed, proven-working vendor-image extraction under
   `artifacts/re/vendor-iso-extract/` is primary evidence of shipped behavior.
4. `references/` — secondary vendor/BSP source comparison only. Source may not
   match the image or board and cannot override DTB, binary, or runtime
   evidence. Never copy vendor implementation or APIs into the source project.
5. `archive/` and `docs/archive/` — superseded context; never current guidance.

`kernels/a733-debug/` and `kernels/mainline-v7/` contain preserved experimental
changes. Reproduce useful work in the source project rather than copying a
working tree wholesale. See [`reverse-engineering.md`](reverse-engineering.md)
for the hardware-evidence hierarchy.

## Repository-owned paths

- `arch/`, `drivers/`, `include/`, `configs/` — kernel-facing source.
- `generators/data/` and `generators/templates/` — authoritative inputs for
  generated files.
- `generated/` and generated files under `drivers/` — tracked review output.
- `patches/archive/` and `patches/wip/` — non-active patch material. There is
  currently no reproducible active patch series.
- `scripts/` — validation, export, deployment, and board-operation helpers;
  see [`../../scripts/README.md`](../../scripts/README.md) before using commands
  that mount media, write raw sectors, or reboot hardware.
- `.tmp/` — ignored local validation output only.

## Local-output policy

Keep builds, root filesystems, firmware copies, UART logs, and temporary staged
boot trees under workspace `artifacts/`, not in the source repository. Do not
silently delete unknown artifacts: move stale but potentially useful material
under a dated `artifacts/experiments/` directory and document its provenance.

Git-linked worktrees must be moved with `git worktree move`, never plain `mv`.
Reference repositories should remain read-only except for their own explicitly
reviewed maintenance branches.
