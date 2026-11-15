# Plan: fixes from the Fable 5.2 skill audit (1.15.0)

Source: a second review of every skill and agent on 2026-11-14, run on Fable 5.2. The skills were mostly planned and written with Opus 5.5. The Codex subscription is cancelled, so Codex stays off until it is reactivated.

| # | Change | Done when |
|---|---|---|
| 1 | tokenomics 1.8.0: Codex is opt-in | The gate routes to Codex only when the user asks for it in the conversation; the description no longer lists Codex |
| 2 | tokenomics: worktree and stacked-PR gotchas get their own section | `reference/gotchas.md` has a "Git worktrees and stacked PRs" section apart from "Codex"; the Gotchas line in `SKILL.md` names both |
| 3 | tokenomics: rules for Opus as a tier under Fable | Opus has a gate, a routing-table row, a delegate target, a place in the escalation order, and a break-even note in `reference/economics.md` |
| 4 | Agents: `worker` and `scout` can load skills | Both list `Skill` in `tools`; tokenomics step 5 says which agents can load a named skill. Not yet proven: agents load at session start, so a spawn in a new session has to confirm it |
| 5 | tokenomics: narrower inline rule, fewer approval stops | "Files already in context" keeps the plan inline only when no task passes its write gate; step 4 stops only for flagged tasks |
| 6 | shutdown-when-done 1.1.1: never commit to the default branch unattended | Step 3 says to create a branch first when the session is on the default branch |

## Status

- Done: items 1 to 6, merged in PR #30 (2026-11-14).
- Done: tagged and released `v1.15.0` (2026-11-14).
- Next: re-upload the tokenomics and shutdown-when-done zips. Copy shutdown-when-done to `~/.claude/skills/shutdown-when-done` too, because the hook runs from that copy.
- Next: in a new session, spawn `worker` with a brief that names a skill and confirm it loads (item 4). If it doesn't, briefs give the path to the skill's `SKILL.md` instead.
- Next: disable `codex-delegate` in the desktop app's skill settings. Its description still triggers on "save Claude usage".
- Earlier: `v1.14.0` is released (tokenomics 1.7.2). Its tokenomics zip is replaced by the `v1.15.0` one.

## Later (from the same audit)

| Item | Why |
|---|---|
| tokenomics: read the routing log before routing, and count `fix` results | The log is only written. 15 of 26 Sonnet packages needed a fix by Main, none escalated, and `grunt` was never used |
| tokenomics: add `blocked` to the log's result values | It is already used in the log |
| reflect: "up to 5 findings per lens, zero is fine"; add memory and `CLAUDE.md` as routing targets | The minimum of 3 per lens pads the list, and a user preference is rejected as `skill-not-used` |
| unslop: make "Adding soul" opt-in; add signposting and question-then-answer patterns; drop the "patterns 1-33" range | The soul rules create their own tells, and teach bans patterns the catalog lacks |
| scope-audit: a short mode | Ten sections is too much for a small tool |
| Housekeeping: delete the root `routing-log.md`; fix the skill name in the global `CLAUDE.md` (`technical-writing:technical-writing`) | Both are stale |
| Recheck the Haiku and Sonnet share of output tokens | Was due around 2026-11-08 |

## Watch list (2026-10-28 cookbook review)

These items come from Anthropic's claude-cookbooks (`multimodal/using_sub_agents`, `misc/prompt_caching`, `cost_optimization/cost_optimization`). The cookbooks ran on Opus 5, Sonnet 5, and Haiku 4.5. Add an item to tokenomics as a Gotcha only when its trigger shows up in real use.

| # | Item | Trigger |
|---|---|---|
| B | A brief that condenses a spec or policy drops its exceptions. In the cost cookbook, a rule card kept an exclusion but lost its exception, and the cheap pipeline denied a claim it should have approved. Point the agent at the source, or keep the decision on Main. | A subagent decides wrongly because the brief summarized a rule instead of pointing to it |
| C | Main's own costs: images bill at about one token per 28×28 pixel patch and are re-read every turn, so take scaled screenshots or read page text. Compute an aggregate over a big file with a command instead of reading the file. | A session's usage shows screenshots or a large data file read into Main's context |
| D | Spawns of the same agent may share a prompt cache. Identical prefixes can share a cache entry, but concurrent requests hit it only on a best-effort basis. If this holds in Claude Code, a second sequential `grunt` within 5 minutes reads the agent prompt from cache, and "each parallel spawn is another cold start" applies only to parallel spawns. | A transcript shows nonzero `cache_read_input_tokens` on the first request of a second spawn of the same agent |
