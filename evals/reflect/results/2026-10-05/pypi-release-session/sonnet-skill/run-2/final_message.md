I wrote the proposals to `proposals.md`. Nothing has been applied to any skill yet; tell me which rows to apply by number.

**Accepted** (all three edit `skills/pypi-release/SKILL.md`):
1. **Version bump:** The skill assumes `pyproject.toml` holds the version, but this repo uses `dynamic` versioning with hatch reading `__about__.py`. The edit tells the agent to check for `dynamic` first and bump the file it points to, never editing build config.
2. **Stale `dist/` files:** The edit adds `rm -rf dist/` before the build. It also says never to use `--skip-existing`, and to treat a "File already exists" error as a reason to stop and investigate.
3. **Closing check:** The edit adds a check before tagging that `dist/` holds only the new version's files and that the built version matches the tag.

**Rejected:**
- The `pyhton` typo was a one-off.
- `docker-deploy` was never used in the session.
- "Don't edit build config blindly" is already folded into row 1.

**Backlog:**
- A release script that cleans `dist/` before building and uploads only the current version.
- A script that finds the version file (for example `hatch version`) instead of relying on prose.