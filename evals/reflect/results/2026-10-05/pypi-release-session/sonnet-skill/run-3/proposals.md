## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set `[project] version` in pyproject.toml, which broke the build on a repo with `dynamic = ["version"]` and drew a user correction. | Replace the step with: check pyproject.toml first; if `version` is in `dynamic` (e.g. `[tool.hatch.version] path`), bump the version in that source file and never edit build config. Otherwise set `[project] version`. | skills/pypi-release/SKILL.md, "Bump the version" |
| 2 | Stale files in `dist/` from the previous release made the upload hit "File already exists", and the agent reached for `--skip-existing`, which can silently skip a changed same-version file. | Add to Build: `rm -rf dist/` before `python -m build`. Add to Upload: never use `--skip-existing`; if the index reports "File already exists", stop and check `dist/` for stale files and whether the version is already published. | skills/pypi-release/SKILL.md, "Build" and "Upload" |
| 3 | The agent said "the index is correct" from the upload output alone, without checking what was actually published. | Add a verification step after upload: confirm that only the new version's two files (sdist and wheel) were uploaded, and tag only after that. | skills/pypi-release/SKILL.md, "Upload" |

## Rejected

- Principle: Don't make typo'd commands (`pyhton`).
  Reason: durability

- Principle: Add docker-deploy guidance.
  Reason: skill-not-used

- Principle: Apologise less / the agent edited config without asking.
  Reason: already-covered (row 1 fixes the root cause, which is the skill's wrong instruction)

## Backlog

- Release preflight. Hit: stale `dist/` and a version bump in the wrong file. Mechanism: a release script or Makefile target that cleans `dist/`, builds, and runs `twine check`, plus a CI check that the version source matches the tag.
- Tag/version consistency. Hit: the tag was pushed on trust. Mechanism: a CI check that fails when the tag differs from the built version.
