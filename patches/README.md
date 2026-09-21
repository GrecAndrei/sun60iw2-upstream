# Patch inventory

There is currently **no reproducible active Linux patch series** in this
repository. The authoritative integration reference is
`../../../kernels/a733-v7.1.3/` on branch `debug/a733-v7.1.3`.

## Layout

- `archive/linux-v7.0/` — historical six-patch Linux v7.0 series. It is kept
  for provenance only; patch 0001 has malformed hunk counts and the sequence
  must not be applied to Linux v7.1.3.
- `wip/` — standalone drafts that have not been proven as a complete series.
  Their presence is not build or boot evidence.

`scripts/apply-patches.sh` is intentionally a guard command while no active
series exists. It lists the inventory and refuses the old implicit
"apply every patch" behavior.

## Creating a future active series

Only add `active/linux-vX.Y/` after all patches have been regenerated from a
clean checkout of that exact release and the complete sequence has passed:

1. `git am` from first patch to last on a clean tree.
2. A733 defconfig, Image, DTB, and module builds.
3. Repository/factory validation.
4. Exact Image/DTB hardware evidence for any runtime claim.

Keep source changes and generated outputs reviewable in this repository even
when a patch export is not yet available.
