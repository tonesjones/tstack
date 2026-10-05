## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set the version in `pyproject.toml` `[project] version`, which broke the build (version is `dynamic`) and was reverted at the user's request. | Replace step 1: locate the version source first; if `pyproject.toml` lists `version` in `dynamic` (e.g. `[tool.hatch.version] path`), bump that file (here `src/acme_client/__about__.py`) and never edit build config. | skills/pypi-release/SKILL.md, "Bump the version" |
| 2 | Stale 2.3.1 files in `dist/` made the upload fail with "File already exists", and the agent reached for `--skip-existing`, which could silently skip a changed same-version file. | In Build, add: clear `dist/` (`rm -rf dist/`) before `python -m build`. In Upload, add: upload without `--skip-existing`; a "File already exists" error means stale artifacts or a version that was already released, so stop and investigate. | skills/pypi-release/SKILL.md, "Build" and "Upload" |
| 3 | The agent committed before building and uploaded without confirming the artifacts matched the target version. | Before uploading, check that every file in `dist/` carries the new version; abort if any file has another version. | skills/pypi-release/SKILL.md, "Upload" |

## Rejected

- Principle: Don't run a bare command name that may be mistyped (the `pyhton` typo).
  Reason: specificity (a one-off typo)
- Principle: Apologize and revert when the user objects.
  Reason: decision-changing (no future change in behavior)
- Principle: docker-deploy guidance changes.
  Reason: skill-not-used (not loaded this session)

## Backlog

- Version-source drift between the skill and the repo. Hit: the skill said to edit `pyproject.toml`, but the repo's version lives in `__about__.py`. Mechanism: a pre-upload check script that compares the built wheel's version to the requested version and fails on mismatch.
- Stale artifacts in `dist/`. Hit: old 2.3.1 files were uploaded alongside the new release. Mechanism: a release script or Makefile target that does `rm -rf dist/ && python -m build`, so the skill calls one command.
