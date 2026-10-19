---
name: codex-delegate
description: Delegate bounded work to OpenAI Codex (the person's ChatGPT/Codex subscription) through the Codex CLI, with Claude as orchestrator and final reviewer. Routes each task to GPT-6 Luna (bulk, mechanical) or GPT-6.1 Sol (security-sensitive, judgment), runs tasks in parallel, and verifies every answer before using it. Use when asked to "use Codex", "ask Codex", "route to Luna/Sol", "get a second opinion from GPT", "review this diff with Codex", to save Claude usage by offloading work, or to fan out bulk reading, triage, test writing, or review across many files. Works in local and cloud sessions.
---

# Codex delegate

Version: 1.2.0 (2026-10-19)

You orchestrate; Codex does delegated work; you own the result. Everything goes through
`scripts/codex_bridge.py` in this skill's directory (call it `$BRIDGE` below; run it with
`python3`, or `python` on Windows).

## 1. Make sure Codex is ready (once per session)

```bash
python3 $BRIDGE status          # installed? logged in? which model each tier maps to
python3 $BRIDGE setup           # installs @openai/codex if missing; restores login from CODEX_AUTH_JSON / CODEX_ACCESS_TOKEN
```

If setup reports "not logged in", run `python3 $BRIDGE login` **in the background**, read its
output for the verification URL and one-time code, and give both to the person to approve in
their browser. Wait for the command to exit, then run `status` again. Never ask the person to
paste a token or `auth.json` into the chat. Never print, cat, or log `~/.codex/auth.json` or any
`CODEX_*`/`OPENAI_*` secret. Use `--allow-api-key` only if the person asks for API billing.

If OpenAI hosts are blocked (network errors to chatgpt.com, auth.openai.com, or api.openai.com),
tell the person which host failed. In a cloud session they allow it under the environment's
network settings.

## 2. Decide whether to delegate

Codex work bills the person's ChatGPT plan, not Claude usage. What Claude pays for is the brief
you write, the result you read (it stays in context for every later turn), and your review. So
delegate when the brief and the review together are clearly smaller than doing the work yourself.
If the tokenomics skill is routing the plan, it picks which tasks go to Codex. The rules below
still apply.

Delegate when the task is self-contained and its result is cheap to check: bulk reading or
summarizing, triage across many files, first-draft tests, mechanical refactors in an isolated
tree, an independent second opinion on a diff or a finding.

Keep it yourself when it is small, when the context needed is mostly already in your
conversation, when it needs tools only you have (connectors, MCP, GitHub), or when it touches
secrets. Never send credentials, `.env` files, tokens, or data the project marks as private or
not-for-models. Follow the project's own rules first: if a repo has its own model pipeline (for
example a project-specific assessment command), use that instead of this bridge for its data.

## 3. Route

| Tier | Use for |
|---|---|
| `--tier luna` | clear, bounded, low-ambiguity work: summaries, inventories, boilerplate, dead-code and lint-style checks, first-pass triage |
| `--tier sol` | security-sensitive or judgment-heavy work: injection, authn/authz, crypto, SSRF, concurrency, design review, anything critical-severity, any task where a wrong answer is costly |
| `--tier astra` | only when the person names it |

Escalate once: if a Luna answer is vague, contradicts the code, or misses the requested format,
rerun that task on Sol. Don't retry beyond that; do it yourself or report the gap.
`--effort low|medium|high` tunes reasoning depth within a tier.

## 4. Write the task

Codex starts cold. Each prompt must stand alone: the goal, exact file paths or globs, what
"done" means, the output format, and the constraints (read-only, no network, which files are
off-limits). Ask for file:line citations for every claim. For machine-readable results, write a
JSON Schema file and pass `--schema`.

Ask for a compact final message: findings first, one line each with its file:line, no restated
task, no summary of what Codex did. The bridge prints at most 8,000 characters (about 2K tokens)
and saves the full message to the receipt's `final` path, so a long answer costs you only what you
choose to read.

For write tasks, list the files the worker may create or change and say that it must not touch any
other file. Keep the project's plan, status, and instruction files (for example `PLAN.md`,
`STATUS.md`, `CLAUDE.md`) off-limits unless editing them is the task. Parallel workers that each
edit one of these files produce conflicting copies that you then have to merge by hand.

