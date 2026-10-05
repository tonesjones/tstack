I've written two proposed edits to `pypi-release` in `proposals.md`. Each comes from something you corrected during the release. I haven't changed any skill files.

1. **Finding the version:** The skill would check `pyproject.toml` first and bump the version wherever it's actually defined. If the version is dynamic, as in this repo, that means bumping it in the file hatch reads (here `src/acme_client/__about__.py`). It would also say never to edit the build config to make a bump work. A build error means the wrong place was edited.
2. **Building and uploading:** The skill would clear `dist/` before building, check that only the new version's two files are there, and upload without `--skip-existing`. If the index says a file already exists, the next step depends on the version:
   - **Older version:** clean `dist/` and rebuild.
   - **Version being released:** stop and tell you.

The file also includes the complete updated `SKILL.md` with both edits applied. I didn't propose any change to `docker-deploy`, since it wasn't used in this session. I also left out the `pyhton` typo, which was a one-off slip.