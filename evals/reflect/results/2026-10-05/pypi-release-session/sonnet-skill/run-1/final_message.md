I've written the proposals to `proposals.md`. Nothing is applied yet, so tell me which rows to apply by number. All three accepted rows are edits to `pypi-release`, the only skill the session used.

**Accepted**
1. **Version location:** The skill says to edit `pyproject.toml`, but this repo keeps the version in `__about__.py`. The skill should look for the real version source first and never touch build config.
2. **Stale `dist/`:** Clear `dist/` before building, and upload without `--skip-existing`. A "File already exists" error should stop the release for investigation.
3. **Version check:** Before uploading, confirm every file in `dist/` carries the new version.

**Rejected**
- **`pyhton` typo:** a one-off.
- **Apologize and revert:** wouldn't change future behavior.
- **`docker-deploy` changes:** that skill wasn't used in this session.

**Backlog**
- A pre-upload script that checks the built wheel's version against the requested version.
- A release script or Makefile target that runs `rm -rf dist/ && python -m build` in one step.