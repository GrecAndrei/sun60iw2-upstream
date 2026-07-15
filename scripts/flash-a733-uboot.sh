#!/usr/bin/env bash

# Back up the complete SD boot reservation and replace only boot_package.fex.
# boot0 and the partition table are deliberately left untouched.

set -euo pipefail

BOOT_PACKAGE_SECTOR=32800
PARTITION_START_SECTOR=65536
SECTOR_SIZE=512
DEVICE=""
PACKAGE=""
BACKUP_DIR=""
ASSUME_YES=0

usage() {
	cat <<EOF
Usage: $0 --device <whole-disk> --package <boot_package.fex> \\
          --backup-dir <directory> [-y|--yes]

The whole 32 MiB reserved boot region is backed up before this script writes
only boot_package.fex at sector ${BOOT_PACKAGE_SECTOR}.  The package is read
back and hash-verified.  A mounted device is rejected.
EOF
}

fail() {
	echo "error: $*" >&2
	exit 1
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--device)
			DEVICE="${2:?missing value for --device}"
			shift 2
			;;
		--package)
			PACKAGE="${2:?missing value for --package}"
			shift 2
			;;
		--backup-dir)
			BACKUP_DIR="${2:?missing value for --backup-dir}"
			shift 2
			;;
		-y|--yes)
			ASSUME_YES=1
			shift
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

[[ -n "${DEVICE}" && -n "${PACKAGE}" && -n "${BACKUP_DIR}" ]] || {
	usage >&2
	exit 1
}
[[ -f "${PACKAGE}" ]] || fail "package not found: ${PACKAGE}"
DEVICE="$(readlink -f "${DEVICE}")"
PACKAGE="$(readlink -f "${PACKAGE}")"
[[ -b "${DEVICE}" ]] || fail "not a block device: ${DEVICE}"
[[ "$(lsblk -dn -o TYPE "${DEVICE}")" == "disk" ]] || \
	fail "device must be a whole disk, not a partition: ${DEVICE}"

mapfile -t MOUNTED_PATHS < <(lsblk -nrpo NAME,MOUNTPOINT "${DEVICE}" | awk 'NF > 1 { print }')
(( ${#MOUNTED_PATHS[@]} == 0 )) || fail "device or child partition is mounted: ${MOUNTED_PATHS[*]}"

PACKAGE_SIZE="$(stat -c %s "${PACKAGE}")"
MAX_PACKAGE_SIZE=$(( (PARTITION_START_SECTOR - BOOT_PACKAGE_SECTOR) * SECTOR_SIZE ))
(( PACKAGE_SIZE > 0 )) || fail "package is empty"
(( PACKAGE_SIZE % SECTOR_SIZE == 0 )) || fail "package is not sector aligned"
(( PACKAGE_SIZE <= MAX_PACKAGE_SIZE )) || fail "package exceeds the reserved boot window"

PACKAGE_HASH="$(sha256sum "${PACKAGE}" | awk '{print $1}')"
mkdir -p "${BACKUP_DIR}"
BACKUP_DIR="$(cd "${BACKUP_DIR}" && pwd -P)"
BACKUP="${BACKUP_DIR}/orangepi4pro-sd-reserved-$(date +%Y%m%d-%H%M%S).img"

printf 'Device: %s\n' "${DEVICE}"
printf 'Package: %s (%s bytes, sha256 %s)\n' "${PACKAGE}" "${PACKAGE_SIZE}" "${PACKAGE_HASH}"
printf 'Backup: %s\n' "${BACKUP}"
printf 'Write: sector %s only; boot0 and partition table are preserved\n' "${BOOT_PACKAGE_SECTOR}"

if (( ASSUME_YES == 0 )); then
	read -r -p "Back up and write this boot package? [y/N] " reply
	[[ "${reply}" =~ ^[Yy]$ ]] || {
		echo "Aborted."
		exit 0
	}
fi

sudo -v
sudo dd if="${DEVICE}" of="${BACKUP}" bs=1M count=32 conv=fsync status=none
sha256sum "${BACKUP}" >"${BACKUP}.sha256"

sudo dd if="${PACKAGE}" of="${DEVICE}" bs="${SECTOR_SIZE}" \
	seek="${BOOT_PACKAGE_SECTOR}" conv=notrunc,fsync status=none
sync

BLOCKS=$(( PACKAGE_SIZE / SECTOR_SIZE ))
READBACK_HASH="$(sudo dd if="${DEVICE}" bs="${SECTOR_SIZE}" skip="${BOOT_PACKAGE_SECTOR}" \
	count="${BLOCKS}" status=none | sha256sum | awk '{print $1}')"
[[ "${READBACK_HASH}" == "${PACKAGE_HASH}" ]] || \
	fail "read-back hash mismatch: expected ${PACKAGE_HASH}, got ${READBACK_HASH}"

printf 'Flash complete and read-back verified. Backup checksum: %s.sha256\n' "${BACKUP}"
