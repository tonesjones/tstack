# Plan: article lessons and changed-skill release notes (1.11.0)

Source: Cloudflare, "Obsessive inference optimization" (fewer turns and tokens beat cheaper tokens).

| # | Change | Done when |
|---|---|---|
| 1 | tokenomics 1.6.0 and agents: subagents read all listed inputs in one parallel batch on their first turn | `worker`, `scout`, `grunt` and the tokenomics brief rule say so |
| 2 | tokenomics: routing log records turns per task | log format line has a `turns` field and the tuning note uses it |
| 3 | tokenomics: review and finding tasks run at high effort | stated in "Main's own costs" and the routing rules |
| 4 | codex-delegate 1.3.0: a timeout resumes the thread with a longer `--timeout` and isn't the Luna to Sol escalation | stated in Route and Run |
| 5 | codex-delegate: a re-review covers only the commits since the last review | stated in Run |
| 6 | codex-delegate: stop background runs you no longer need | stated in Run |
| 7 | Release notes list every skill with its version and whether it changed since the previous tag | `scripts/release_notes.py` prints the table locally; the workflow passes it to `gh release create`; README says to re-upload only changed skills |

## Status

- Done: all items, merged in PR #23 and released as `v1.11.0` (2026-10-22).
- Next: none.
- Open decisions: none.
