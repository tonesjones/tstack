#!/bin/sh
# Build a fresh fixture repo at $1: main = clean base, branch feature/signups = base + seeded slop.
set -e
dest=$1; here=$(cd "$(dirname "$0")" && pwd)
rm -rf "$dest"; mkdir -p "$dest"; cd "$dest"
git init -q -b main
git config user.email eval@example.com; git config user.name eval
cp "$here/base/signups.py" .
git add . && git commit -q -m "base: signups"
git checkout -q -b feature/signups
cp "$here/branch/signups.py" .
git commit -qam "Add attendee list builder"
