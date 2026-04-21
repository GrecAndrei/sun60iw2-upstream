#!/bin/bash
# apply-patches.sh - Apply sun60iw2 patches to a Linux kernel tree

set -e

LINUX_TREE="${1:-}"
PATCH_DIR="$(dirname "$0")/../patches"

if [ -z "$LINUX_TREE" ]; then
    echo "Usage: $0 <path-to-linux-tree>"
    echo "Example: $0 ~/linux"
    exit 1
fi

if [ ! -d "$LINUX_TREE/.git" ]; then
    echo "Error: $LINUX_TREE is not a git repository"
    exit 1
fi

if [ ! -d "$PATCH_DIR" ]; then
    echo "Error: Patch directory $PATCH_DIR not found"
    exit 1
fi

echo "Applying patches from $PATCH_DIR to $LINUX_TREE..."

cd "$LINUX_TREE"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Warning: Linux tree has uncommitted changes"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Apply patches
for patch in "$PATCH_DIR"/*.patch; do
    if [ -f "$patch" ]; then
        echo "Applying $(basename "$patch")..."
        git am --3way "$patch" || {
            echo "Failed to apply $(basename "$patch")"
            echo "Run 'git am --abort' to clean up"
            exit 1
        }
    fi
done

echo "All patches applied successfully!"
