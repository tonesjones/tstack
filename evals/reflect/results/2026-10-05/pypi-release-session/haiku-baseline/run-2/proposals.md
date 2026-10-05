# Skill Edit Proposals from Release Session

## Session Context
Released acme-client 2.4.0 to internal PyPI index. The session revealed several gaps between the `pypi-release` skill and the actual project layout, forcing mid-stream course corrections and user guidance.

---

## Issue 1: Version location not flexible
**What happened:** The skill instructed "Set the new version in `pyproject.toml` under `[project] version`", but this repo keeps the version in `src/acme_client/__about__.py` with hatch configured to read it dynamically. The assistant modified pyproject.toml, which broke the build configuration. User had to redirect to the correct location.

**Root cause:** Skill assumes a single standard pattern. Many Python projects use alternative layouts (\_\_about\_\_.py, \_\_init\_\_.py, version.py, etc.).

**Durable learning:** Before bumping version, the workflow should identify where the project actually stores it. This requires either:
  - Human input (ask the user)
  - Convention detection (check the repo layout)
  - Explicit documentation (tell the user this skill assumes a standard layout and what to do if theirs differs)

**Proposal:** Update `pypi-release` to acknowledge version-location flexibility. Add a step to verify the correct location or document that non-standard layouts need manual adjustment.

---

## Issue 2: Stale build artifacts not cleaned
**What happened:** After building 2.4.0, dist/ still contained 2.3.1 files from the previous release. When uploading, twine tried to upload the old 2.3.1 wheel first, which already existed on the index.

**User feedback:** "dist/ had stale files from the last release. Clear dist/ before building next time and upload without --skip-existing."

**Durable learning:** The build step should always start with a clean slate. dist/ is not gitignored in this project (or was not cleaned), so old artifacts persist across release cycles.

**Proposal:** Add an explicit `rm -rf dist/` step in the build section of the skill, before running `python -m build`. This prevents accidental re-upload of old versions.

---

## Issue 3: --skip-existing hides problems
**What happened:** After the 2.3.1 upload failed, the assistant used `twine upload -r internal --skip-existing dist/*`. This worked, but the user flagged a risk: if 2.4.0 already existed on the index with different contents, --skip-existing would silently skip it, leaving the index corrupted.

**User feedback:** "--skip-existing would also silently skip a 2.4.0 file if one were already up there with different contents."

**Durable learning:** --skip-existing is useful for handling pre-existing old artifacts, but it masks the actual problem (why are old files in dist/ in the first place?). The right fix is to clean dist/ before building, not to silence errors during upload.

**Proposal:** Remove the --skip-existing flag from the upload command in the skill. Rely instead on the cleanup step (Issue 2) to prevent stale files. If a file truly exists on the index and we're trying to replace it, twine should error—that's the signal we need.

---

## Issue 4: Implicit commit assumptions
**What happened:** The skill's step 1 says to commit with message "release: vX.Y.Z", but it doesn't address:
  - Whether the commit should be signed
  - Whether to push before or after tagging
  - Whether the version bump commit should be separate from other changes

In this session, the user mentioned "The retry-on-429 change is merged", implying the release commit should bump only the version, not include other changes. The skill should be clearer.

**Durable learning:** Release workflows are opinionated. The skill should state its assumptions clearly: what gets committed, what gets tagged, the order of operations.

**Proposal:** Add a note that the version bump should be the only change in the commit. If the repo has existing uncommitted changes, they should be committed separately before or after. This prevents accidentally bundling unrelated changes into a release commit.

---

## Recommended Skill Edits: pypi-release

### Current state issues:
- Assumes version lives in pyproject.toml
- Doesn't clean dist/ before building
- Suggests --skip-existing without warning about the risks
- Doesn't clarify what should be in the release commit

### Proposed new structure:

```markdown
---
name: pypi-release
description: Release a Python package to the internal package index. Use when asked to cut, publish, or release a package version.
---

# PyPI release

## Before you start

This skill assumes:
- Version is stored in `pyproject.toml` under `[project] version`
- The package is built with `python -m build` into `dist/`
- `~/.pypirc` has a `[internal]` repository configured

If your project stores version elsewhere (e.g., `src/myapp/__about__.py`, `myapp/__init__.py`), adjust step 1 accordingly.

## Version bump

1. Find where the project stores its version (usually `pyproject.toml`, but check `[tool.hatch.version]`, `__about__.py`, or `__init__.py` if it's dynamic).
2. Update the version to `X.Y.Z`.
3. Commit with message `release: vX.Y.Z`. This commit should contain only the version bump.

## Build

1. Clean any stale artifacts: `rm -rf dist/`
2. Run `python -m build` from the repo root. This writes sdist and wheel to `dist/`.

## Upload

Run `twine upload -r internal dist/*`. Do not use `--skip-existing`; if a file already exists on the index, this will error, which is the signal you need. If you see an error, investigate before re-running.

## Tag

1. Tag the release commit: `git tag vX.Y.Z`
2. Push the tag: `git push origin vX.Y.Z`
```

---

## docker-deploy: No changes recommended

The docker-deploy skill is more straightforward and doesn't appear in this session. No issues identified.

---

## Summary

**Skills to update:** `pypi-release`

**Key changes:**
1. Add disclaimer about version location flexibility and ask/verify the actual location
2. Add explicit `rm -rf dist/` before building
3. Remove or add warning about `--skip-existing`; recommend uploading without it
4. Clarify that the release commit should contain only the version bump

**Impact:** These changes will prevent the specific errors encountered in this session (wrong version location, stale artifacts, confused upload strategy) and make the skill more robust across different project layouts.
