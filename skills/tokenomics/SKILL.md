---
name: tokenomics
description: After a plan is drafted, decide whether delegation pays, map each task to the main session's model or a cheaper tier (Sonnet, Haiku, a fork, or Codex) by difficulty and token shape, bundle and delegate to the matching subagent without breaking the main session's prompt cache, then review results in the main session against acceptance criteria. Use at the end of any planning session, including each new phase of a multi-phase plan and after /compact when more planned work remains, when asked to "route the plan" or run /tokenomics, or when asked to cut token cost or usage.
---

# Tokenomics

Version: 1.7.1 (2026-10-28)

Turn a finished plan into routed, delegated work, then review it. Routing is
relative to whatever model the main session runs (call it **Main**): Main keeps
the hard work, and only tiers *below* Main are worth delegating to.

Tier ladder, strongest first: Fable > Opus > Sonnet > Haiku. Haiku 5.5 runs at
two effort levels: medium (`scout`, `Explore`) and low (`grunt`).
- Main on Fable or Opus: delegate to Sonnet (`worker`) and Haiku (`scout`, `Explore`, `grunt`). On Fable, Opus is also a delegation tier (general-purpose agent with `model: opus`).
- Main on Sonnet: Sonnet-tier work stays inline; only Haiku-tier work is delegated.
- Main on Haiku: run everything inline.

Two routes sit beside the ladder. A **fork** runs on Main's model but keeps its
tool output out of Main's context. **Codex** (the `codex-delegate` skill) bills
the person's ChatGPT plan instead of Claude usage.

Cheaper tiers save money on **output tokens and new input** (file reads, tool
output), not on re-reading context: Main re-reads its warm cache at about the
price Sonnet charges for a cache read ($0.20/MTok on Opus 5.5, $0.25 on Fable
5.1). Every subagent starts cold. Haiku 5.5 is the exception to that cost: it
reads fresh input for half what Opus pays to re-read its cache, so a Haiku
subagent's cost is mostly the brief Main writes and the report Main reads. If
unsure whether delegation pays, see `reference/economics.md`.

## Main's own costs

Every Main turn re-reads the whole context, and Main's output is the most
expensive token in the session. No routing removes that. These habits do:
- Batch independent tool calls into one turn. Each extra turn re-reads everything.
- Read line ranges, cap search results (`head_limit`), and trim command output (`| tail -n 40`, quiet flags). Whatever lands in context is paid for again every later turn.
- Fit effort to the work. Thinking bills as output. Reviews and bug hunts are the exception: run them at `high`. In Cloudflare's code reviewer (2026), moving from medium to high cost about two cents per review and gave 58% more critical or warning findings. On Opus 5.5, Sonnet 5.5, Haiku 5.5, and Fable 5.1 with an API key or a Claude subscription, `/effort` changes keep the cache, so drop to `low` or `medium` for mechanical stretches and raise it for the hard parts. Main can't change its own effort: only the user can type `/effort`, and the desktop app's `set_session_effort` refuses the calling session. So at the start of a mechanical stretch, ask the user in one line to type `/effort low`, and to raise it again before the hard part. Main sets effort directly only on work it starts: the Agent tool's `effort` parameter, or `set_session_effort` on another session. On other models, Bedrock, or Vertex, an effort change re-reads the whole context uncached, so set it once.
- `/compact` between tasks, never mid-task. `/rewind` out of a dead end instead of compacting it.

## 0. Delegation gate
Each tier has its own gate. "New input" means files and tool output not already
in Main's context.
- **Sonnet:** delegate only when the task is expected to **write more than
  about 3K tokens or read more than about 6K tokens of new input**. Below both,
  the cold start costs more than it saves. Main on Fable, whose output costs 5x
  Sonnet's: about 1K written or 3K read.
- **Haiku:** delegate when the brief is clearly shorter than what Main would
  write doing the task inline, or when the task reads new input Main doesn't
  need to keep (searches, bulk reads). The cold start costs about a tenth of a
  cent; Main's brief and review are the real cost.
- **Codex:** delegate when `codex-delegate` is installed and logged in, the
  task is self-contained, its result is cheap to check, and minutes of latency
  are fine. The Claude-side cost is the brief, the printed result, and the review.

Execute the whole plan inline in the main session (if the work is routine, ask
the user to type `/effort low`) and skip steps 2–5 when **any** of these is true:
- No task passes its tier's gate.
- One dependent chain where each step needs the last one's reasoning.
- The files involved are already in context.
- The "done when" can't be checked objectively (a cheap tier risks paying twice).
- No tier exists below Main.

State the decision in one line, e.g. *"Inline: 2 edits, ~1K written, files already loaded."*

Inline still means using the right skill. If a dedicated skill covers the work
(`code-review` for a review, `security-review` for a security pass), invoke it
in the main session instead of doing the work freehand.

