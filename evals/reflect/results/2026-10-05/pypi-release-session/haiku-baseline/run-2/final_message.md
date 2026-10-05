Done. I've reviewed the session transcript and identified four key issues that emerged during the PyPI release workflow:

1. **Version location not flexible** — The skill assumes version lives in `pyproject.toml`, but this project stores it in `src/acme_client/__about__.py`. The skill needs to acknowledge different project layouts.

2. **Stale build artifacts** — dist/ wasn't cleaned before building, leaving 2.3.1 files that caused upload errors. A `rm -rf dist/` step is needed.

3. **--skip-existing masks problems** — Using this flag silently skipped old files but risks hiding genuine index corruption if a new version already exists with wrong contents. Better to fail loudly and require investigation.

4. **Implicit commit assumptions** — The skill doesn't clarify that the release commit should contain only the version bump, or what to do if other changes are pending.

I've written detailed proposals to **proposals.md** with the root causes, durable learnings, and a revised `pypi-release` skill structure that addresses all four issues. The docker-deploy skill had no issues in this session.