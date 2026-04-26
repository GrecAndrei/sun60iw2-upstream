#!/bin/bash

set -euo pipefail

DEVICE="/dev/mmcblk0p1"
MOUNT_POINT="/mnt/sun60i-a733-rootfs"
DTB_NAME="sun60i-a733-orangepi-4-pro.dtb"
IMAGE_PATH=""
DTB_PATH=""
ASSUME_YES=0
MOUNTED_BY_SCRIPT=0

usage() {
    cat <<EOF
Usage: $0 --image <path> --dtb <path> [options]

Options:
  --device <path>        Rootfs partition to update (default: ${DEVICE})
  --mount-point <path>   Temporary mount point (default: ${MOUNT_POINT})
  --dtb-name <name>      Target DTB name under /boot (default: ${DTB_NAME})
  -y, --yes              Skip confirmation prompt
  -h, --help             Show this help

Example:
  $0 \\
    --image /path/to/linux/arch/arm64/boot/Image \\
    --dtb /path/to/linux/arch/arm64/boot/dts/allwinner/${DTB_NAME}
EOF
}

cleanup() {
    if [[ ${MOUNTED_BY_SCRIPT} -eq 1 ]] && findmnt -rn --target "${MOUNT_POINT}" >/dev/null 2>&1; then
        sudo umount "${MOUNT_POINT}" || true
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --device)
            DEVICE="${2:?missing value for --device}"
            shift 2
            ;;
        --mount-point)
            MOUNT_POINT="${2:?missing value for --mount-point}"
            shift 2
            ;;
        --dtb-name)
            DTB_NAME="${2:?missing value for --dtb-name}"
            shift 2
            ;;
        --image)
            IMAGE_PATH="${2:?missing value for --image}"
            shift 2
            ;;
        --dtb)
            DTB_PATH="${2:?missing value for --dtb}"
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
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ -z "${IMAGE_PATH}" || -z "${DTB_PATH}" ]]; then
    usage >&2
    exit 1
fi

if [[ ! -f "${IMAGE_PATH}" ]]; then
    echo "Image not found: ${IMAGE_PATH}" >&2
    exit 1
fi

if [[ ! -f "${DTB_PATH}" ]]; then
    echo "DTB not found: ${DTB_PATH}" >&2
    exit 1
fi

if [[ ! -b "${DEVICE}" ]]; then
    echo "Block device not found: ${DEVICE}" >&2
    exit 1
fi

printf 'Image:  %s\n' "${IMAGE_PATH}"
printf 'DTB:    %s\n' "${DTB_PATH}"
printf 'Device: %s\n' "${DEVICE}"
printf 'Mount:  %s\n' "${MOUNT_POINT}"
printf 'Target boot files:\n'
printf '  /boot/Image\n'
printf '  /boot/%s\n' "${DTB_NAME}"

if [[ ${ASSUME_YES} -ne 1 ]]; then
    read -r -p "Update boot files on ${DEVICE}? [y/N] " reply
    if [[ ! "${reply}" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

trap cleanup EXIT

sudo -v

EXISTING_MOUNT="$(findmnt -rn -S "${DEVICE}" -o TARGET || true)"
if [[ -n "${EXISTING_MOUNT}" ]]; then
    echo "Unmounting existing mount: ${EXISTING_MOUNT}"
    sudo umount "${EXISTING_MOUNT}"
fi

sudo mkdir -p "${MOUNT_POINT}"
sudo mount -o rw "${DEVICE}" "${MOUNT_POINT}"
MOUNTED_BY_SCRIPT=1

if [[ ! -d "${MOUNT_POINT}/boot" ]]; then
    echo "Expected boot directory not found at ${MOUNT_POINT}/boot" >&2
    exit 1
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TARGET_IMAGE="${MOUNT_POINT}/boot/Image"
TARGET_DTB="${MOUNT_POINT}/boot/${DTB_NAME}"

if [[ -f "${TARGET_IMAGE}" ]]; then
    sudo cp -a "${TARGET_IMAGE}" "${TARGET_IMAGE}.old.${TIMESTAMP}"
fi

if [[ -f "${TARGET_DTB}" ]]; then
    sudo cp -a "${TARGET_DTB}" "${TARGET_DTB}.old.${TIMESTAMP}"
fi

sudo install -m 0644 "${IMAGE_PATH}" "${TARGET_IMAGE}"
sudo install -m 0644 "${DTB_PATH}" "${TARGET_DTB}"
sync

echo "Updated boot files:"
sudo ls -lh "${TARGET_IMAGE}" "${TARGET_DTB}"
echo "Backups created with suffix: .old.${TIMESTAMP}"

sudo umount "${MOUNT_POINT}"
MOUNTED_BY_SCRIPT=0
echo "Done."
