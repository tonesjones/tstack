#!/bin/sh
# Build a fresh fixture repo at $1: main = clean base, branch feature/restock = base + seeded slop.
set -e
dest=$1; here=$(cd "$(dirname "$0")" && pwd)
rm -rf "$dest"; mkdir -p "$dest"; cd "$dest"
git init -q -b main
git config user.email eval@example.com; git config user.name eval
cp "$here/base/inventory.py" .
git add . && git commit -q -m "base: inventory"
git checkout -q -b feature/restock
cp "$here/branch/inventory.py" .
git commit -qam "Add restock planning"
