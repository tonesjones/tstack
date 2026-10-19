# Tokenomics: delegation gotchas

## Haiku 5.5 subagents

From the move to Haiku 5.5 (2026-10-07) and its migration guide in the
claude-api skill.

- **The `haiku` alias resolves to `claude-haiku-5-5`.** Checked 2026-10-07 in a `grunt` subagent transcript. If a transcript ever shows another Haiku ID, pin `model: claude-haiku-5-5` in the agent files.
- **Refusals have no fallback.** Haiku 5.5 runs safety classifiers that can decline a benign request (categories include `cyber` and `general_harms`), and unlike the larger models it has no server-side fallback. Re-run the package on Sonnet with the same brief; it doesn't count as the task's escalation.
- **Set effort explicitly.** Haiku 5.5 defaults to medium effort. An agent file without `effort:` runs at medium, so `grunt` needs `effort: low` to be the cheap tier.
- **Low effort can stop early.** With a long agent system prompt at low effort, Haiku 5.5 sometimes hands the task back before it's done. If `grunt` reports unfinished work without a reason, re-run it on `scout`; that counts as the escalation.
- **Haiku 5.5 often skips skills.** It tends to do the task itself instead of loading the skill whose description matches. In the 2026-10-07 trigger eval, it loaded the right skill on 37 of 76 prompts, against 69 of 76 for Haiku 4.5 with the same descriptions. If a Haiku package needs a skill, name it in the brief. An agent file's `skills:` field preloads a skill's full text on every spawn, so use it only for a dedicated agent, never for `grunt` or `scout`.
- **The built-in `Explore` wins if the override isn't installed.** Each agent file has to be linked into `~/.claude/agents/`, and agents load at session start. Without `explore.md` there, `Explore` runs on Main's model.

## Claude Code agents and caching

From the Claude Code subagent and prompt-caching docs (checked 2026-10-19).

- **A per-call `model` overrides only the model.** The Agent tool's `model` parameter beats the agent file's `model`, but the file's prompt and `tools` still apply. The `Explore` override keeps its 10-line report, its "stop if this needs judgment" rule, and `Read, Grep, Glob` (no Bash, no MCP). A skill that spawns `Explore` with `model: sonnet` for a thorough or MCP-backed read gets a Sonnet that is told to stop early and can't reach MCP. Spawn `general-purpose` with `model: sonnet` and a read-only instruction instead.
- **A skill or command that names a `model` switches Main's model for that turn.** The next request re-reads the whole conversation uncached. `scripts/validate_skills.py` rejects `model:` in tstack skill frontmatter.
- **Subagent caches last 5 minutes.** A `worker` that waits on a command longer than that (a slow test suite) rewrites its cache on its next turn. If that happens often, add `experimental: {cacheTtl: 1h}` to the agent file (Claude Code 2.1.248 or later). A 1-hour write costs 2x input instead of 1.25x.
- **A fork carries Main's whole context.** Its first request reads Main's cache, but every fork turn re-reads all of it. A 20-turn fork on a 150K-token context re-reads 3M tokens, about $0.60 on Opus 5.5. A fork pays off by keeping bulky tool output out of Main, not by making turns cheaper.

## Codex and git worktrees

Problems hit while delegating to Codex in git worktrees and merging the
resulting stacked PRs. Read this before delegating to Codex or using worktrees.

- **Codex in the background waits on stdin.** A bare `codex exec` run in the background with no TTY prints "Reading additional input from stdin..." and does nothing. Append `< /dev/null` to it. Don't add the redirect to a command that already reads a heredoc or a pipe, because it replaces that input. A backgrounded `python - <<'EOF' ... EOF < /dev/null` got empty stdin, looped on a missing console, and wrote a 1.5 GB error log.
- **Codex can't commit in a git worktree.** Its `workspace-write` sandbox can't reach the git metadata, which lives outside the worktree. Tell it not to commit, and commit yourself after review.
- **Codex leaves locked pytest folders.** Cache and temp folders created in its sandbox get ACLs that block deletion, so `git worktree remove` fails. Have it run `python -m pytest -p no:cacheprovider`. If folders are already locked, the user runs `takeown /f <dir> /r /d y` from an elevated shell, then deletes them.
- **Never link an ignored data folder into a worktree.** On Windows, `git worktree remove` deletes the worktree's ignored contents recursively and follows junctions. In one project each worktree had a `data` junction to the main checkout's ignored `data/`, and removing the worktrees emptied the real folder. Only a 3-day-old backup saved it. Pass subagents absolute paths into the main checkout instead of creating junctions or symlinks. If a link already exists, remove it with `cmd /c rmdir <link>` (no `/s`) before removing the worktree. Never remove a worktree you haven't checked for links.
- **Deleting the base of stacked PRs closes them.** `gh pr merge --delete-branch` on a PR that other PRs target closes those PRs instead of retargeting them, and a closed PR whose base is gone can't be reopened. Squash-merge the base PR without `--delete-branch`. Then retarget each stacked PR with `gh pr edit <n> --base main`, run `git rebase --onto origin/main <old-base-branch> <branch>`, and push with `--force-with-lease`. The squash gives the base's commits new hashes, so a plain merge of `main` replays them and conflicts. Delete the base branch after every stacked PR is retargeted.
