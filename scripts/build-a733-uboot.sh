#!/usr/bin/env bash

# Build the patched legacy U-Boot and assemble the A733 SD boot package.
# The script deliberately does not write a block device; use
# flash-a733-uboot.sh only after reviewing the generated manifest.

set -euo pipefail

BOARD="a733"
PARTITION_START_SECTOR=65536
BOOT_PACKAGE_SECTOR=32800
SECTOR_SIZE=512
SOURCE=""
PACK_ROOT=""
TOOLCHAIN=""
OUT=""
JOBS="$(getconf _NPROCESSORS_ONLN 2>/dev/null || printf '1')"

usage() {
	cat <<EOF
Usage: $0 --source <u-boot-tree> --pack-root <pack-uboot-root> \\
          --toolchain <cross-compiler-prefix> --out <empty-directory> [--jobs <n>]

Builds sun60iw2p1_t736_defconfig and creates boot_package.fex for the
Orange Pi 4 Pro / A733.  No block device is written.

Required paths:
  --source      Patched legacy U-Boot tree.
  --pack-root   Orange Pi pack-uboot directory containing tools/ and sun60iw2/bin/.
  --toolchain   ARM cross-prefix ending in arm-linux-gnueabi-.
  --out         Empty output directory to create the package and evidence in.
EOF
}

fail() {
	echo "error: $*" >&2
	exit 1
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--source)
			SOURCE="${2:?missing value for --source}"
			shift 2
			;;
		--pack-root)
			PACK_ROOT="${2:?missing value for --pack-root}"
			shift 2
			;;
		--toolchain)
			TOOLCHAIN="${2:?missing value for --toolchain}"
			shift 2
			;;
		--out)
			OUT="${2:?missing value for --out}"
			shift 2
			;;
		--jobs)
			JOBS="${2:?missing value for --jobs}"
			shift 2
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			fail "unknown argument: $1"
			;;
	esac
done

[[ -n "${SOURCE}" && -n "${PACK_ROOT}" && -n "${TOOLCHAIN}" && -n "${OUT}" ]] || {
	usage >&2
	exit 1
}
[[ "${JOBS}" =~ ^[1-9][0-9]*$ ]] || fail "--jobs must be a positive integer"
[[ -f "${SOURCE}/Makefile" ]] || fail "U-Boot Makefile not found: ${SOURCE}"
[[ -x "${TOOLCHAIN}gcc" ]] || fail "cross compiler not found: ${TOOLCHAIN}gcc"
[[ -x "${PACK_ROOT}/tools/dtc" ]] || fail "pack tool not found: ${PACK_ROOT}/tools/dtc"
[[ -f "${PACK_ROOT}/sun60iw2/bin/boot_package.cfg" ]] || fail "sun60iw2 package inputs not found"

if [[ -e "${OUT}" ]]; then
	[[ -d "${OUT}" ]] || fail "output path exists and is not a directory: ${OUT}"
	[[ -z "$(find "${OUT}" -mindepth 1 -maxdepth 1 -print -quit)" ]] || \
		fail "output directory must be empty: ${OUT}"
else
	mkdir -p "${OUT}"
fi

SOURCE="$(cd "${SOURCE}" && pwd -P)"
PACK_ROOT="$(cd "${PACK_ROOT}" && pwd -P)"
OUT="$(cd "${OUT}" && pwd -P)"
TOOLS="${PACK_ROOT}/tools"
BIN="${PACK_ROOT}/sun60iw2/bin"
BUILD_LOG="${OUT}/build.log"
PACKAGE_LOG="${OUT}/package.log"

BUILD_EPOCH="${SOURCE_DATE_EPOCH:-}"
if [[ -z "${BUILD_EPOCH}" ]]; then
	BUILD_EPOCH="$(git -C "${SOURCE}" log -1 --format=%ct 2>/dev/null)" || \
		fail "set SOURCE_DATE_EPOCH when the U-Boot source is not a Git checkout"
fi
[[ "${BUILD_EPOCH}" =~ ^[0-9]+$ ]] || fail "SOURCE_DATE_EPOCH must be seconds since the Unix epoch"

mkdir -p "${OUT}/vendor-export/default/bin"

printf 'Building U-Boot in %s\n' "${SOURCE}"
pushd "${SOURCE}" >/dev/null
SOURCE_DATE_EPOCH="${BUILD_EPOCH}" make CROSS_COMPILE="${TOOLCHAIN}" \
	sun60iw2p1_t736_defconfig >"${BUILD_LOG}" 2>&1