## 1. Break the plan into tasks
Each task must be independently executable and include:
- **ID**: T1, T2, …
- **Description**: one or two sentences
- **Inputs**: file paths, line ranges, or outputs of other tasks it needs
- **Touches**: files it will modify
- **Done when**: concrete, checkable acceptance criteria (tests pass, file exists, output matches spec)
- **Depends on**: task IDs, if any
- **Shape**: `read-heavy` (> ~6K new input), `write-heavy` (> ~3K output), `reasoning` (small I/O, hard), or `touch-up` (small change to already-loaded context)
- **Size**: rough tokens read / written, e.g. `20K / 2K`

Write these fields once, in the package brief (step 5). The routing table in
step 4 summarizes them. Don't write them out a third time.

If a task can't be given concrete acceptance criteria, it is still ambiguous and stays with Main.

## 2. Route each task

| Tier | Route here when the task… | Examples |
|---|---|---|
| **Main** (main session) | needs judgment, design choices, ambiguity resolution, planning, cross-cutting reasoning, or security-sensitive decisions; is a `reasoning`/`touch-up` task; or doesn't pass its tier's gate | architecture, planning, ambiguous tasks, hard reviews, tricky debugging, API design, small fixes in loaded files |
| **Main fork** (`subagent_type: "fork"`) | needs Main's context and judgment but produces bulky tool output Main won't need again | a long debug loop, a noisy test-and-fix cycle, a sweep over files Main already discussed |
| **Sonnet** (`worker`) | is well specified, needs real reasoning or non-trivial code, and is `read-heavy` or `write-heavy` | implementing a feature to spec, multi-file refactors, debugging without a reproducer, larger test suites |
| **Haiku medium** (`scout`) | is routine and well specified, and a test or command proves the result | small code changes with a test, bug fixes with a failing test or reproducer, tests written to a spec |
| **Haiku medium** (`Explore`) | is a read-only search with a clear question | codebase searches, repo exploration, "where is X used" |
| **Haiku low** (`grunt`) | is mechanical, follows a pattern given in the brief, and has an objective "done when" | classification, extraction, summarizing, processing search results, formatting, renames, boilerplate, docstrings, simple transforms |
| **Codex** (`codex-delegate`, Luna or Sol) | is self-contained, checkable from its output, can wait minutes, and needs no MCP, connectors, or secrets | bulk reading and triage, first-draft tests in a worktree, a cross-family second opinion on a diff |

Routing rules:
- Never route a task to a tier at or above Main; that tier is Main itself, inline.
- When in doubt between two tiers, choose the cheaper one **only if** the "done when" is fully objective; otherwise choose the stronger one.
- Haiku low vs medium: `grunt` when the brief gives the pattern to apply; `scout` when the agent has to work out where or how (find the call sites, make a failing test pass) or needs Bash.
- Debugging goes to `scout` only when the brief includes a failing test or a reproducer. Without one, "done when" isn't objective: route to Sonnet.
- Any task touching auth, crypto, data deletion, or migrations goes to Sonnet at minimum (Main if Main is Sonnet) and is always flagged for review by Main. Codex takes these only on Sol.
- A fork reads Main's warm cache on its first request, so it has no cold start. It runs at Main's price per token, so it saves context growth, not rate. Use it only when the tool output is large.
- Codex picks Luna or Sol by that skill's table. A flagged task can add a Codex Sol review of its diff (`codex_bridge.py review`): a second model family at almost no Claude cost.
- Split a mixed task rather than routing the whole thing up a tier.
- Keep each Haiku package under about **60K tokens of reading** by Main's count. Above a 100K-token prompt, Haiku 5.5 charges 5x per token, a subagent's prompt grows with every file it reads, and Haiku counts the same text as about 30% more tokens. Split larger packages.
- Don't give Haiku open-ended reasoning: a failed run costs a redo one tier up.
- Review tasks (diff review, security pass, bug hunt) run at `effort: high` on whatever tier they get. Lower effort saves little on them and misses real findings.

## 3. Bundle into packages
Group same-tier tasks that share inputs into **one** subagent call or Codex
run (P1, P2, …), so the cold start is paid once. A package can pass the Sonnet
gate even when its tasks don't individually. Haiku packages stay under the size
cap in step 2. Run packages in parallel only when they are independent (no
dependency between them and no overlap in **Touches**) and latency matters;
each parallel spawn is another cold start.

## 4. Output the routing table
Present it before delegating:

| ID | Task | Shape, size | Tier | Package | Done when | Depends on |
|---|---|---|---|---|---|---|

Keep each cell short. The brief carries the detail. Add a reason only where a
rule overrides the shape (a flagged task, a split). Then add a one-line estimate
of the share of expected **tokens** (not tasks) on each tier.

Stop and wait for the user to approve or adjust the table when any task is
flagged (auth, crypto, deletion, migrations) or more than half the expected
tokens go to subagents, unless the user already said to proceed without
confirmation. Otherwise continue straight to delegation.

