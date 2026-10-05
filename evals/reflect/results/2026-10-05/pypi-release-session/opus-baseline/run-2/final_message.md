I've written two proposed edits to `proposals.md`. Both are for the **pypi-release** skill, and each one comes from a correction you made during the session.

1. **Bump the version where the build tool reads it.** The skill currently says to set the version in `pyproject.toml`. That's what caused the build error and then led to the build config being edited. The new step checks `pyproject.toml` first. If the version is listed under `dynamic`, it edits the file hatch reads instead (for acme-client, `src/acme_client/__about__.py`). It also says never to change the build config to make a bump work, and to ask you if it's unclear.
2. **Clear `dist/` before building and upload without `--skip-existing`.**
   - The build step now starts with `rm -rf dist/` and then checks that only the two new-version files are there.
   - The upload step forbids `--skip-existing`, because it would silently skip a same-version file with different contents.
   - If the upload says "File already exists", the agent stops and works out why instead of working around it.

The file also has the complete rewritten `SKILL.md`, ready to use if you accept both. I didn't propose anything for **docker-deploy**, since this session didn't use it. I also left out the `pyhton` typo, which was a one-off slip rather than something to learn from.