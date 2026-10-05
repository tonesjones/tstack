Reviewed the session and identified three durable learnings that should improve the pypi-release skill:

1. **Version location varies** — The skill hardcodes `pyproject.toml` but this repo uses hatch dynamic version from `src/acme_client/__about__.py`. Need a detection step.

2. **Clean dist/ before building** — Stale files from prior releases caused twine to reject old versions as duplicates, blocking the new ones.

3. **Remove --skip-existing guidance** — It silently skips files with matching names but different contents; the solution is ensuring dist/ is clean first.

Written full proposals to `proposals.md` with specific recommendations and implementation priority.