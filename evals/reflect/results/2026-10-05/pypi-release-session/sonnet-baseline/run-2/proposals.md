# Skill edit proposals (from the acme-client 2.4.0 release session)

Only `pypi-release` needs edits. `docker-deploy` was not used and nothing in the session bears on it, so no change is proposed.

## 1. pypi-release: version location (user correction)

**Evidence:** The skill said to set `[project] version` in `pyproject.toml`. The assistant did that, and the build failed because `version` was listed in `dynamic`. The assistant then removed `version` from `dynamic` and deleted `[tool.hatch.version]`. The user rejected that: "don't touch the build config", the version lives in `src/acme_client/__about__.py`, and hatch reads it from there.

**Edit:** replace "Bump the version" with:

```markdown
## Bump the version

1. Find where the version is defined before editing anything. Check `pyproject.toml`:
   - If `[project]` lists `version` in `dynamic` (e.g. `[tool.hatch.version] path = "..."`), the version is in that file. Edit the `__version__` there, e.g. `src/<pkg>/__about__.py`.
   - Only if `version` is a static field under `[project]` do you edit `pyproject.toml`.
2. Never change build configuration (`dynamic`, `[tool.hatch.*]`) to make a version bump work. If the build complains about the version, you are editing the wrong place.
3. Commit with the message `release: vX.Y.Z`.
```

Note: the skill is a general one, so the `acme-client` / `__about__.py` specifics should not be hard-coded. The "check `dynamic` first" rule is the part that generalizes. If this skill is only ever used for this repo, add a line naming `src/acme_client/__about__.py`.

## 2. pypi-release: clean dist/ before build (user correction)

**Evidence:** `dist/` held stale 2.3.1 files from the previous release. The upload of `dist/*` failed with 400 "File already exists".

**Edit:** in "Build", add as the first step:

```markdown
Clear `dist/` first (`rm -rf dist/`). Stale artifacts from earlier releases get picked up by `dist/*` and break the upload. Then run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
```

## 3. pypi-release: no `--skip-existing` (user correction)

**Evidence:** The assistant retried with `--skip-existing` to get past the 400. The user pointed out that this would also silently skip a 2.4.0 file already on the index with different contents. The user said to upload without it.

**Edit:** in "Upload", add:

```markdown
Do not use `twine upload --skip-existing`. It hides a collision on the new version, where a file with different contents is already on the index. If the upload reports "File already exists", find out why (usually stale files in `dist/`; see Build). Do not paper over it. Before uploading, check that `dist/` contains only files for the version being released.
```

## 4. pypi-release: verify after upload (optional, small)

**Evidence:** The assistant concluded "the index is correct" because both 2.4.0 files uploaded. That is reasonable, but the skill gives no check step. It is a weaker learning, not a user correction.

**Edit (optional):** after Upload, add "Confirm that the output shows exactly the new version's sdist and wheel being uploaded, and no other versions." Skip this if the skill should stay short.

## 5. Not proposed

- The `pyhton` typo was a one-off slip. It is not a skill matter.
- Tagging and pushing worked as described, so that section is unchanged.
- `git commit -am` and the ordering of commit vs. build are fine. Optionally the commit could run after a successful build, but nothing in the session showed a problem.

## Resulting skill (for convenience)

```markdown
---
name: pypi-release
description: Release a Python package to the internal package index. Use when asked to cut, publish, or release a package version.
---

# PyPI release

## Bump the version

1. Find where the version is defined before editing anything. Check `pyproject.toml`:
   - If `[project]` lists `version` in `dynamic` (e.g. `[tool.hatch.version] path = "..."`), the version is in that file. Edit the `__version__` there, e.g. `src/<pkg>/__about__.py`.
   - Only if `version` is a static field under `[project]` do you edit `pyproject.toml`.
2. Never change build configuration (`dynamic`, `[tool.hatch.*]`) to make a version bump work. If the build complains about the version, you are editing the wrong place.
3. Commit with the message `release: vX.Y.Z`.

## Build

Clear `dist/` first (`rm -rf dist/`). Stale artifacts from earlier releases get picked up by `dist/*` and break the upload. Then run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Do not use `--skip-existing`. It hides a collision on the new version, where a file with different contents is already on the index. If the upload reports "File already exists", find out why (usually stale files in `dist/`; see Build). Do not paper over it. Before uploading, check that `dist/` contains only files for the version being released.

## Tag

Tag the release commit `vX.Y.Z` and push the tag.
```
