# Routing log

`date | task ID | shape | model | package | result (pass/fix/escalate/inline) | tokens in/out | notes`

2026-10-03 | T1 | touch-up | opus | inline | inline | n/a | cp + scripted version-line insert; diff vs sources shows only the version line; grunt lacks Bash so a copy-by-rewrite would cost more and risk drift
2026-10-03 | T2 | write-heavy | sonnet | P1 | pass | 27.6K total (P1) | checkout pinned v7.0.1 (= latest), no third-party actions, gh CLI release; zips use <name>/ as root
2026-10-03 | T3 | write-heavy | sonnet | P1 | pass | (in P1) | exits 0 on all 5 skills; worker showed non-zero on broken fixture
2026-10-03 | T4 | read+write-heavy | sonnet | P1 | pass | (in P1) | runs on this session; pricing rows cross-checked against pricing.md (Opus 5.5 $4/$5/$8/$0.20/$20)
2026-10-03 | T5 | reasoning | opus | inline | inline | n/a | Action green (run 37157576070, 6s); 5 assets; tokenomics.zip byte-identical to repo, <name>/ root
2026-10-03 | T6 | touch-up | opus | inline | inline | n/a | measure_session.py: actual $1.05 vs all-Opus $1.16, saved $0.11 (9.5%); cold-start loss $0.018; 5m42s; 0 fix / 0 escalate

## Verdict (2026-10-03)
- Routing paid off, slightly: one Sonnet package saved about $0.11 (9.5%) net of a $0.02 cold start, with zero fixes or escalations.
- Next time: same split. Keep file copies inline (grunt has no Bash), and bundle code-to-spec tasks into one worker package early so it runs while Opus does the git work.
- Threshold: no change. Most of the cost is Opus re-reading its own cache, which no routing removes; delegation only pays on code-heavy output like T4.
