# Plan: skill fixes from the transcript pass (1.12.0)

Sources: a review of 14 days of transcripts for items 11 to 13 (tokenomics ran in 15 of 118 sessions, and about 95% of output tokens stayed on Main), and `proposals/gotchas-2026-10-25.md` (PR #25), 211 tstack skill invocations from past transcripts. shutdown-when-done 1.1.0 (PR #12) is also in 1.12.0.

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
| 10 | tokenomics 1.7.0: trigger at each plan phase and after `/compact` | description says so |
| 11 | tokenomics: Main asks the user to type `/effort low`, because `set_session_effort` refuses the calling session | stated in "Main's own costs" and step 0 |
| 12 | tokenomics: the routing log line is written after review, and a stale header is replaced | stated in step 7 |
| 13 | Global CLAUDE.md (outside this repo): use `Explore`, `scout` and `grunt` even when tokenomics doesn't run | rule added to `~/.claude/CLAUDE.md` |

## Status

- Done: items 1 to 10, merged in PR #26 (2026-10-26). PR #25 closed unmerged. Items 11 to 13 are in PR #27; item 10 moved from tokenomics 1.6.1 to 1.7.0 there.
- Done: tagged `v1.12.0` (2026-10-26); stale branches deleted.
- Next: re-upload the seven changed zips (codex-delegate, deslop, scope-audit, shutdown-when-done, teach, tokenomics, unslop).
- Open decisions: whether to narrow the "files already in context" inline trigger to small edits.
- Later: recheck the Haiku and Sonnet share of output tokens around 2026-11-08.
- Done: tokenomics 1.7.1 (2026-10-28 cookbook review), merged in PR #28 and released in `v1.13.0`. Main confirms each fact from a Haiku report before repeating it or acting on it, as it already does for Codex results. A wrong fact repeated from a report fails silently, so this one didn't wait for a real case.
- Next: re-upload the tokenomics zip from `v1.13.0`.

## Watch list (2026-10-28 cookbook review)

These items come from Anthropic's claude-cookbooks (`multimodal/using_sub_agents`, `misc/prompt_caching`, `cost_optimization/cost_optimization`). The cookbooks ran on Opus 5, Sonnet 5, and Haiku 4.5. Add an item to tokenomics as a Gotcha only when its trigger shows up in real use.

| # | Item | Trigger |
|---|---|---|
| B | A brief that condenses a spec or policy drops its exceptions. In the cost cookbook, a rule card kept an exclusion but lost its exception, and the cheap pipeline denied a claim it should have approved. Point the agent at the source, or keep the decision on Main. | A subagent decides wrongly because the brief summarized a rule instead of pointing to it |
| C | Main's own costs: images bill at about one token per 28×28 pixel patch and are re-read every turn, so take scaled screenshots or read page text. Compute an aggregate over a big file with a command instead of reading the file. | A session's usage shows screenshots or a large data file read into Main's context |
| D | Spawns of the same agent may share a prompt cache. Identical prefixes can share a cache entry, but concurrent requests hit it only on a best-effort basis. If this holds in Claude Code, a second sequential `grunt` within 5 minutes reads the agent prompt from cache, and "each parallel spawn is another cold start" applies only to parallel spawns. | A transcript shows nonzero `cache_read_input_tokens` on the first request of a second spawn of the same agent |
