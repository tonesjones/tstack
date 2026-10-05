# Skill edit proposals from session: release acme-client 2.4.0

## Summary

The session used `pypi-release`. The user corrected it twice, and each correction points to a gap in the skill:

1. **Version location.** The skill says to set the version in `pyproject.toml` under `[project] version`. In acme-client the version is dynamic: hatch reads it from `src/acme_client/__about__.py`. Following the skill caused a build error. The assistant then "fixed" that error by rewriting the build config, and the user had it reverted.
2. **Stale `dist/` and `--skip-existing`.** The skill builds into `dist/` without clearing it first, so `dist/*` still held the 2.3.1 files from the last release. The upload failed with "File already exists", and the assistant worked around it with `--skip-existing`. The user said why that's unsafe: it would also silently skip a 2.4.0 file already on the index, even one with different contents. Their rule: clear `dist/` before building, and upload without `--skip-existing`.

Both corrections are durable. They apply to every future release, not just this one, so both belong in `pypi-release`.

`docker-deploy` wasn't used and nothing in the session touches it, so no change is proposed there.

Not proposed: the `pyhton` typo. It was a one-off slip with nothing to learn from.

---

## Proposal 1: `pypi-release`: find where the version actually lives and never change build config to bump it

**Evidence:** Lines 12–41 of the transcript. Adding a static `version` next to `dynamic = ["version"]` made hatch fail. The assistant then removed `dynamic` and `[tool.hatch.version]`, and the user replied: "No, don't touch the build config. This repo keeps the version in src/acme_client/__about__.py and hatch reads it from there."

**Edit:** Replace the "Bump the version" section with:

```markdown
## Bump the version

1. Find where the version is defined before editing anything. Read `pyproject.toml`:
   - If `[project]` has a static `version = "..."`, edit it there.
   - If `version` is listed in `[project] dynamic`, the build backend reads it from somewhere else. For hatch, `[tool.hatch.version] path` names the file (e.g. `src/<pkg>/__about__.py` containing `__version__ = "..."`). Edit that file.
2. Never change build configuration (`dynamic`, `[tool.hatch.version]`, backend settings) as a way to bump the version. If the build rejects the bump, you edited the wrong place. Revert and find the real source.
3. Commit with the message `release: vX.Y.Z`.
```

---

## Proposal 2: `pypi-release`: clear `dist/` before building and upload without `--skip-existing`

**Evidence:** Lines 55–72. `twine upload -r internal dist/*` tried to upload the stale `acme_client-2.3.1` files and got a 400 "File already exists". The assistant retried with `--skip-existing`. The user said: "--skip-existing would also silently skip a 2.4.0 file if one were already up there with different contents. dist/ had stale files from the last release. Clear dist/ before building next time and upload without --skip-existing."

**Edit:** Replace the "Build" and "Upload" sections with:

```markdown
## Build

1. Remove old build output first: `rm -rf dist/`. Otherwise `dist/*` still holds files from earlier releases, and the upload will try to re-upload them.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `dist/` holds only the two files for the new version, with no older versions mixed in.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Do **not** use `--skip-existing`. It would also silently skip a file for the version you're releasing if one is already on the index, even one with different contents. If the upload reports "File already exists":
- For an older version, `dist/` wasn't cleaned. Clear it, rebuild, and upload again.
- For the version you're releasing, stop and tell the user. Don't overwrite or skip it.
```

---

## Resulting `skills/pypi-release/SKILL.md` (both proposals applied)

```markdown
---
name: pypi-release
description: Release a Python package to the internal package index. Use when asked to cut, publish, or release a package version.
---

# PyPI release

## Bump the version

1. Find where the version is defined before editing anything. Read `pyproject.toml`:
   - If `[project]` has a static `version = "..."`, edit it there.
   - If `version` is listed in `[project] dynamic`, the build backend reads it from somewhere else. For hatch, `[tool.hatch.version] path` names the file (e.g. `src/<pkg>/__about__.py` containing `__version__ = "..."`). Edit that file.
2. Never change build configuration (`dynamic`, `[tool.hatch.version]`, backend settings) as a way to bump the version. If the build rejects the bump, you edited the wrong place. Revert and find the real source.
3. Commit with the message `release: vX.Y.Z`.

## Build

1. Remove old build output first: `rm -rf dist/`. Otherwise `dist/*` still holds files from earlier releases, and the upload will try to re-upload them.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `dist/` holds only the two files for the new version, with no older versions mixed in.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Do **not** use `--skip-existing`. It would also silently skip a file for the version you're releasing if one is already on the index, even one with different contents. If the upload reports "File already exists":
- For an older version, `dist/` wasn't cleaned. Clear it, rebuild, and upload again.
- For the version you're releasing, stop and tell the user. Don't overwrite or skip it.

## Tag

Tag the release commit `vX.Y.Z` and push the tag.
```

---

## No change: `docker-deploy`

It wasn't used in this session, and nothing that happened applies to it.
