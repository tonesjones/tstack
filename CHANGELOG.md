# Changelog

## 1.1.0 (unreleased)

- Add the `worker` and `grunt` subagents from claude-tokenomics-skill, which is now archived.
- Note: tokenomics 1.0.0 in this repo matches claude-tokenomics-skill v2.1.0 plus its last uncommitted paragraph ("Inline still means using the right skill").

## 1.0.0 (2026-10-03)

- Import unslop, deslop, technical-writing, reflect, and tokenomics (tokenomics from claude-tokenomics-skill v2.1.0).
- Add a `Version:` line to each `SKILL.md`. Skill contents are otherwise unchanged.
- Add a release workflow that attaches one zip per skill to each `v*` tag.
- Add `scripts/validate_skills.py` and `scripts/measure_session.py`.
