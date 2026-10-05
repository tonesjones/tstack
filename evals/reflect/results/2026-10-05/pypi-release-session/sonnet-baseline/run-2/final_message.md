I wrote the proposals to `proposals.md`. All of them are edits to `pypi-release`; I proposed nothing for `docker-deploy`, which the session never used.

The three required edits each come from a correction the user made:

1. **Version location:** the skill said to edit `pyproject.toml`, but this repo keeps the version in `src/acme_client/__about__.py` and hatch reads it from there. The edit tells the skill to check `dynamic` and `[tool.hatch.version]` first, and never to change build config to make a bump work.
2. **Clear `dist/` before building:** stale 2.3.1 files made the upload of `dist/*` fail with a 400.
3. **No `--skip-existing`:** it would silently skip a 2.4.0 file already on the index with different contents. The edit tells the skill to find out why "File already exists" appears instead.

I also included an optional fourth edit: confirm after upload that only the new version's files went up. That one came from my own reading, not from a user correction, so skip it if you want the skill short.

The file ends with the full updated `SKILL.md` for convenience.