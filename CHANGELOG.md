# Changelog

## 1.1.0 (unreleased)

- Add the `worker` and `grunt` subagents from claude-tokenomics-skill, which is now archived.
- Add `teach`, merged from the pstack plugin's (cursor/plugins) `teach`, `how`, and `why` skills into one skill. Rewritten for Claude: subagent spawns use the Agent tool (`Explore`, Sonnet) in place of Cursor Task slugs and model rules, MCP discovery uses session tool names, the final explanation is written by the main session, and the per-MCP playbooks are condensed into `reference/sources.md`. Behavior changes from the originals: there are no standalone `/how` or `/why` entry points, the structured Why report (What We Found, Competing Hypotheses, Confidence Summary) is replaced by the same confidence tiers worked into the explanation, Why defaults to a narrow git-first pass and widens on demand, and the image-generation step is replaced by an artifact or widget, or an ASCII sketch.
- tokenomics 1.1.0: add a Gotchas section from a session that delegated to Codex in git worktrees. It covers four problems: background `codex exec` waiting on stdin, the Codex sandbox being unable to commit in a worktree, ACL-locked pytest folders blocking `git worktree remove`, and `gh pr merge --delete-branch` closing PRs stacked on the merged branch.
- Note: tokenomics 1.0.0 in this repo matches claude-tokenomics-skill v2.1.0 plus its last uncommitted paragraph ("Inline still means using the right skill").

## 1.0.0 (2026-10-03)

- Import unslop, deslop, technical-writing, reflect, and tokenomics (tokenomics from claude-tokenomics-skill v2.1.0).
- Add a `Version:` line to each `SKILL.md`. Skill contents are otherwise unchanged.
- Add a release workflow that attaches one zip per skill to each `v*` tag.
- Add `scripts/validate_skills.py` and `scripts/measure_session.py`.
