# Proposed skill edits

Only `pypi-release` needs changes. `docker-deploy` was not used in this session, so I propose no edits to it. The `pyhton` typo was a one-off slip and not worth encoding.

## pypi-release/SKILL.md

### 1. Fix the version bump step (the user corrected this)

The skill says to set `version` in `pyproject.toml`. In this repo the version is dynamic and hatch reads it from `src/acme_client/__about__.py`. Following the skill made the build fail, and the assistant then edited the build config. The user told it to revert that and not touch the build config.

Replace the "Bump the version" section:

```
## Bump the version

1. Find where the version lives before editing anything. Check `pyproject.toml`:
   - If `[project]` has a static `version = "..."`, edit it there.
   - If `version` is listed in `dynamic` (for example with `[tool.hatch.version] path = ...`), edit the file that `path` points to, usually `src/<pkg>/__about__.py`. Never add a static `version` to `pyproject.toml` in this case.
2. Do not change build configuration (`dynamic`, `[tool.hatch.*]`, etc.) to get a build to pass. If the build complains about version metadata, you are probably editing the wrong file. Stop and re-check step 1.
3. Commit with the message `release: vX.Y.Z`.
```

### 2. Clear `dist/` before building (the user corrected this)

Stale files from the previous release were in `dist/`, so the upload tried to push 2.3.1 again and failed with a 400.

Replace the "Build" section:

```
## Build

1. Clear old artifacts first: `rm -rf dist/`. Stale files from earlier releases will otherwise be uploaded too.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `dist/` contains only files for the version being released.
```

### 3. Upload without `--skip-existing` (the user corrected this)

`--skip-existing` would silently skip a file of the new version that was already on the index with different contents. That hides a real conflict.

Replace the "Upload" section:

```
## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Do not use `--skip-existing`. It can silently skip a file of the new version that is already on the index with different contents. If the upload fails with "File already exists", first check that `dist/` was cleared and holds only the new version. If a file of the new version really is already on the index, stop and ask the user.
```

### 4. Tag (no change)

The tag step worked as written. Keep it.
