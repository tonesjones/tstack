# Skill edit proposals: acme-client 2.4.0 release session

## Summary

The session used **pypi-release**. The user corrected it twice, and both corrections trace back to wrong or missing instructions in the skill:

1. **Where the version lives.** The skill says to set `[project] version` in `pyproject.toml`. acme-client declares `dynamic = ["version"]`, and hatch reads the version from `src/acme_client/__about__.py`. Following the skill caused a build error. The agent then edited the build config to get around it, and the user rejected that: "don't touch the build config".
2. **Stale `dist/` and `--skip-existing`.** The skill builds into `dist/` without clearing it, so 2.3.1 artifacts from the last release were still there and `twine upload dist/*` failed. The agent worked around it with `--skip-existing`. The user rejected that too, because the flag would also silently skip a 2.4.0 file already on the index with different contents. They asked for `dist/` to be cleared before building and for uploads without `--skip-existing`.

**docker-deploy** was not used in this session, so no changes are proposed for it.

Not proposed: the `pyhton` typo was a one-off slip, not a durable lesson.

---

## Proposal 1: pypi-release, bump the version where the build backend reads it

**Evidence:** transcript lines 12–45. Adding a static `version` conflicted with `dynamic = ["version"]`. The agent then removed `version` from `dynamic` and deleted `[tool.hatch.version]`. The user said: "No, don't touch the build config. This repo keeps the version in src/acme_client/__about__.py and hatch reads it from there."

**Change:** replace the "Bump the version" section.

```diff
 ## Bump the version

-1. Set the new version in `pyproject.toml` under `[project] version`.
-2. Commit with the message `release: vX.Y.Z`.
+1. Read `pyproject.toml` to find where the version is defined:
+   - If `[project]` has a static `version = "..."`, edit it there.
+   - If `[project] dynamic` lists `"version"`, the build backend reads the version from another file. For hatch, that file is the `path` under `[tool.hatch.version]`, e.g. acme-client uses `src/acme_client/__about__.py` (`__version__ = "X.Y.Z"`). Edit that file.
+2. Never change the build configuration (`dynamic`, `[tool.hatch.version]`, the build backend) to make a version bump work. If the version source is unclear or the build rejects it, stop and ask the user.
+3. Commit with the message `release: vX.Y.Z` (after the build in the next section succeeds).
```

## Proposal 2: pypi-release, clear dist/ first and upload without --skip-existing

**Evidence:** transcript lines 55–72. Stale 2.3.1 files in `dist/` caused "400 File already exists". The `--skip-existing` workaround was rejected: "--skip-existing would also silently skip a 2.4.0 file if one were already up there with different contents… Clear dist/ before building next time and upload without --skip-existing."

**Change:** replace the "Build" and "Upload" sections.

```diff
 ## Build

-Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
+1. Delete old artifacts first: `rm -rf dist/`. Stale files from earlier releases would otherwise be picked up by `dist/*` at upload time.
+2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
+3. Check that `dist/` contains only the two files for the new version (`<pkg>-X.Y.Z.tar.gz` and `<pkg>-X.Y.Z-py3-none-any.whl`).

 ## Upload

-Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.
+Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.
+
+Do **not** use `--skip-existing`. It silently skips any file already on the index, including a same-version file with different contents, which hides a broken release. If the upload fails with "File already exists", stop. Either `dist/` was not cleaned, or this version has already been published. Diagnose which one before going further, and ask the user if the version is already on the index.
```

---

## Resulting pypi-release/SKILL.md (if both proposals are accepted)

```markdown
---
name: pypi-release
description: Release a Python package to the internal package index. Use when asked to cut, publish, or release a package version.
---

# PyPI release

## Bump the version

1. Read `pyproject.toml` to find where the version is defined:
   - If `[project]` has a static `version = "..."`, edit it there.
   - If `[project] dynamic` lists `"version"`, the build backend reads the version from another file. For hatch, that file is the `path` under `[tool.hatch.version]`, e.g. acme-client uses `src/acme_client/__about__.py` (`__version__ = "X.Y.Z"`). Edit that file.
2. Never change the build configuration (`dynamic`, `[tool.hatch.version]`, the build backend) to make a version bump work. If the version source is unclear or the build rejects it, stop and ask the user.
3. Commit with the message `release: vX.Y.Z` (after the build below succeeds).

## Build

1. Delete old artifacts first: `rm -rf dist/`. Stale files from earlier releases would otherwise be picked up by `dist/*` at upload time.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `dist/` contains only the two files for the new version.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Do **not** use `--skip-existing`. It silently skips any file already on the index, including a same-version file with different contents. If the upload fails with "File already exists", stop. Either `dist/` was not cleaned, or this version has already been published. Diagnose which one, and ask the user if the version is already on the index.

## Tag

Tag the release commit `vX.Y.Z` and push the tag.
```