## 5. Delegate (cache-safe)
- Never switch the main session's model (`/model`). That cold-starts the whole conversation cache. Cheaper tiers run only as subagents.
- Main-tier tasks run in the main session or a fork; Sonnet packages go to `worker`, Haiku medium packages to `scout`, Haiku low packages to `grunt`, read-only searches to `Explore`, and Codex packages through `codex-delegate`'s bridge in the background. Respect dependencies.
- If `worker`, `scout`, `grunt`, or `Explore` isn't defined in `~/.claude/agents/`, use the general-purpose agent with a model override (`sonnet` / `haiku`), set its effort (`medium` for `scout` and `Explore` work, `low` for `grunt` work), and put the agent's report contract and stop rule (step 6) in the brief. The built-in `Explore` runs on Main's model (or Opus when Main is Fable), so don't use it for cheap searches.
- Briefs carry **pointers, not pastes**: paths, line ranges, each task's description and "done when", constraints. Never paste file contents or the whole plan; Main's output is the most expensive token you can spend. Turns cost more than tokens: every subagent turn re-reads its whole context, and a model that makes fewer calls can halve a task's cost at the same price per token. So list every input up front, and the agent reads them all in one parallel batch on its first turn. For a `general-purpose` fallback, say so in the brief. The agent files already carry the report contract and stop rule, so don't repeat them in briefs to `worker`, `scout`, or `grunt`. If the work needs a skill (`deslop`, `technical-writing`), name it in the brief: Haiku 5.5 often skips a skill it isn't told to load.
- Expect compact reports (the agents are told ≤ 10 lines, starting with DONE, PARTIAL, or BLOCKED). Everything returned is re-read on every later main-session turn.
- Cache TTLs differ (Claude Code docs, checked 2026-10-19): on a Claude subscription within plan usage, the main conversation gets a **1-hour** cache; subagents get **5 minutes**. On an API key, cloud provider, or once usage credits kick in, both get 5 minutes unless `promptCacheTtl` / `subagentPromptCacheTtl` say otherwise. So a subagent idle between turns past 5 minutes pays its cold start again, and on API billing, Main should do its own tasks while a subagent runs rather than idle past 5 minutes.

## 6. Review (Main), proportionate
For each completed task:
- Objective "done when" (tests, lint, build, file exists): run the check yourself and accept on pass. Don't re-read the diff.
- Read the diff only for flagged tasks (auth, crypto, deletion, migrations), spot-checks of Haiku output, and integration points between tasks. When you read one, review adversarially: assume it is wrong and look for the failure, and write one line per finding (`file:line — problem`). No praise, no summary.
- Codex results follow `codex-delegate`'s review step: confirm each claim you will repeat or act on, and read write-run diffs in full.
- Facts in a Haiku report (an `Explore` answer, a `grunt` extraction or summary) get the same check: before you repeat a fact or act on it, read the source it came from (`Explore` gives `path:line`). A wrong fact fails no test, so nothing later catches it. In Anthropic's sub-agents cookbook, Haiku compared mismatched periods and the orchestrator repeated its figures unchecked.
- Mark it **pass**, **fix** (small correction done by Main), or **escalate** (redo one tier up, with the original brief plus the failure reason). The order is Haiku low, Haiku medium, Sonnet, Sonnet at `effort: high` (the Agent tool's `effort` parameter), Main.
- When the subagent should fix its own work and its report arrived less than 5 minutes ago, continue it with SendMessage instead of spawning a new one: it re-reads its own warm cache, and Main skips a second brief. An escalation always starts a fresh agent.
- Subagents stop and report back to Main, rather than guessing, at three decision points: choosing between approaches the brief didn't settle, the same error twice, or "done when" can't be met as written. The `worker`, `scout`, and `grunt` files carry this rule. Put it in the brief only for a general-purpose fallback. Main answers with a short brief, never by handing over its transcript.
- A task escalates at most once. If it fails again, Main does it inline.
- A Haiku run that ends in a safety refusal is re-run on Sonnet with the same brief. Haiku 5.5 has no server-side fallback, and a refusal says nothing about the task's difficulty, so it doesn't count as the task's escalation. Log it as `refusal` in notes.

## 7. Log
Append to `~/.claude/routing-log.md` (create it with the header line below if
it doesn't exist, and replace its header if it lacks a field below), one line
per task, written after the step 6 review so `result` is final. Inline runs get
one line for the whole plan. Use a different path only when the user names one.

`date | project | task ID | shape | main model | tier | package | result (pass/fix/escalate/inline) | tokens in/out | turns | notes`

`tier` is one of `main`, `fork`, `opus` (Main on Fable only), `sonnet`,
`haiku-med`, `haiku-low`, `codex-luna`, or `codex-sol`. `project` is the
repository or working-directory name. Record token usage when the subagent
result or the Codex receipt reports it (one figure per package is fine);
otherwise write `n/a`. `turns` is the number of model calls (tool-use turns) the subagent made, or `n/a`. The session transcripts under `~/.claude/projects/` hold
per-model usage for later cost analysis.

Escalations are the tuning signal: if a (tier, shape) pair keeps escalating, route it higher next time. Turns are the second signal: a pair that passes but takes many turns per task needs fuller inputs in its briefs, or a tier that makes fewer calls. If inline runs were consistently trivial, raise the Sonnet thresholds.

## Gotchas
- Delegating to Codex, working in git worktrees, a Haiku run that refused or stopped early, or another skill that spawns `Explore` with a model override: read `reference/gotchas.md` first.
