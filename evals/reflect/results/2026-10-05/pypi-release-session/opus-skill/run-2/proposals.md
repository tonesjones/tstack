## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set `[project] version` in `pyproject.toml`, which breaks builds in repos where `version` is in `project.dynamic`, and that led to an unwanted edit of the build config. | Replace step 1 with: "Find where the version comes from first. If `version` is in `[project] dynamic`, bump the file that the build backend reads (for example `[tool.hatch.version] path`). Only set `[project] version` when it is already static." | skills/pypi-release/SKILL.md § Bump the version |
| 2 | When the build failed, the agent changed the build config to get it passing, and the user had to correct it. | Add a rule: "Never edit build-backend config (`dynamic`, `[tool.*.version]`, build-system) to make a release build pass. Bump the version in the repo's existing source of truth and stop to ask if that fails." | skills/pypi-release/SKILL.md § Bump the version |
| 3 | `python -m build` adds files to `dist/`, so stale artifacts from an earlier release were left there and picked up by `twine upload dist/*`. | Make the Build step start with `rm -rf dist/` before `python -m build`. | skills/pypi-release/SKILL.md § Build |
| 4 | The agent worked around the "File already exists" error with `--skip-existing`, which would also silently skip a conflicting file for the new version. | Add to Upload: "Never use `--skip-existing`. A 'File already exists' error means `dist/` is dirty or the version was already released, so stop and investigate." | skills/pypi-release/SKILL.md § Upload |
| 5 | The release was declared done based only on twine's "Uploading…" lines, without checking what was in `dist/` or what the index serves. | Before upload, check that `ls dist/` shows only `<name>-X.Y.Z` files. After upload, confirm the index serves the version (for example `pip index versions <name> -i <internal-url>` or `pip download <name>==X.Y.Z --no-deps`) before tagging. | skills/pypi-release/SKILL.md § Upload / § Tag |

## Rejected

- Principle: Typos in commands (`pyhton`) waste a tool call.
  Reason: specificity (trivial retry, not a learning).
- Principle: acme-client keeps its version in `src/acme_client/__about__.py`.
  Reason: durability (a repo-specific path that may change; row 1 generalizes it as "find the source of truth first").
- Principle: Docker image deploys should verify the rollout.
  Reason: skill-not-used (docker-deploy was available but neither needed nor loaded).
- Principle: Upload a version-specific glob (`dist/<name>-X.Y.Z*`) instead of `dist/*`.
  Reason: duplicate (rows 3 and 5 already prevent stale files from being uploaded; adding a third safeguard for the same failure only adds text).
- Principle: Commit the version bump only after a successful build.
  Reason: decision-changing (the session already did this and nothing went wrong; the step order in the skill is a minor point).

## Backlog

- Release preflight script. Hit: stale 2.3.1 artifacts in `dist/` caused a 400, and the `--skip-existing` workaround could have hidden a bad 2.4.0 upload. Mechanism: a bundled `release.sh` (or `make release`) that cleans `dist/`, builds, asserts that every artifact's version matches the tag, uploads without `--skip-existing`, verifies the version on the index, then tags. Once that exists, rows 3 to 5 shrink to "run the script".
- Version source-of-truth check. Hit: a static `version` was added next to `dynamic = ["version"]`. Mechanism: a pre-commit or CI check (for example `validate-pyproject`, or a step that asserts `python -m build --sdist` succeeds) that flags `pyproject.toml` changes to `dynamic` or `[tool.hatch.version]` in release commits.
