---
name: pypi-release
description: Release a Python package to the internal package index. Use when asked to cut, publish, or release a package version.
---

# PyPI release

## Bump the version

1. Set the new version in `pyproject.toml` under `[project] version`.
2. Commit with the message `release: vX.Y.Z`.

## Build

Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

## Tag

Tag the release commit `vX.Y.Z` and push the tag.