## 5. Run

```bash
# read-only (default): Codex can read files under --cd and run read-only commands
python3 $BRIDGE run --tier luna --cd <repo> --prompt-file task.md

# writes: only into a scratch git worktree, never your working tree
git worktree add ../wt-codex-<task> -b codex/<task>
python3 $BRIDGE run --tier sol --write --cd ../wt-codex-<task> --prompt-file task.md

# follow-up on the same Codex thread (thread id comes from the receipt)
python3 $BRIDGE resume <thread> --prompt "Now add tests for the two cases you found."

# second opinion on a diff with Codex's built-in reviewer (read-only)
python3 $BRIDGE review --tier sol --cd <repo> --base main --prompt "Focus on the auth changes."
```

Stdout is Codex's final message, then a single `--- codex receipt:` JSON line with `exit`,
`thread`, `requested_model`, `model`, `usage`, `commands_run`, `files_changed`, `errors`, `cwd`,
the `final` message path, and the `log` path.

- Tasks over a minute or two: run with Bash `run_in_background` and keep working; you are
  notified when they finish. Independent tasks can run in parallel (keep it to about 4 at once).
- `--write` refuses any directory that isn't a linked git worktree. For a scratch directory
  outside git, pass `--no-worktree-check`.
- `resume` runs in the directory and sandbox its thread started with, so a write task resumes in
  its worktree. It refuses if that directory is gone. Pass `--cd` to choose one.
- `review` takes `--base <branch>`, `--commit <sha>`, or `--uncommitted`. `--prompt` adds custom
  instructions.
- The default timeout is 1800 s (`--timeout`). A timed-out run still prints its receipt, so you
  can `resume` the thread.
- `--max-output 0` prints the whole final message.
- `--ephemeral` skips saving the Codex session, which also disables `resume`.

## 6. Review (always)

Codex output is a draft from a junior colleague, not a fact.

- Before you repeat a claim to the person or act on it, open its file:line and confirm it. Drop
  what doesn't hold. For bulk triage with many findings, check every high-severity one yourself.
  Hand the rest to a Haiku `Explore` or `scout` subagent as a list of claims to confirm or
  refute (mechanical and objective), and read only its verdicts.
- For write runs, read `git -C <worktree> diff` in full, run the project's tests and linters in
  the worktree, then merge or cherry-pick only what you have verified. Remove the worktree when
  done.
- Check the receipt: a `model` different from `requested_model`, non-empty `errors`, or
  unexpected `files_changed` means stop and look at the log.
- A second opinion is the same brief on a second model family. Findings that Codex and Claude
  raise independently are the strongest signal. A finding only one of them raises still needs
  your check.
- Tell the person what was delegated, to which tier, what you kept, and what you rejected.
- If the tokenomics routing log is in use, add one line per run with tier `codex-luna` or
  `codex-sol` and the receipt's `usage`.

## Gotchas

- **An old `codex` on PATH.** The bridge uses the first `codex` it finds on PATH. If `status` shows
  an older version than the one you installed (for example a global install that shadows the npm
  one), set `CODEX_BIN` to the full path of the binary you want and run `status` again.
- **Threads from before bridge 1.2.0 have no recorded directory.** `resume` warns and runs in the
  current directory. Pass `--cd <worktree>` for those, or Codex edits your main checkout. Check
  `files_changed` in the receipt.
- **Codex may lack the test runner.** Codex can use a different Python than the project (on Windows,
  for example, a system `C:\Python3xx` with no pytest), so it may not run the tests. Run them
  yourself in the worktree before merging anything.
- **Worktree and pytest problems.** Codex can't commit in a worktree, and on Windows it can leave
  pytest folders that block `git worktree remove`. See tokenomics `reference/gotchas.md`.
- **`--ephemeral` leaves `model` null.** The bridge reads the receipt's `model` from the Codex
  session file, and `--ephemeral` doesn't write that file. `requested_model` still shows what the
  bridge asked for, not what ran. Leave out `--ephemeral` when you need the tier check.
