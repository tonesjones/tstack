## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | pypi-release skill assumes version is in `pyproject.toml [project]` but many repos keep it in a source file; skill blindly modifies pyproject causing build failure | Add guidance to locate the actual version definition first (check `src/*/\_\_about\_\_.py`, `src/*/\_\_init\_\_.py`, setup.py, or pyproject.toml), then bump only that location—never modify build config's `dynamic` or `[tool.hatch.version]` fields | pypi-release / Bump the version |
| 2 | dist/ directory accumulated stale files from previous releases, creating upload confusion; no cleanup step before build | Add explicit step: remove old dist/ contents before building with `rm -rf dist/` | pypi-release / Build |
| 3 | twine upload with `--skip-existing` silently hides real upload errors if a file with same name but different content already exists on index | Change upload command from `twine upload -r internal --skip-existing dist/*` to `twine upload -r internal dist/*` (safe only after dist/ cleanup) | pypi-release / Upload |
| 4 | Skill provided no guidance on respecting repo's build-system configuration; assistant modified pyproject.toml's `dynamic` field causing build to reject both static and hatch-based versioning | Add note: never modify pyproject.toml's build-system settings (`dynamic`, `[tool.hatch.version]`, etc.) to work around version issues—these are enforced by the repo's build setup and must be respected | pypi-release / Bump the version |

## Rejected

None.

## Backlog

None.

---

I found four tightly-connected findings, all rooted in the pypi-release skill's incorrect assumption about how Python projects store version numbers. The session shows a real, durable pattern: version can live in multiple places, build config must never be touched, and dist/ hygiene prevents silent failures. All four route to edits in the one skill the session used.

Shall I apply these edits to `skills/pypi-release/SKILL.md`?