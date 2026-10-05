## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set `[project] version` in pyproject.toml, which breaks builds in repos where the version is `dynamic` and read from a source file, and led the session to rewrite the build config. | Replace step 1 with: check `[project]` first; if `version` is listed in `dynamic`, bump the file that `[tool.hatch.version] path` (or the backend's equivalent) points to, such as `__about__.py`, and never edit the build config to make the bump work. | skills/pypi-release/SKILL.md § Bump the version |
| 2 | Stale artifacts from earlier releases in `dist/` get uploaded with `dist/*` and fail with "File already exists". | Add a first step to Build: clear `dist/` (`rm -rf dist/`) before running `python -m build`, so `dist/` only holds the version being released. | skills/pypi-release/SKILL.md § Build |
| 3 | The workaround for a "File already exists" upload error was `--skip-existing`, which would also skip a same-version file with different contents without saying so. | Add to Upload: never use `--skip-existing`; if the upload says a file already exists, find out why (stale `dist/` or a version that was already published) and fix that instead of skipping. | skills/pypi-release/SKILL.md § Upload |

## Rejected

- Principle: Commands should be spelled correctly (`pyhton` → `python`).
  Reason: specificity (a trivial typo that was retried right away).
- Principle: Release changes should go through the release skill, not be fixed by improvising.
  Reason: duplicate (rows 1 and 3 already cover this for the two places it happened).
- Principle: Release steps should run in order: build and upload succeed before the release commit is pushed or tagged, so a failed upload doesn't leave a tagged commit behind.
  Reason: convergence (only one lens found it, the session's order caused no failure, and the user said nothing about it).
- Principle: Pushing only the tag (`git push origin vX.Y.Z`) leaves the `release: vX.Y.Z` commit off the remote `main` branch.
  Reason: convergence (only one lens found it, and the session doesn't show whether this repo wants release commits pushed directly to main or sent through a PR; worth asking the user).
- Principle: The Docker deploy steps could be improved.
  Reason: skill-not-used (docker-deploy was never loaded in this session).

## Backlog

- Pre-upload guard for release artifacts. Hit: `dist/` held 2.3.1 files during the 2.4.0 upload. Mechanism: a small script in the pypi-release skill (or a release Makefile target) that fails if any file in `dist/` doesn't match the target version, run before `twine upload`.
- Version-source check. Hit: the session added a static `version` while `dynamic = ["version"]` was set. Mechanism: a script that reads pyproject.toml and prints which file holds the version (static field vs. the `[tool.hatch.version] path`), called from the Bump step.
