# tstack

Personal Claude skills, versioned in one repo and released as uploadable zips.

| Skill | Purpose |
|---|---|
| [unslop](skills/unslop/SKILL.md) | Remove AI writing tells from prose. |
| [deslop](skills/deslop/SKILL.md) | Remove AI-generated slop from a code diff. |
| [technical-writing](skills/technical-writing/SKILL.md) | Layered technical-writing standard. |
| [reflect](skills/reflect/SKILL.md) | Turn a finished task's lessons into skill edits. |
| [teach](skills/teach/SKILL.md) | Explain what a body of work is, how it works, and why, in plain terms. Folds in pstack's `how` and `why`. |
| [tokenomics](skills/tokenomics/SKILL.md) | Route a plan across Opus, Sonnet, and Haiku. |

## Evidence

`evals/` holds A/B tests that compare each skill against the same model without it; see [evals/README.md](evals/README.md). Latest results: [evals/results-2026-10-05.md](evals/results-2026-10-05.md), with one fixture per skill, Haiku 4.5 and Sonnet 5.5 for every skill, Opus 5.5 for some, 3 runs per cell, and a blind LLM rubric where judgment is needed.

- **unslop:** keep. There's a small gain for Sonnet (blind rubric 67% to 83%), none for Opus, and Haiku still adds new tells.
- **technical-writing:** keep. Structure improves (Sonnet 90% to 100% deterministic, Haiku rubric 67% to 83%). Every arm still invents some steps.
- **reflect:** revise. Every model finds the right learnings with or without the skill. The skill changes format and length, not substance, on this fixture.
- **deslop:** keep for Haiku-tier only. On slop the skill doesn't name, Haiku goes from 81% to 83%. Sonnet and Opus are at 100% without it. The 2026-10-03 gain (74% to 91%) came mostly from slop the skill names.

A trigger-routing test led to tighter descriptions for unslop, technical-writing, and deslop (Haiku routing 84/98 to 90/98, Sonnet 79/98 to 84/98).

## Layout

Each skill lives in `skills/<name>/` with a `SKILL.md` and any `reference/`, `references/`, or `scripts/` it needs. The folder name must match the `name` in the frontmatter.

## Agents

`agents/` holds the `worker` (Sonnet), `grunt` (Haiku), and `Explore` (Haiku) subagents that tokenomics delegates to. `Explore` replaces the built-in Explore agent, which runs on the main session's model. Claude Code loads them from `~/.claude/agents/`, so link or copy them there:

```bash
ln -s "$PWD/agents/worker.md" ~/.claude/agents/worker.md
ln -s "$PWD/agents/grunt.md" ~/.claude/agents/grunt.md
ln -s "$PWD/agents/explore.md" ~/.claude/agents/explore.md
```

## Install

1. Download `<name>.zip` from the [latest release](https://github.com/tonesjones/tstack/releases/latest).
2. In the Claude desktop app, open **Settings > Capabilities > Skills** and upload the zip.

`teach` works best in Claude Code (CLI or the desktop Code tab), where it can read the repo, run git, and spawn subagents. Its `disable-model-invocation` frontmatter means it only runs when you invoke it. Check that the skill upload accepts that key.

## Release

1. Bump the `Version:` line in each changed `SKILL.md` and add an entry to [CHANGELOG.md](CHANGELOG.md).
2. Run `python scripts/validate_skills.py`.
3. Push a tag such as `v1.1.0`. The release workflow validates the skills, zips each one, and attaches the zips to a GitHub release.

## Scripts

- `scripts/validate_skills.py` checks frontmatter, folder names, version lines, and Cursor-specific leftovers. For each skill changed since the last `v*` tag, it also checks that the newest CHANGELOG entry names the skill's version, as `<skill> X.Y.Z`.
- `scripts/measure_session.py` totals a Claude Code session's tokens per model and compares the cost with an all-Opus baseline.
