I wrote the review to `proposals.md`. It proposes five edits to `skills/pypi-release/SKILL.md`, all based on what went wrong in the acme-client 2.4.0 release. Nothing has been applied yet.

## Accepted

| # | Problem | Proposal | Routing |
|---|---|---|---|
| 1 | The skill says to set `[project] version` in `pyproject.toml`, which breaks builds where the version is listed in `dynamic`. | Find where the version comes from first and bump that file. Only set `[project] version` if the version is already static. | pypi-release § Bump the version |
| 2 | When the build failed, I edited the build config to get it passing, and you had to correct me. | Add a rule: never edit build-backend config to make a release build pass; if bumping the real version source fails, stop and ask. | pypi-release § Bump the version |
| 3 | Old files from the last release were still in `dist/` and got picked up by `dist/*`. | Delete `dist/` (`rm -rf dist/`) before running `python -m build`. | pypi-release § Build |
| 4 | I worked around "File already exists" with `--skip-existing`, which could silently skip a conflicting file for the new version. | Never use `--skip-existing`; treat that error as a sign `dist/` is dirty or the version is already out, and stop to investigate. | pypi-release § Upload |
| 5 | I called the release done based only on twine's "Uploading…" output. | Before upload, check `dist/` holds only the new version's files. After upload, confirm the index serves that version before tagging. | pypi-release § Upload / § Tag |

## Rejected
- **The `pyhton` typo:** a one-off mistake, not something to learn from.
- **acme-client's specific version file path:** that detail may change; row 1 covers the general rule.
- **docker-deploy changes:** that skill wasn't used in this session.
- **Uploading only the new version's files (e.g. `dist/acme_client-2.4.0*`):** rows 3 and 5 already prevent the same problem.
- **Moving the commit step after the build:** wouldn't change what a future session does.

## Backlog
- **A release script:** clean `dist/`, build, check every file's version matches the tag, upload without `--skip-existing`, confirm the index has it, then tag. With that in place, rows 3–5 could shrink to "run the script".
- **A CI or pre-commit check:** flag release commits that change how `pyproject.toml` defines the version.

Tell me which row numbers to apply.