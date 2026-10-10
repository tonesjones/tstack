# Changelog

## 1.6.0 (2026-10-10)

- tokenomics 1.4.0: two review ideas borrowed from an Opus/Sonnet/Haiku routing diagram.
  - Step 6: when Main reads a diff, it reviews adversarially, assuming the change is wrong, and writes one line per finding.
  - Step 6: subagents stop and report back at three decision points (an approach the brief didn't settle, the same error twice, a "done when" that can't be met). Main answers with a short brief, not its transcript.

## 1.5.0 (2026-10-07)

- codex-delegate 1.1.1: two Gotchas from using the skill in another project. `resume` runs in the current directory, not the original `--cd` worktree, so `cd` into the worktree first. Codex may use a Python without pytest, so run the tests yourself. A third Gotcha points to the worktree and pytest-folder problems in tokenomics `reference/gotchas.md`. Step 2 no longer names a project-specific command.

## 1.4.0 (2026-10-07)

- tokenomics 1.3.0: Haiku 5.5 replaces Haiku 4.5 as the cheapest tier.
  - Haiku runs at two effort levels: medium (the new `scout` agent and `Explore`) and low (`grunt`). The routing table splits Haiku work between them.
  - Planning and ambiguous tasks stay with Main. Debugging goes to `scout` only with a failing test or reproducer.
  - The delegation gate is per tier. Sonnet keeps about 3K written or 6K read. Haiku delegates when the brief is shorter than doing the work, because Haiku 5.5 reads fresh input for half what Main pays to re-read its cache.
  - Haiku packages are capped at about 60K tokens of reading, to stay under Haiku 5.5's 100K-token price band. This replaces the 200K-context rule.
  - A Haiku safety refusal re-runs on Sonnet and doesn't count as the task's escalation.
  - Briefs name any skill the work needs. In the 2026-10-07 trigger eval, Haiku 5.5 loaded the right skill on 37 of 76 prompts, against 69 for Haiku 4.5.
  - The routing log's `tier` takes `haiku-med` and `haiku-low`.
  - `reference/economics.md` has Haiku 5.5 prices for both bands, the 512-token cache minimum, the tokenizer difference, and reworked examples. `reference/gotchas.md` has a Haiku 5.5 section.
- Add the `scout` agent (Haiku, medium effort, with Bash). `grunt` gets `effort: low` and `Explore` gets `effort: medium`.
- `evals/triggers/run_triggers.py` reads the child's output as UTF-8. It crashed on the Windows cp1252 default.
- `evals/aggregate.py` labels `haiku` results as Haiku 5.5 from 2026-10-07 and as Haiku 4.5 before.

## 1.3.0 (2026-10-06)

- Add scope-audit 1.0.0: audits a drifting project against its goal in ten sections (North Star and conflicting goals, what works, feature audit, AI-generated scope creep, lessons, deletion candidates, current state, shortest path to done, Definition of Done, recommendation A to E). It starts with an inventory of open PRs, branches, and stashes, recommends but never closes or deletes without approval, and says when to re-audit: a new direction, all Definition of Done checks passing, or about every 10 merged PRs. Built from a real project audit; the skill keeps the method, not that project's content.
- Add codex-delegate 1.1.0, imported from the uploaded skill with two changes from a reflect pass:
  - Write tasks list the files the worker may change, and keep plan, status, and instruction files (`PLAN.md`, `STATUS.md`, `CLAUDE.md`) off-limits unless editing them is the task.
  - New Gotchas section: an older `codex` on PATH can shadow the one you installed; set `CODEX_BIN` to pick the right binary.

## 1.2.0 (2026-10-05)

- Apply fixes 1, 3, and 5 from the 2026-10-04 skill audit. Fix 4 (tokenomics) is separate.
  - reflect 1.1.0: runs only on "reflect" or "/reflect". After a task with dead ends or corrections it offers to run instead of starting. The description names skill-creator and skill-review for the cases they own. For a skill kept in a source repo such as tstack, edits go to the repo copy with a version bump and a CHANGELOG entry.
  - unslop 1.1.0: parentheses are fine around a full grammatical unit, which matches technical-writing. Scope says technical docs, commit messages, and PR descriptions get the pattern catalog without the Adding soul section.
  - technical-writing 1.1.0: applies unslop's patterns 1-31 and skips Adding soul for reference docs, commit messages, and PR descriptions. Points at unslop for the filler, plain-word, and active-voice swaps instead of repeating them. Refers to "rule 26" by its name, Abstract metaphor nouns. The description and body say to apply it alongside any doc-creation skill.
  - teach 1.0.1: the description says it doesn't quiz and isn't for research reports, to separate it from learn and deep-research.
