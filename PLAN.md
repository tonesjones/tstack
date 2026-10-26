# Plan: skill fixes from the transcript pass (1.12.0)

Source: `proposals/gotchas-2026-10-25.md` (PR #25), 211 tstack skill invocations from past transcripts. shutdown-when-done 1.1.0 (PR #12) is also in 1.12.0.

| # | Change | Done when |
|---|---|---|
| 1 | deslop 1.1.0: fetch and diff against `origin/main` | "Get the diff" says to fetch and uses `origin/main` |
| 2 | deslop: read untracked files | "Get the diff" lists `git ls-files --others --exclude-standard` |
| 3 | codex-delegate 1.3.1: the bridge prints non-ASCII answers on a Windows code page | `main()` reconfigures stdout and stderr to UTF-8; a test with `PYTHONIOENCODING=cp1252` fails before and passes after |
| 4 | teach 1.1.2: hedge claims about behavior not read in the session | Teaching rule 2 says so |
| 5 | unslop 1.2.1: self-audit a draft written after the skill loads | Process says so after step 4 |
| 6 | scope-audit 1.1.0: say where the report goes | Output says outside the repo by default, summary only in a plan |
| 7 | shutdown-when-done 1.1.0: power words in non-command text | Gotcha added; a script file's `-e` counts only next to `powershell` or `pwsh`, with tests |
| 8 | codex-delegate: read-only runs give partial test results | Gotcha added |
| 9 | deslop: stop on docs-only diffs | first Guardrails bullet |
| 10 | tokenomics 1.6.1: trigger at each plan phase and after `/compact` | description says so |

## Status

- Done: all items, merged in PR #26 (2026-10-26). PR #25 closed unmerged.
- Next: tag `v1.12.0`, then re-upload the seven changed zips.
- Open decisions: none.
