# Skill edit proposals (from the acme-client 2.4.0 release session)

Only `pypi-release` needs edits. `docker-deploy` wasn't used and nothing in the session bears on it, so no change.

## 1. pypi-release: "Bump the version" step is wrong for this repo

**Evidence:** The skill said to set `[project] version` in `pyproject.toml`. The assistant did that, and the build failed because `version` is listed in `dynamic`. The assistant then "fixed" it by deleting the hatch version config. The user rejected that: the repo keeps the version in `src/acme_client/__about__.py`, and hatch reads it via `[tool.hatch.version] path`. Do not touch build config.

**Proposed replacement for the "Bump the version" section:**

```markdown
## Bump the version

1. Find where the version lives before editing anything. Check `pyproject.toml`:
   - If `[project]` lists `dynamic = ["version"]` and there is a `[tool.hatch.version] path = ...` entry, the version is stored in that file (e.g. `src/<pkg>/__about__.py`). Edit `__version__` there.
   - Only if `version = "..."` is already a static field under `[project]` should you edit `pyproject.toml`.
2. Never add a static `version` to `pyproject.toml` or remove `version` from `dynamic` / delete `[tool.hatch.version]` to make a build pass. Don't change build config as part of a release. If the build fails on metadata, stop and ask.
3. Commit with the message `release: vX.Y.Z`.
```

(acme-client is the known example; the general rule is "follow the version source the build config points to".)

## 2. pypi-release: clear `dist/` before building

**Evidence:** `dist/` held stale 2.3.1 files from the previous release, so `twine upload dist/*` failed with 400 "File already exists". The assistant retried with `--skip-existing`. The user objected: that flag would also silently skip a 2.4.0 file already on the index with different contents. The user's instruction: clear `dist/` before building, and upload without `--skip-existing`.

**Proposed replacement for the "Build" and "Upload" sections:**

```markdown
## Build

1. Clear old artifacts first: `rm -rf dist/`. Stale files from earlier releases will otherwise be uploaded too.
2. Run `python -m build` from the repo root. This writes an sdist and a wheel to `dist/`.
3. Check that `ls dist/` shows only files for the version being released.

## Upload

Run `twine upload -r internal dist/*`. The `internal` repository is configured in `~/.pypirc`.

Do not use `--skip-existing`. It hides a real conflict, such as a same-version file already on the index with different contents. If upload returns "File already exists", find out why (stale `dist/`, or the version was already released) rather than skipping.
```

## 3. pypi-release: small hardening (lower confidence)

**Evidence:** The assistant typed `pyhton -m build` and hit "command not found". That is a one-off typo, so it is not worth a skill rule. One cheap addition is a pre-flight check, which would have caught both problems above:

```markdown
## Before releasing

- Confirm the working tree is clean and the target version is greater than the latest one on the index.
```

Optional; drop it if the skill should stay minimal.

## 4. Tag step

No change. Tagging and pushing `vX.Y.Z` worked as written.

## Not proposed

- No skill for the typo or for the assistant's apology. Those are session-specific.
