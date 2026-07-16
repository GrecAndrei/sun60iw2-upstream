#!/bin/bash
# apply-patches.sh - Apply sun60iw2 patches to a Linux kernel tree

set -e

LINUX_TREE="${1:-}"
PATCH_DIR="$(dirname "$0")/../patches"
CONFIG_DIR="$(dirname "$0")/../configs"

if [ -z "$LINUX_TREE" ]; then
    echo "Usage: $0 <path-to-linux-tree>"
    echo "Example: $0 ~/linux"
    exit 1
fi

if [ ! -e "$LINUX_TREE/.git" ]; then
    echo "Error: $LINUX_TREE is not a git repository"
    exit 1
fi

if [ ! -d "$PATCH_DIR" ]; then
    echo "Error: Patch directory $PATCH_DIR not found"
    exit 1
fi

if [ ! -d "$CONFIG_DIR" ]; then
    echo "Error: Config directory $CONFIG_DIR not found"
    exit 1
fi

echo "Applying patches from $PATCH_DIR to $LINUX_TREE..."

cd "$LINUX_TREE"

if [ -z "$(git config user.name || true)" ] || [ -z "$(git config user.email || true)" ]; then
    echo "Error: git user.name and user.email must be configured in $LINUX_TREE before running git am"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Warning: Linux tree has uncommitted changes"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Apply only standalone git-format-patch files from the bootable SoC series.
for patch in "$PATCH_DIR"/*.patch; do
    if [ -f "$patch" ]; then
        if ! head -n 1 "$patch" | grep -q '^From '; then
            echo "Skipping non-format-patch artifact $(basename "$patch")"
            continue
        fi
        echo "Applying $(basename "$patch")..."
        git am --3way "$patch" || {
            echo "Failed to apply $(basename "$patch")"
            echo "Run 'git am --abort' to clean up"
            exit 1
        }
    fi
done

echo "Installing defconfigs..."
cp "$CONFIG_DIR"/sun60iw2_defconfig "$LINUX_TREE"/arch/arm64/configs/
cp "$CONFIG_DIR"/sun60iw2_minimal_defconfig "$LINUX_TREE"/arch/arm64/configs/

echo "All patches applied successfully!"
