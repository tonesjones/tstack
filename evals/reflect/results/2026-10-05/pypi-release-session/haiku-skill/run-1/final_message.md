```
## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | Skill hardcodes version in `pyproject.toml [project]`, but projects store it variously (e.g., `src/acme_client/__about__.py`). User had to correct the approach. | Add guidance: check the project's actual version source first (common patterns: `pyproject.toml`, `src/*/__about__.py`, `src/*/_version.py`), then bump accordingly; don't assume `pyproject.toml`. | skills/pypi-release/SKILL.md / "Bump the version" |
| 2 | Stale `dist/` files from prior releases (2.3.1 wheels) broke the build or forced unsafe workarounds; skill never mentions cleaning. | Add a step to clean `dist/` before building: `rm -rf dist/` then `python -m build`. Ensures fresh build output. | skills/pypi-release/SKILL.md / "Build" |
| 3 | Skill doesn't mention `--skip-existing` is unsafe; it silently skips files and would skip 2.4.0 if already present with different contents, corrupting the release. | Remove any suggestion of `--skip-existing`. Clean `dist/` instead to fix duplicate-file errors. Upload command stays: `twine upload -r internal dist/*`. | skills/pypi-release/SKILL.md / "Upload" |

## Rejected

- Typo `pyhton` instead of `python`: Reason: trivial, one-off mistake not a durable pattern.

## Backlog

None.
```