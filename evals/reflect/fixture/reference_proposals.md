## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set `[project] version`, which breaks repos that declare a dynamic version. | Before bumping, check `pyproject.toml`: if `version` is in `project.dynamic`, bump the file the build backend reads (for hatch, `[tool.hatch.version] path`, e.g. `__about__.py`) and leave the build config alone. | skills/pypi-release/SKILL.md, Bump the version |
| 2 | Stale files in `dist/` from the previous release made the upload fail, and `--skip-existing` would hide a real conflict. | Delete `dist/` before `python -m build`, and upload without `--skip-existing`. | skills/pypi-release/SKILL.md, Build and Upload |

## Rejected

- Principle: Check command spelling. Reason: specificity (one-off typo).