SOURCE_DATE_EPOCH="${BUILD_EPOCH}" make CROSS_COMPILE="${TOOLCHAIN}" -j"${JOBS}" \
	LICHEE_CHIP_CONFIG_DIR="${OUT}/vendor-export" \
	LICHEE_BUSSINESS=default \
	LICHEE_PLAT_OUT="${OUT}/vendor-export" >>"${BUILD_LOG}" 2>&1
popd >/dev/null

[[ -f "${SOURCE}/u-boot.bin" ]] || fail "build finished without u-boot.bin; see ${BUILD_LOG}"

printf 'Assembling boot package in %s\n' "${OUT}"
cp -a "${BIN}"/. "${OUT}/"
cp "${SOURCE}/u-boot.bin" "${OUT}/u-boot.bin"
cp "${SOURCE}/u-boot.bin" "${OUT}/u-boot.fex"

pushd "${OUT}" >/dev/null
"${TOOLS}/dtc" -p 2048 -W no-unit_address_vs_reg -@ -O dtb \
	-o "${BOARD}-u-boot.dtb" -b 0 dts/u-boot-current.dts >"${PACKAGE_LOG}" 2>&1
sed -i 's/\r$//; s/$/\r/' sys_config/sys_config.fex
cp sys_config/sys_config.fex sys_config.fex
"${TOOLS}/script" sys_config.fex >>"${PACKAGE_LOG}" 2>&1
cp "${BOARD}-u-boot.dtb" sunxi.fex
"${TOOLS}/update_dtb" sunxi.fex 4096 >>"${PACKAGE_LOG}" 2>&1
"${TOOLS}/update_uboot" -no_merge u-boot.fex sys_config.bin >>"${PACKAGE_LOG}" 2>&1
"${TOOLS}/update_uboot" -no_merge u-boot.bin sys_config.bin >>"${PACKAGE_LOG}" 2>&1
sed -i 's/\r$//; s/$/\r/' boot_package.cfg
"${TOOLS}/dragonsecboot" -pack boot_package.cfg >>"${PACKAGE_LOG}" 2>&1
popd >/dev/null

PACKAGE="${OUT}/boot_package.fex"
[[ -f "${PACKAGE}" ]] || fail "packaging finished without boot_package.fex; see ${PACKAGE_LOG}"
PACKAGE_SIZE="$(stat -c %s "${PACKAGE}")"
MAX_PACKAGE_SIZE=$(( (PARTITION_START_SECTOR - BOOT_PACKAGE_SECTOR) * SECTOR_SIZE ))
(( PACKAGE_SIZE % SECTOR_SIZE == 0 )) || fail "boot package is not sector aligned: ${PACKAGE_SIZE} bytes"
(( PACKAGE_SIZE <= MAX_PACKAGE_SIZE )) || fail "boot package exceeds reserved boot window"

sha256sum "${OUT}/u-boot.bin" \
	"${OUT}/boot_package.fex" \
	"${OUT}/boot0_sdcard_a733.fex" \
	"${OUT}/monitor.fex" \
	"${OUT}/scp.fex" >"${OUT}/SHA256SUMS"
{
	printf 'board=Orange Pi 4 Pro (A733)\n'
	printf 'boot0_sdcard_sector=16\n'
	printf 'boot_package_sector=%s\n' "${BOOT_PACKAGE_SECTOR}"
	printf 'partition_start_sector=%s\n' "${PARTITION_START_SECTOR}"
	printf 'boot_package_max_bytes=%s\n' "${MAX_PACKAGE_SIZE}"
	printf 'boot_package_bytes=%s\n' "${PACKAGE_SIZE}"
	printf 'u_boot_source=%s\n' "${SOURCE}"
	printf 'u_boot_revision=%s\n' "$(git -C "${SOURCE}" rev-parse --verify HEAD 2>/dev/null || printf unavailable)"
	printf 'u_boot_dirty=%s\n' "$(git -C "${SOURCE}" status --porcelain 2>/dev/null | wc -l)"
	printf 'source_date_epoch=%s\n' "${BUILD_EPOCH}"
	printf 'cross_compiler=%s\n' "$("${TOOLCHAIN}gcc" -dumpfullversion -dumpversion)"
} >"${OUT}/BUILD-INFO"

printf 'Package: %s (%s bytes)\n' "${PACKAGE}" "${PACKAGE_SIZE}"
printf 'Manifest: %s\n' "${OUT}/BUILD-INFO"
printf 'Checksums: %s\n' "${OUT}/SHA256SUMS"
printf 'Logs: %s, %s\n' "${BUILD_LOG}" "${PACKAGE_LOG}"