- `validate_skills.py` fails when a skill changed since the last `v*` tag and the newest CHANGELOG entry doesn't name its `Version:`, as `<skill> X.Y.Z`. The release workflow fetches full history so the check can run.
- Tighten three skill descriptions using trigger-routing evidence from `evals/triggers/` (2026-10-05). Skill bodies are unchanged.
  - deslop 1.0.1: also triggers on pasted code, not only a branch diff.
  - unslop: also triggers when text "sounds robotic, salesy, like marketing copy, or full of filler and buzzwords".
  - technical-writing: names tutorials, how-to guides, and CONTRIBUTING or setup docs, and excludes product UI strings.
- tokenomics 1.2.0: routing is relative to the main session's model instead of assuming Opus.
  - The delegation gate uses numbers: delegate a task above about 3K tokens written or 6K read.
  - Cache TTLs corrected against the Claude Code docs: 1 hour for the main conversation on a subscription, 5 minutes for subagents, 5 minutes for both on API billing.
  - `routing-log.md` defaults to `~/.claude/routing-log.md`, with `project` and `main model` columns.
  - The Codex and worktree Gotchas move to `reference/gotchas.md`.
- Add an `Explore` agent on Haiku that overrides the built-in Explore, which runs on the main session's model.
- unslop 1.1.0: narrow the Scope line from "any prose you write or edit" to explicit edit or de-AI requests plus prose the user will publish, so the wider description doesn't make it fire on every reply. Add a rule against adding facts, steps, or escalation paths that aren't in the source.
- technical-writing 1.1.0: add review checklist item 9, the same no-invented-content rule. In the 2026-10-05 evals, 11 of 12 runs invented a step.
- Add A/B evals for unslop, technical-writing, and reflect, a second deslop fixture with slop the skill doesn't name, Opus 5.5 cells, a blind LLM rubric grader, and a trigger-routing eval. Results: `evals/results-2026-10-05.md`.

## 1.1.0 (2026-10-04)

- Add the `worker` and `grunt` subagents from claude-tokenomics-skill, which is now archived.
- Add `teach`, merged from the pstack plugin's (cursor/plugins) `teach`, `how`, and `why` skills into one skill. Rewritten for Claude: subagent spawns use the Agent tool (`Explore`, Sonnet) in place of Cursor Task slugs and model rules, MCP discovery uses session tool names, the final explanation is written by the main session, and the per-MCP playbooks are condensed into `reference/sources.md`. Behavior changes from the originals: there are no standalone `/how` or `/why` entry points, the structured Why report (What We Found, Competing Hypotheses, Confidence Summary) is replaced by the same confidence tiers worked into the explanation, Why defaults to a narrow git-first pass and widens on demand, and the image-generation step is replaced by an artifact or widget, or an ASCII sketch.
- tokenomics 1.1.0: add a Gotchas section from a session that delegated to Codex in git worktrees. It covers four problems: background `codex exec` waiting on stdin, the Codex sandbox being unable to commit in a worktree, ACL-locked pytest folders blocking `git worktree remove`, and `gh pr merge --delete-branch` closing PRs stacked on the merged branch.
- Note: tokenomics 1.0.0 in this repo matches claude-tokenomics-skill v2.1.0 plus its last uncommitted paragraph ("Inline still means using the right skill").

## 1.0.0 (2026-10-03)

- Import unslop, deslop, technical-writing, reflect, and tokenomics (tokenomics from claude-tokenomics-skill v2.1.0).
- Add a `Version:` line to each `SKILL.md`. Skill contents are otherwise unchanged.
- Add a release workflow that attaches one zip per skill to each `v*` tag.
- Add `scripts/validate_skills.py` and `scripts/measure_session.py`.
