# Upstreaming guide

The source repository is not itself a kernel commit history. The standalone
boot baseline is kept as Git-format patches under `patches/`; reproduce and
review changes in a Linux tree before producing a new series.

Before exporting a series:

1. Regenerate all affected outputs from their source data.
2. Run factory validation and refresh `docs/status.md`.
3. Test the exact patchset and record the outcome.
4. Run the Linux tree's `scripts/checkpatch.pl --strict` and obtain current
   maintainers with `scripts/get_maintainer.pl`.
5. Keep experimental AIC8800 skeleton work separate until it is a coherent,
   independently reviewable series.

`scripts/apply-patches.sh` is a local integration helper, not an upstream
submission mechanism. It skips non-Git-format files and installs the defconfigs
after applying the boot-baseline patch files.
