I reviewed the session and wrote three proposed edits to the `pypi-release` skill in `proposals.md`. I haven't applied anything; tell me which row numbers to make.

| # | Problem | Proposal | Where in the skill |
|---|---|---|---|
| 1 | The skill says to set the version in `pyproject.toml`. In this repo that broke the build and led to rewriting the build config. | First check whether `version` is listed as `dynamic`. If it is, bump the file hatch reads it from (here `__about__.py`), and never edit the build config to make the bump work. | Bump the version |
| 2 | Old files from 2.3.1 were still in `dist/` and got uploaded along with 2.4.0. | Clear `dist/` before building. | Build |
| 3 | `--skip-existing` was used to get past "File already exists". It would also skip a 2.4.0 file with different contents without saying so. | Never use `--skip-existing`; find out why the file already exists and fix that instead. | Upload |

**Rejected:**
- The `pyhton` typo: too trivial to keep.
- A general "follow the skill" rule: rows 1 and 3 already cover it.
- Building and uploading before committing and tagging: only one weak signal, and it caused no failure.
- Changes to `docker-deploy`: that skill wasn't used this session.

**One open question:** the session pushed only the tag, so the `release: v2.4.0` commit isn't on the remote `main` branch. If this repo expects release commits on `main` (pushed directly or through a PR), the Tag step should say so. I left it out because the session doesn't show which.

**Backlog (better handled by a script than by skill text):**
- A check before upload that fails if any file in `dist/` isn't for the version being released.
- A small script that reports which file holds the version, for the bump step to call.