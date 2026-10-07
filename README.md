# tstack

Personal Claude skills, versioned in one repo and released as uploadable zips.

| Skill | Purpose |
|---|---|
| [unslop](skills/unslop/SKILL.md) | Remove AI writing tells from prose. |
| [deslop](skills/deslop/SKILL.md) | Remove AI-generated slop from a code diff. |
| [technical-writing](skills/technical-writing/SKILL.md) | Layered technical-writing standard. |
| [reflect](skills/reflect/SKILL.md) | Turn a finished task's lessons into skill edits. Runs only when you ask. |
| [teach](skills/teach/SKILL.md) | Explain what a body of work is, how it works, and why, in plain terms. Folds in pstack's `how` and `why`. |
| [tokenomics](skills/tokenomics/SKILL.md) | Route a plan's tasks to the main session's model or a cheaper tier. |
| [scope-audit](skills/scope-audit/SKILL.md) | Audit a drifting project against its goal and recommend what to keep, cut, or park. |
| [codex-delegate](skills/codex-delegate/SKILL.md) | Hand bounded tasks to the Codex CLI (Luna or Sol tier) and review the results. |

## Evidence

`evals/` holds A/B tests that compare each skill against the same model without it; see [evals/README.md](evals/README.md). Latest results: [evals/results-2026-10-05.md](evals/results-2026-10-05.md), with one fixture per skill, Haiku 4.5 and Sonnet 5.5 for every skill, Opus 5.5 for some, 3 runs per cell, and a blind LLM rubric where judgment is needed. Every Haiku figure below comes from Haiku 4.5. The A/B tests haven't been re-run on Haiku 5.5.

- **unslop:** keep. There's a small gain for Sonnet (blind rubric 67% to 83%), none for Opus, and Haiku still adds new tells.
- **technical-writing:** keep. Structure improves (Sonnet 90% to 100% deterministic, Haiku rubric 67% to 83%). Every arm still invents some steps.
- **reflect:** revise. Every model finds the right learnings with or without the skill. The skill changes format and length, not substance, on this fixture.
- **deslop:** keep for Haiku-tier only. On slop the skill doesn't name, Haiku goes from 81% to 83%. Sonnet and Opus are at 100% without it. The 2026-10-03 gain (74% to 91%) came mostly from slop the skill names.

A trigger-routing test led to tighter descriptions for unslop, technical-writing, and deslop (Haiku routing 84/98 to 90/98, Sonnet 79/98 to 84/98).

A 2026-10-07 re-run of the trigger test on Haiku 5.5, with the current descriptions and 2 runs per prompt, loaded the right skill on 37 of 76 prompts. Haiku 4.5 managed 69 of the same 76. Haiku 5.5 mostly did the task itself instead of loading a skill. It hit deslop on 9/16, reflect 7/18, technical-writing 4/16, and unslop 6/14, and it correctly loaded nothing on 11/12 negatives. Results: `evals/triggers/results/2026-10-07/`.

## Layout

Each skill lives in `skills/<name>/` with a `SKILL.md` and any `reference/`, `references/`, or `scripts/` it needs. The folder name must match the `name` in the frontmatter.

## Agents

`agents/` holds the subagents that tokenomics delegates to:

| Agent | Model | Effort | Work |
|---|---|---|---|
| `worker` | Sonnet | medium | Implementation to a spec, multi-file refactors |
| `scout` | Haiku 5.5 | medium | Small changes a test or command proves |
| `Explore` | Haiku 5.5 | medium | Read-only searches |
| `grunt` | Haiku 5.5 | low | Mechanical work that follows a pattern from the brief |

`Explore` replaces the built-in Explore agent, which runs on the main session's model. Claude Code loads agents from `~/.claude/agents/` when a session starts. Link or copy them there, then start a new session:

```bash
ln -s "$PWD/agents/worker.md" ~/.claude/agents/worker.md
ln -s "$PWD/agents/scout.md" ~/.claude/agents/scout.md
ln -s "$PWD/agents/grunt.md" ~/.claude/agents/grunt.md
ln -s "$PWD/agents/explore.md" ~/.claude/agents/explore.md
```

## Install

1. Download `<name>.zip` from the [latest release](https://github.com/tonesjones/tstack/releases/latest).
2. In the Claude desktop app, open **Settings > Capabilities > Skills** and upload the zip.

Each uploaded skill updates separately. After a release, upload every changed skill's zip from the same tag, so the installed set matches one version of this repo.

`codex-delegate` needs Python 3.9+ and the Codex CLI with a ChatGPT login. Its `scripts/codex_bridge.py` installs the CLI if it is missing; run `python3 scripts/codex_bridge.py status` to check.

`teach` works best in Claude Code (CLI or the desktop Code tab), where it can read the repo, run git, and spawn subagents. Its `disable-model-invocation` frontmatter means it only runs when you invoke it. Check that the skill upload accepts that key.

## Release

1. Bump the `Version:` line in each changed `SKILL.md` and add an entry to [CHANGELOG.md](CHANGELOG.md) that names each one as `<skill> X.Y.Z`.
2. Run `python scripts/validate_skills.py`.
3. Push a tag such as `v1.3.0`. The release workflow validates the skills, zips each one, and attaches the zips to a GitHub release.

## Scripts

- `scripts/validate_skills.py` checks frontmatter, folder names, version lines, and Cursor-specific leftovers. For each skill changed since the last `v*` tag, it also checks that the newest CHANGELOG entry names the skill's version, as `<skill> X.Y.Z`.
- `scripts/measure_session.py` totals a Claude Code session's tokens per model and compares the cost with an all-Opus baseline.
