I wrote the proposals to `proposals.md`. I haven't edited any skill; the reflect skill says nothing is applied until you approve rows by number.

**Accepted** (all in `skills/pypi-release/SKILL.md`):
1. **Bump the version where the repo keeps it.** The skill says to set `[project] version`, which broke the build here because `version` is listed in `dynamic`. The edit tells the agent to check for that first and bump the dynamic source file (here `__about__.py`) without touching build config.
2. **Clean `dist/` and drop `--skip-existing`.** Stale files from the last release caused the "File already exists" error. The edit adds `rm -rf dist/` before building and bans `--skip-existing`, since it can silently skip a changed file of the same version.
3. **Verify the upload before tagging.** The agent called the index "correct" from the upload output alone. The edit adds a check that only the new version's two files were uploaded, and tagging comes after it.

**Rejected:**
- The `pyhton` typo is a one-off, so it isn't durable.
- `docker-deploy` wasn't used in the session.
- The "edited config without asking" point is already fixed by row 1, which removes the instruction that caused it.

**Backlog:**
- A release script or Makefile target that cleans `dist/`, builds and runs `twine check`.
- A CI check that the tag matches the built version.

Tell me which row numbers to apply.