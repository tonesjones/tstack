I wrote the proposals to `proposals.md`. All of them are for `pypi-release`; I didn't change any skill files.

You corrected two things during the release, and the skill's own instructions caused both:

1. **Where to bump the version.** The skill says to edit `[project] version` in `pyproject.toml`, which broke the build because this repo reads the version from another file. I then edited the build config to get past that, which you rejected. The proposed fix tells the skill to find where the version comes from first. If `pyproject.toml` marks the version as dynamic, it edits the file that config points to (`__about__.py` for acme-client). It must never change the build config to get a release through, and should stop and ask if the version source is unclear.
2. **Stale files in `dist/`.**
   - **Build:** run `rm -rf dist/` before building, then check that `dist/` holds only the new version's two files.
   - **Upload:** never use `--skip-existing`. If the index says a file already exists, an old version means `dist/` wasn't cleaned: clear it and rebuild. If it's the version being released, stop and tell you.

The file has the before and after text for each section, plus the complete updated `SKILL.md`.

I'm not proposing anything for `docker-deploy`, since the session didn't use it. I also left out the `pyhton` typo, which was a one-off and not worth a rule.