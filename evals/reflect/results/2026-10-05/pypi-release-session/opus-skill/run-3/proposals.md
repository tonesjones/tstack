## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set `[project] version` in `pyproject.toml`, which breaks repos that declare `dynamic = ["version"]`; the agent then "fixed" the build config and the user had to correct it. | Replace step 1 with: read `pyproject.toml` first, and if `version` is in `project.dynamic`, bump the file the build backend reads (e.g. `[tool.hatch.version] path`), never editing `dynamic` or the backend config to make a static version work. | skills/pypi-release/SKILL.md — "Bump the version" |
| 2 | Stale artifacts from the previous release stayed in `dist/`, so `twine upload dist/*` tried to re-upload 2.3.1 and failed. | Add a first step to Build: `rm -rf dist/` before `python -m build`, then confirm `dist/` holds only files named for the new version. | skills/pypi-release/SKILL.md — "Build" |
| 3 | The agent reached for `--skip-existing` on an upload error, which would silently skip a same-version file with different contents. | In Upload, state: never use `--skip-existing`; a "File already exists" error means stale `dist/` contents or a version that was already published, so stop and diagnose rather than bypass it. | skills/pypi-release/SKILL.md — "Upload" |
| 4 | After the bypass, the agent said "the index is correct" based only on twine's log, without checking what the index actually holds. | Add a closing check to Upload: confirm the index lists exactly the new sdist and wheel for X.Y.Z (e.g. `pip download acme-client==X.Y.Z --no-deps -i <internal index>` or the index's simple page) before tagging. | skills/pypi-release/SKILL.md — "Upload" |

## Rejected

- Principle: Build before committing, so a failed build never leaves a `release:` commit behind.
  Reason: decision-changing — the session already committed after a successful build, so nothing went wrong, and only one lens raised it.
- Principle: Scope the upload glob to the release version (`dist/*-X.Y.Z*`) as a second safeguard.
  Reason: duplicate — row 2 (clean `dist/` and check its contents) already prevents this, and two overlapping rules add noise.
- Principle: Double-check command spelling (`pyhton` typo).
  Reason: specificity — a trivial one-off retry.
- Principle: The docker-deploy skill could use cleanup or verification steps too.
  Reason: skill-not-used — the session never loaded or needed docker-deploy.

## Backlog

- Pre-upload release guard. Hit: stale 2.3.1 files in `dist/` were picked up by `twine upload dist/*`, and the agent bypassed the error with `--skip-existing`. Mechanism: a `release.sh` (or Makefile target) that runs `rm -rf dist && python -m build`, fails if any `dist/` file isn't for the version that `__about__.py` / `hatch version` reports, and runs twine without `--skip-existing`; the skill would then just call it.
- Version-source check. Hit: a static `version` was added next to `dynamic = ["version"]`, and then `dynamic` was removed to make the build pass. Mechanism: a pre-commit or CI check that fails when `pyproject.toml` drops `version` from `project.dynamic` or removes `[tool.hatch.version]`.
