#!/bin/bash

set -euo pipefail

DEVICE="/dev/mmcblk0p1"
MOUNT_POINT="/mnt/sun60i-a733-rootfs"
DTB_NAME="sun60i-a733-orangepi-4-pro.dtb"
IMAGE_PATH=""
DTB_PATH=""
MODULE_PATHS=()
KERNEL_RELEASE=""
ASSUME_YES=0
INSTALL_BUSYBOX_MODUTILS=0
MOUNTED_BY_SCRIPT=0
BUSYBOX_MODUTILS=(insmod rmmod lsmod modprobe depmod)

usage() {
    cat <<EOF
Usage: $0 --image <path> --dtb <path> [options]

Options:
  --device <path>        Rootfs partition to update (default: ${DEVICE})
  --mount-point <path>   Temporary mount point (default: ${MOUNT_POINT})
  --dtb-name <name>      Target DTB name under /boot (default: ${DTB_NAME})
  --module <path>        Kernel module to install (repeatable; requires --kernel-release)
  --kernel-release <rel> Target /lib/modules release for --module files
  --busybox-modutils     Link available BusyBox module applets under /sbin
  -y, --yes              Skip confirmation prompt
  -h, --help             Show this help

Example:
  $0 \\
    --image /path/to/linux/arch/arm64/boot/Image \\
    --dtb /path/to/linux/arch/arm64/boot/dts/allwinner/${DTB_NAME} \\
    --module /path/to/aic8800_core.ko \\
    --module /path/to/aic8800_sdio.ko \\
    --kernel-release 7.1.3-a733
EOF
}

cleanup() {
    if [[ ${MOUNTED_BY_SCRIPT} -eq 1 ]] && findmnt -rn --target "${MOUNT_POINT}" >/dev/null 2>&1; then
        sudo umount "${MOUNT_POINT}" || true
    fi
}

verify_checksum() {
    local label="$1"
    local expected="$2"
    local target="$3"
    local actual

    actual="$(sudo sha256sum "${target}" | awk '{print $1}')"
    if [[ "${actual}" != "${expected}" ]]; then
        echo "Verification failed for ${label}: ${target}" >&2
        echo "  expected: ${expected}" >&2
        echo "  actual:   ${actual}" >&2
        return 1
    fi

    printf 'Verified %s: %s\n' "${label}" "${actual}"
}

validate_busybox_modutils() {
    local applet

    BUSYBOX_PATH="${MOUNT_POINT}/bin/busybox"
    if [[ ! -f "${BUSYBOX_PATH}" ]]; then
        echo "BusyBox not found: ${BUSYBOX_PATH}" >&2
        return 1
    fi

    for applet in "${BUSYBOX_MODUTILS[@]}"; do
        if ! strings "${BUSYBOX_PATH}" | grep -Fx "${applet}" >/dev/null; then
            echo "BusyBox does not provide required applet: ${applet}" >&2
            return 1
        fi
    done
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
        --module)
            MODULE_PATHS+=("${2:?missing value for --module}")
            shift 2
            ;;
        --kernel-release)
            KERNEL_RELEASE="${2:?missing value for --kernel-release}"
            shift 2
            ;;
        --busybox-modutils)
            INSTALL_BUSYBOX_MODUTILS=1
            shift
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

