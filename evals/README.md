# Skill A/B evals

Measures whether a skill beats the same model without it. Layout follows skill-creator
(`evals.json`, `grading.json`, `aggregate_benchmark.py`).

## deslop
1. `evals/deslop/fixture/setup_case.sh <dir>` builds a throwaway repo: `main` is clean, `feature/restock` adds seeded slop.
2. Run one subagent per (model, arm, repeat) with the repo as its working directory. Same model for both arms.
   - baseline: "Review the changes on this branch vs main and clean up anything that makes the code worse. Do not load or invoke any skill."
   - skill: "Run /deslop on this branch's changes."
3. `python3 evals/deslop/grade.py <dir> --out <run>/grading.json` scores 14 expectations: behavior (the harness's own `check.py`, never the repo copy), 9 seeded removals, 2 keeps, 2 collateral. `setup_case.sh` no longer copies `check.py` into the run repo. Doing nothing scores 5/14; the hand-cleaned `reference_inventory.py` scores 14/14.
4. Save each subagent's `total_tokens`/`duration_ms` to `<run>/timing.json`, then aggregate with skill-creator's `python -m scripts.aggregate_benchmark <iteration-dir> --skill-name deslop`.

Layout per iteration: `eval-seeded-slop-restock/<model>-with_skill|without_skill/run-N/`.

## 2026-10-05 harness (all phase-1 skills)

`run_ab.py <skill> --models haiku,sonnet[,opus] [--case NAME] --work DIR` runs each (model, arm, repeat) as an isolated `claude -p` child with a throwaway `HOME`. It writes `evals/<skill>/results/<date>/<case>/<model>-<arm>/run-N/` with outputs, `final_message.md`, `timing.json`, and `grading.json`, and it is idempotent, so rerun the same command to resume. The cases are `unslop/build-times-post`, `technical-writing/cert-rotation-runbook`, `reflect/pypi-release-session`, and `deslop/signups`.

- `llm_grade.py <skill> --all <results_dir>`: blind rubric grading (`<skill>/rubric.md`). The grader never sees the arm or model. reflect's rubric runs inside `reflect/grade.py --llm sonnet`.
- `aggregate.py <skill>`: markdown tables, with deterministic and LLM scores reported separately.
- `triggers/run_triggers.py --model haiku --label current [--skills-dir DIR] [--reps N]`: trigger routing over `triggers/prompts.json`.

Results and caveats: [results-2026-10-05.md](results-2026-10-05.md).
