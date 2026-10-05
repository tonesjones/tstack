## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | Skill assumes version is always in `[project] version` in pyproject.toml, but projects use dynamic versioning (e.g., Hatch reading from `__about__.py`); user had to correct an incorrect version bump. | Update "Bump the version" section to: check pyproject.toml for version configuration (static or dynamic) before deciding where to edit; handle both patterns. | skills/pypi-release/SKILL.md – "Bump the version" |
| 2 | dist/ accumulates stale artifacts from previous releases, causing silent failures when re-uploading (e.g., uploading old 2.3.1 alongside new 2.4.0); user had to intervene. | Add step before build: clear dist/ with `rm -rf dist/` to prevent stale files from interfering with version verification and upload. | skills/pypi-release/SKILL.md – "Build" |
| 3 | `--skip-existing` flag silently skips uploading new versions if old files with the same name exist, masking upload failures; user explained the hazard and corrected the approach. | Update "Upload" section to warn against `--skip-existing` and recommend uploading without it after cleaning dist/; note that the flag skips deterministically only if dist/ is verified clean first. | skills/pypi-release/SKILL.md – "Upload" |

## Rejected

None.

## Backlog

None.

---

Ready to apply these three edits to `skills/pypi-release/SKILL.md`?