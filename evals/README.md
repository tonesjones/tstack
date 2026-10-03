# Skill A/B evals

Measures whether a skill beats the same model without it. Layout follows skill-creator
(`evals.json`, `grading.json`, `aggregate_benchmark.py`).

## deslop
1. `evals/deslop/fixture/setup_case.sh <dir>` builds a throwaway repo: `main` is clean, `feature/restock` adds seeded slop.
2. Run one subagent per (model, arm, repeat) with the repo as its working directory. Same model for both arms.
   - baseline: "Review the changes on this branch vs main and clean up anything that makes the code worse. Do not load or invoke any skill."
   - skill: "Run /deslop on this branch's changes."
3. `python3 evals/deslop/grade.py <dir> --out <run>/grading.json` scores 14 expectations: behavior (`check.py`), 9 seeded removals, 2 keeps, 2 collateral. Doing nothing scores 5/14; the hand-cleaned `reference_inventory.py` scores 14/14.
4. Save each subagent's `total_tokens`/`duration_ms` to `<run>/timing.json`, then aggregate with skill-creator's `python -m scripts.aggregate_benchmark <iteration-dir> --skill-name deslop`.

Layout per iteration: `eval-seeded-slop-restock/<model>-with_skill|without_skill/run-N/`.
