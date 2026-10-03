# tstack

Personal Claude skills, versioned in one repo and released as uploadable zips.

| Skill | Purpose |
|---|---|
| [unslop](skills/unslop/SKILL.md) | Remove AI writing tells from prose. |
| [deslop](skills/deslop/SKILL.md) | Remove AI-generated slop from a code diff. |
| [technical-writing](skills/technical-writing/SKILL.md) | Layered technical-writing standard. |
| [reflect](skills/reflect/SKILL.md) | Turn a finished task's lessons into skill edits. |
| [tokenomics](skills/tokenomics/SKILL.md) | Route a plan across Opus, Sonnet, and Haiku. |

## Layout

Each skill lives in `skills/<name>/` with a `SKILL.md` and any `reference/`, `references/`, or `scripts/` it needs. The folder name must match the `name` in the frontmatter.

## Agents

`agents/` holds the `worker` (Sonnet) and `grunt` (Haiku) subagents that tokenomics delegates to. Claude Code loads them from `~/.claude/agents/`, so link or copy them there:

```bash
ln -s "$PWD/agents/worker.md" ~/.claude/agents/worker.md
ln -s "$PWD/agents/grunt.md" ~/.claude/agents/grunt.md
```

## Install

1. Download `<name>.zip` from the [latest release](https://github.com/tonesjones/tstack/releases/latest).
2. In the Claude desktop app, open **Settings > Capabilities > Skills** and upload the zip.

## Release

1. Bump the `Version:` line in each changed `SKILL.md` and add an entry to [CHANGELOG.md](CHANGELOG.md).
2. Run `python scripts/validate_skills.py`.
3. Push a tag such as `v1.1.0`. The release workflow validates the skills, zips each one, and attaches the zips to a GitHub release.

## Scripts

- `scripts/validate_skills.py` checks frontmatter, folder names, version lines, and Cursor-specific leftovers.
- `scripts/measure_session.py` totals a Claude Code session's tokens per model and compares the cost with an all-Opus baseline.
