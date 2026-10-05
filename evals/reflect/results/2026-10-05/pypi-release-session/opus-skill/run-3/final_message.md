I reviewed the release session and wrote four proposed edits to the pypi-release skill into `proposals.md`. I haven't changed any skill files yet.

## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set the version in `pyproject.toml`. In this repo the version is read from another file, so the agent edited the build config and you had to correct it. | First read `pyproject.toml`. If the version is marked `dynamic`, bump the file the build tool reads it from, and never change the build config to make a fixed version work. | skills/pypi-release/SKILL.md — "Bump the version" |
| 2 | Old 2.3.1 files left in `dist/` were picked up by `dist/*` and the upload failed. | Run `rm -rf dist/` before building, then check that `dist/` holds only files for the new version. | skills/pypi-release/SKILL.md — "Build" |
| 3 | The agent worked around the upload error with `--skip-existing`, which can silently skip a same-version file with different contents. | Never use `--skip-existing`. A "File already exists" error means stale files in `dist/` or a version already published, so stop and find the cause. | skills/pypi-release/SKILL.md — "Upload" |
| 4 | The agent said "the index is correct" based only on the upload log. | Before tagging, check that the index actually lists the new sdist and wheel. | skills/pypi-release/SKILL.md — "Upload" |

## Rejected

- **Build before committing:** in this session the commit already came after a good build, so it would change nothing.
- **Upload only files matching the version (`dist/*-X.Y.Z*`):** row 2 already covers this.
- **The `pyhton` typo:** a one-off slip, not a lesson.
- **Changes to docker-deploy:** the session never used that skill.

## Backlog

- **Release script:** one script that clears `dist/`, builds, fails if any file isn't for the expected version, and uploads without `--skip-existing`.
- **Version-source check:** a pre-commit or CI check that fails if `pyproject.toml` stops treating the version as dynamic or drops the line that points to `__about__.py`.

Tell me which rows to apply by number, or point any of them somewhere else.