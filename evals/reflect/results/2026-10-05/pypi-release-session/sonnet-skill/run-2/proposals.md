## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set the version in `pyproject.toml`, but this repo uses `dynamic = ["version"]` with hatch reading `__about__.py`; following the skill broke the build and the agent edited build config until the user corrected it. | Replace the bump step: first check whether `pyproject.toml` lists `version` in `dynamic` (or has `[tool.hatch.version]`). If so, bump the file it points to and never edit the build config. Otherwise set `[project] version`. | skills/pypi-release/SKILL.md, "Bump the version" |
| 2 | Stale 2.3.1 files in `dist/` from the last release made the upload fail with "File already exists". The agent worked around it with `--skip-existing`, which would also silently skip a 2.4.0 file already on the index with different contents. | Add to Build: `rm -rf dist/` before `python -m build`. Add to Upload: upload only the new version's files, never use `--skip-existing`, and treat a "File already exists" error as a stop-and-investigate signal. | skills/pypi-release/SKILL.md, "Build" and "Upload" |
| 3 | The skill has no check that the upload landed and that the tag matches the built version, so success was self-reported from twine output. | Add a closing check before tagging: `dist/` contains only `*-X.Y.Z*` files, and the version in the built filenames matches the tag. | skills/pypi-release/SKILL.md, "Tag" |

## Rejected

- Principle: Don't mistype commands (`pyhton`).
  Reason: durability (a one-off typo).
- Principle: Update docker-deploy with release-related lessons.
  Reason: skill-not-used (docker-deploy was never loaded and is unrelated).
- Principle: Don't make "fix" edits to build config to get a build passing when the repo's convention is unknown.
  Reason: already-covered (folded into row 1).

## Backlog

- Stale artifacts in `dist/` leaking into uploads. Hit: the 2.3.1 files were re-uploaded, causing a 400 error. Mechanism: a release script or Makefile target that cleans `dist/` before building and uploads only the current version's files, so the skill calls one command.
- Version source of truth differs by repo. Hit: the skill assumed `pyproject.toml`, but the version lived in `__about__.py`. Mechanism: a script that resolves the version file (for example `hatch version`) instead of prose.
