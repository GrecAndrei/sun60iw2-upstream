#!/usr/bin/env bash
# Patch-series guard: there is no validated active Linux series at present.

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
	cat <<EOF
Usage: $0 --list
       $0 --help

No active patch series is currently available. The historical Linux v7.0
artifacts are deliberately separated under patches/archive/, and standalone
drafts live under patches/wip/.

Use the integrated Linux v7.1.3 reference instead:
  $ROOT_DIR/../../kernels/a733-v7.1.3
EOF
}

case "${1:-}" in
--list)
	printf '%s\n' 'Patch inventory:'
	find "$ROOT_DIR/patches" -mindepth 1 -maxdepth 4 -type f \
		\( -name '*.patch' -o -name 'README.md' \) \
		-printf '  %P\n' | sort
	;;
--help|-h)
	usage
	;;
*)
	usage >&2
	cat >&2 <<'EOF'

Refusing to apply patches: the former implicit series was historical,
malformed, and not rebased to the current Linux baseline. See patches/README.md.
EOF
	exit 2
	;;
esac
