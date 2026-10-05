# Skill edit proposals from the acme-client 2.4.0 release session

## Summary

The session used **pypi-release**. The user corrected two of its steps, and the skill text caused both mistakes:

1. **Version bump location.** The skill says to set `[project] version` in `pyproject.toml`. acme-client declares `dynamic = ["version"]`, and hatch reads the version from `src/acme_client/__about__.py`. Following the skill broke the build. The assistant then edited the build config to make the build pass, and the user rejected that: "don't touch the build config."
2. **Stale `dist/` and `--skip-existing`.** The skill never says to clear `dist/`. Old 2.3.1 files were still there, so `twine upload dist/*` failed. The assistant worked around it with `--skip-existing`. The user rejected that too, because that flag would also silently skip a 2.4.0 file already on the index with different contents. Their instruction: clear `dist/` before building and upload without `--skip-existing`.

Both corrections apply to every future release, so they belong in the skill.

**docker-deploy** wasn't used and nothing in the session concerns it, so I'm proposing no changes to it.

**Left out on purpose:** the `pyhton` typo was a one-off and fixed itself, so it isn't a lesson. I'm also not adding acme-client's exact file path as the only rule. The skill covers any package, so the edit tells it to follow whatever version source `pyproject.toml` declares, and uses acme-client as the example.

---

## Proposal 1: pypi-release, "Bump the version" section

**Why:** Corrections 1 and 2 above. Many packages (hatch, setuptools-scm, flit) don't keep a static `[project] version`, and the user explicitly doesn't want build config changed during a release.

**Current:**

```markdown
## Bump the version

1. Set the new version in `pyproject.toml` under `[project] version`.
2. Commit with the message `release: vX.Y.Z`.
```

**Proposed:**

```markdown
## Bump the version

1. Read `pyproject.toml` to find where the version comes from:
   - If `[project]` has a static `version = "..."`, edit it there.
   - If `[project] dynamic` includes `"version"`, the version lives in the file the build backend reads.
     For hatch, that is the `path` under `[tool.hatch.version]` (for example, acme-client uses
     `src/acme_client/__about__.py`, `__version__ = "X.Y.Z"`). Edit that file.
2. Do not change the build configuration (`dynamic`, `[tool.hatch.version]`, the build backend, and so on)
   to make a release work. If the version source is unclear or the build rejects it, stop and ask.
3. Commit with the message `release: vX.Y.Z`.
```

---

## Proposal 2: pypi-release, "Build" section

**Why:** Correction 2. Leftover artifacts in `dist/` get uploaded alongside the new ones.

**Current:**

```markdown
## Build

Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
```

**Proposed:**

```markdown
## Build

1. Remove old artifacts first: `rm -rf dist/`. Leftover files from earlier releases would otherwise be uploaded too.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `dist/` holds only the new version's sdist and wheel.
```

---

## Proposal 3: pypi-release, "Upload" section

**Why:** Correction 2. `--skip-existing` hides real conflicts, such as a file for the same version already on the index with different contents.

**Current:**

```markdown
## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.
```

**Proposed:**

```markdown
## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Never use `--skip-existing`. It would silently skip a file for this version that is already on the index,
even if its contents differ. If the upload reports "File already exists":
- for an old version, `dist/` was not cleaned. Clear it, rebuild, and upload again.
- for the version being released, stop and tell the user. Don't work around it.
```

---

## Full proposed `skills/pypi-release/SKILL.md`

```markdown
---
name: pypi-release
description: Release a Python package to the internal package index. Use when asked to cut, publish, or release a package version.
---

# PyPI release

## Bump the version

1. Read `pyproject.toml` to find where the version comes from:
   - If `[project]` has a static `version = "..."`, edit it there.
   - If `[project] dynamic` includes `"version"`, the version lives in the file the build backend reads.
     For hatch, that is the `path` under `[tool.hatch.version]` (for example, acme-client uses
     `src/acme_client/__about__.py`, `__version__ = "X.Y.Z"`). Edit that file.
2. Do not change the build configuration (`dynamic`, `[tool.hatch.version]`, the build backend, and so on)
   to make a release work. If the version source is unclear or the build rejects it, stop and ask.
3. Commit with the message `release: vX.Y.Z`.

## Build

1. Remove old artifacts first: `rm -rf dist/`. Leftover files from earlier releases would otherwise be uploaded too.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `dist/` holds only the new version's sdist and wheel.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Never use `--skip-existing`. It would silently skip a file for this version that is already on the index,
even if its contents differ. If the upload reports "File already exists":
- for an old version, `dist/` was not cleaned. Clear it, rebuild, and upload again.
- for the version being released, stop and tell the user. Don't work around it.

## Tag

Tag the release commit `vX.Y.Z` and push the tag.
```
