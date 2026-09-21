# Upstreaming guide

The source repository is not itself a kernel commit history. There is no
active patch series: `patches/archive/` preserves historical exports and
`patches/wip/` contains isolated drafts. Reproduce and review changes in a
clean Linux tree before producing a new complete series.

Before exporting a series:

1. Regenerate all affected outputs from their source data.
2. Run repository/factory validation and refresh `docs/status.md`.
3. Export from a clean checkout of the exact target release.
4. Apply the complete sequence from first patch to last and build Image, DTBs,
   and modules.
5. Test the exact patchset and record the outcome.
6. Run the Linux tree's `scripts/checkpatch.pl --strict` and obtain current
   maintainers with `scripts/get_maintainer.pl`.
7. Keep experimental AIC8800 driver work separate until it is a coherent,
   independently reviewable series.

Only then create `patches/active/linux-vX.Y/` and update the build guide.
`scripts/apply-patches.sh` remains a refusal guard until such a series exists.