if (( ${#MODULE_PATHS[@]} > 0 )); then
    if [[ -z "${KERNEL_RELEASE}" ]]; then
        echo "--kernel-release is required when installing modules" >&2
        exit 1
    fi
    if [[ ! "${KERNEL_RELEASE}" =~ ^[A-Za-z0-9._+-]+$ ]]; then
        echo "Invalid kernel release: ${KERNEL_RELEASE}" >&2
        exit 1
    fi
    for module_path in "${MODULE_PATHS[@]}"; do
        if [[ ! -f "${module_path}" || "${module_path}" != *.ko ]]; then
            echo "Module not found or not a .ko file: ${module_path}" >&2
            exit 1
        fi
    done
fi

if [[ ${INSTALL_BUSYBOX_MODUTILS} -eq 1 ]] && (( ${#MODULE_PATHS[@]} == 0 )); then
    echo "--busybox-modutils requires at least one --module" >&2
    exit 1
fi

if [[ ! -b "${DEVICE}" ]]; then
    echo "Block device not found: ${DEVICE}" >&2
    exit 1
fi

IMAGE_SHA256="$(sha256sum "${IMAGE_PATH}" | awk '{print $1}')"
DTB_SHA256="$(sha256sum "${DTB_PATH}" | awk '{print $1}')"

printf 'Image:  %s\n' "${IMAGE_PATH}"
printf 'DTB:    %s\n' "${DTB_PATH}"
printf 'Device: %s\n' "${DEVICE}"
printf 'Mount:  %s\n' "${MOUNT_POINT}"
printf 'Target boot files:\n'
printf '  /boot/Image\n'
printf '  /boot/uImage (if present)\n'
printf '  /boot/%s\n' "${DTB_NAME}"
printf '  /boot/dtb/allwinner/%s (if present)\n' "${DTB_NAME}"
if (( ${#MODULE_PATHS[@]} > 0 )); then
    printf '  /lib/modules/%s/kernel/drivers/net/wireless/aicsemi/aic8800/\n' "${KERNEL_RELEASE}"
fi

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

if [[ ${INSTALL_BUSYBOX_MODUTILS} -eq 1 ]]; then
    validate_busybox_modutils
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
TARGET_IMAGE="${MOUNT_POINT}/boot/Image"
TARGET_UIMAGE="${MOUNT_POINT}/boot/uImage"
TARGET_DTB="${MOUNT_POINT}/boot/${DTB_NAME}"
TARGET_DTB_SUBDIR="${MOUNT_POINT}/boot/dtb/allwinner/${DTB_NAME}"
MODULE_TARGET_DIR=""
MODULE_TARGET_PATHS=()
MODULE_SHA256S=()
BUSYBOX_MODUTILS_PATHS=()
HAS_UIMAGE=0
HAS_DTB_SUBDIR=0
UIMAGE_SHA256=""

if [[ -f "${TARGET_UIMAGE}" ]]; then
    HAS_UIMAGE=1
fi

if [[ -d "${MOUNT_POINT}/boot/dtb/allwinner" ]]; then
    HAS_DTB_SUBDIR=1
fi

if [[ -f "${TARGET_IMAGE}" ]]; then
    sudo cp -a "${TARGET_IMAGE}" "${TARGET_IMAGE}.old.${TIMESTAMP}"
fi

if [[ ${HAS_UIMAGE} -eq 1 ]]; then
    sudo cp -a "${TARGET_UIMAGE}" "${TARGET_UIMAGE}.old.${TIMESTAMP}"
fi

if [[ -f "${TARGET_DTB}" ]]; then
    sudo cp -a "${TARGET_DTB}" "${TARGET_DTB}.old.${TIMESTAMP}"
fi

if [[ -f "${TARGET_DTB_SUBDIR}" ]]; then
    sudo cp -a "${TARGET_DTB_SUBDIR}" "${TARGET_DTB_SUBDIR}.old.${TIMESTAMP}"
fi

sudo install -m 0644 "${IMAGE_PATH}" "${TARGET_IMAGE}"

if [[ -f "${TARGET_UIMAGE}" ]]; then
    if ! command -v mkimage >/dev/null 2>&1; then
        echo "uImage present on boot partition, but mkimage is missing." >&2
        echo "Install u-boot-tools and re-run to update /boot/uImage." >&2
        exit 1
    fi

    TMP_UIMAGE="$(mktemp)"
    trap 'rm -f "${TMP_UIMAGE}"; cleanup' EXIT
    mkimage -A arm64 -O linux -T kernel -C none -a 0x40080000 -e 0x40080000 \
        -n "Linux" -d "${IMAGE_PATH}" "${TMP_UIMAGE}"
    UIMAGE_SHA256="$(sha256sum "${TMP_UIMAGE}" | awk '{print $1}')"
    sudo install -m 0644 "${TMP_UIMAGE}" "${TARGET_UIMAGE}"
    rm -f "${TMP_UIMAGE}"
fi

sudo install -m 0644 "${DTB_PATH}" "${TARGET_DTB}"
if [[ ${HAS_DTB_SUBDIR} -eq 1 ]]; then
    sudo install -m 0644 "${DTB_PATH}" "${TARGET_DTB_SUBDIR}"
fi

if (( ${#MODULE_PATHS[@]} > 0 )); then
    MODULE_ROOT="${MOUNT_POINT}/lib/modules/${KERNEL_RELEASE}"
    if [[ ! -d "${MODULE_ROOT}" ]]; then
        echo "Target kernel module tree not found: ${MODULE_ROOT}" >&2
        exit 1
    fi
    MODULE_TARGET_DIR="${MODULE_ROOT}/kernel/drivers/net/wireless/aicsemi/aic8800"
    sudo install -d -m 0755 "${MODULE_TARGET_DIR}"
    for module_path in "${MODULE_PATHS[@]}"; do
        module_target="${MODULE_TARGET_DIR}/$(basename "${module_path}")"
        if [[ -f "${module_target}" ]]; then
            sudo cp -a "${module_target}" "${module_target}.old.${TIMESTAMP}"
        fi
        sudo install -m 0644 "${module_path}" "${module_target}"
        MODULE_TARGET_PATHS+=("${module_target}")
        MODULE_SHA256S+=("$(sha256sum "${module_path}" | awk '{print $1}')")
    done
    if ! command -v depmod >/dev/null 2>&1; then
        echo "depmod is required when installing modules" >&2
        exit 1
    fi
    sudo depmod -b "${MOUNT_POINT}" "${KERNEL_RELEASE}"
fi

if [[ ${INSTALL_BUSYBOX_MODUTILS} -eq 1 ]]; then
    sudo install -d -m 0755 "${MOUNT_POINT}/sbin"
    for applet in "${BUSYBOX_MODUTILS[@]}"; do
        applet_path="${MOUNT_POINT}/sbin/${applet}"
        if [[ -e "${applet_path}" || -L "${applet_path}" ]]; then
            if [[ "$(sudo readlink "${applet_path}" 2>/dev/null || true)" != "/bin/busybox" ]]; then
                echo "Preserving existing module tool: /sbin/${applet}"
                continue
            fi
        else
            sudo ln -s /bin/busybox "${applet_path}"
        fi
        BUSYBOX_MODUTILS_PATHS+=("${applet_path}")
    done
fi
sync

echo "Updated boot files:"
if [[ -f "${TARGET_UIMAGE}" ]] && [[ -f "${TARGET_DTB_SUBDIR}" ]]; then
    sudo ls -lh "${TARGET_IMAGE}" "${TARGET_UIMAGE}" "${TARGET_DTB}" "${TARGET_DTB_SUBDIR}"
elif [[ -f "${TARGET_UIMAGE}" ]]; then
    sudo ls -lh "${TARGET_IMAGE}" "${TARGET_UIMAGE}" "${TARGET_DTB}"
elif [[ -f "${TARGET_DTB_SUBDIR}" ]]; then
    sudo ls -lh "${TARGET_IMAGE}" "${TARGET_DTB}" "${TARGET_DTB_SUBDIR}"
else
    sudo ls -lh "${TARGET_IMAGE}" "${TARGET_DTB}"
fi
echo "Backups created with suffix: .old.${TIMESTAMP}"
if (( ${#MODULE_TARGET_PATHS[@]} > 0 )); then
    echo "Updated kernel modules:"
    sudo ls -lh "${MODULE_TARGET_PATHS[@]}"
fi
if (( ${#BUSYBOX_MODUTILS_PATHS[@]} > 0 )); then
    echo "BusyBox module tools available under /sbin:"
    printf '  %s\n' "${BUSYBOX_MODUTILS[@]}"
fi

sudo umount "${MOUNT_POINT}"
MOUNTED_BY_SCRIPT=0
sudo mount -o ro "${DEVICE}" "${MOUNT_POINT}"
MOUNTED_BY_SCRIPT=1

verify_checksum "Image" "${IMAGE_SHA256}" "${TARGET_IMAGE}"
verify_checksum "DTB" "${DTB_SHA256}" "${TARGET_DTB}"
if [[ ${HAS_DTB_SUBDIR} -eq 1 ]]; then
    verify_checksum "DTB (allwinner)" "${DTB_SHA256}" "${TARGET_DTB_SUBDIR}"
fi
if [[ ${HAS_UIMAGE} -eq 1 ]]; then
    verify_checksum "uImage" "${UIMAGE_SHA256}" "${TARGET_UIMAGE}"
fi
for module_index in "${!MODULE_TARGET_PATHS[@]}"; do
    verify_checksum "module $(basename "${MODULE_TARGET_PATHS[module_index]}")" \
        "${MODULE_SHA256S[module_index]}" "${MODULE_TARGET_PATHS[module_index]}"
done
for applet_path in "${BUSYBOX_MODUTILS_PATHS[@]}"; do
    if [[ "$(sudo readlink "${applet_path}")" != "/bin/busybox" ]]; then
        echo "Verification failed for BusyBox module tool: ${applet_path}" >&2
        exit 1
    fi
done

sudo umount "${MOUNT_POINT}"
MOUNTED_BY_SCRIPT=0
echo "Done: boot files and requested modules written, read-only remounted, and checksum-verified."
