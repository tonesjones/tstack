# Routing log

`date | task ID | shape | model | package | result (pass/fix/escalate/inline) | tokens in/out | notes`

2026-10-03 | T1 | touch-up | opus | inline | inline | n/a | cp + scripted version-line insert; diff vs sources shows only the version line; grunt lacks Bash so a copy-by-rewrite would cost more and risk drift
2026-10-03 | T2 | write-heavy | sonnet | P1 | pass | 27.6K total (P1) | checkout pinned v7.0.1 (= latest), no third-party actions, gh CLI release; zips use <name>/ as root
2026-10-03 | T3 | write-heavy | sonnet | P1 | pass | (in P1) | exits 0 on all 5 skills; worker showed non-zero on broken fixture
2026-10-03 | T4 | read+write-heavy | sonnet | P1 | pass | (in P1) | runs on this session; pricing rows cross-checked against pricing.md (Opus 5.5 $4/$5/$8/$0.20/$20)
