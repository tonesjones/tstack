---
name: "scope-audit"
description: "Audit a drifting project's scope against its goal using tests, real runs, and git history. Use after many PRs, AI-written features, or an unclear goal, or when asked for a scope audit, are we drifting, what should we cut, or audit this project. Not for code review or a single PR."
---

# Scope Audit

Version: 1.0.0 (2026-10-06)

Find the smallest path from the project's proven state to its intended outcome.
Recommend what to keep, cut, or park. The audit recommends; the user decides.

## Rules

- Support claims with evidence. Cite file paths with line numbers, PR numbers, commit hashes, test results, or run outputs.
- "Works" means proven by a test or a real run. Docs and PR descriptions show intent, not working behavior.
- Separate reproduced results, historical results, assumptions, and unknowns. State what you could not verify and why.
- Make no code changes during the audit. Do not implement the plan or remove anything.
- Do not close PRs or delete branches or stashes without the user's approval.

## Inventory before writing

Record the audited commit, branch, and any local changes with `git rev-parse HEAD` and `git status --short --branch`.
List local and remote branches with `git branch -a`, stashes with `git stash list`, and open PRs with the forge's PR list.
For GitHub, use `gh pr list --state open` and include every page of results.
If remote or forge access is unavailable, state the gap; do not claim the inventory is complete.

Inspect each item's diff, age, merge status, PR text, and relation to the goal.
Include an inventory table in the document's opening summary: item, evidence, recommendation, reason.
For every stale item, recommend merge, close with a one-line reason, or keep.
For branches and stashes, explain whether merge means recovering useful work and close means deleting the stale item.
These are recommendations only. Preserve all items until the user approves an action.

Read the project description, README, plans, roadmaps, and project instructions.
Compare them with entry points, callers, tests, recent commits, and merged PRs.
Run relevant existing tests and the main user workflow where possible. Record commands, inputs, environment, and outputs.
Check setup from the README and whether advertised features are reachable through the actual user workflow.
Distinguish a fixture or cached result from a fresh run, and a tuned example from an unseen input.

## Output

Create a shareable document: a doc or artifact if the session offers one, otherwise a Markdown file.
Put a short summary and the selected recommendation at the top, followed by the inventory.
Include the audited commit, strongest findings, next actions, and verification limits in the summary.
Then write the following ten sections in this order. Keep each conclusion tied to evidence.

### 1. North Star (one sentence) and Conflicting goals

Write one sentence naming the user, problem, and smallest outcome that solves it.
Research the original request and project description alongside current docs and plans.
List real conflicts in a table: topic, one stated goal, competing goal, decision needed.
Cite both sources by path and line, PR number, or commit hash. State your working interpretation as an assumption.

### 2. What actually works

Test the main path end to end and check the claimed inputs, outputs, setup, and integrations.
List working, partially working, broken, fragile, unwired, and unknown behavior.
Cite test commands and pass/fail/skip counts, run commands and outputs, and relevant code paths.
Scope each result to the inputs and environment tested. Passing unit tests do not prove an integration works.
Mark inaccessible data, missing credentials, and unrun cases as unknown rather than working or broken.

### 3. Feature audit

Trace each feature from its entry point through callers and tests to the user's outcome.
Use this table, with one row per feature:

| Feature | Evidence it works | Used by the North Star? | Keep/cut/park |
|---|---|---|---|

Cite implementation paths and test or run evidence in each row; write "unverified" where needed.
Keep what serves the goal, cut what does not, and park what lacks evidence or a needed prerequisite.
If only part earns its keep, name the retained part and the part to cut or park.
Account for shared code and safeguards before classifying a feature as expendable.

### 4. AI-generated scope creep

Use `git log`, feature diffs, and PR descriptions to trace additions back to requests.
Look for generated "next steps" becoming new plans without a user need, a second product inside the first,
experiments that generate more experiments, premature extensibility, duplicate outputs, and repeated status docs.
Compare the maintenance burden of optimization machinery with its measured benefit.
For each suspected feature nobody asked for, cite its introducing commit or PR and the request history checked.
If request history is incomplete, say "no request found"; do not infer AI authorship from style alone.
Separate necessary safeguards from additions that fail to move the outcome.

### 5. Lessons that changed the assumptions

Compare initial expectations in plans and PRs with tests, experiments, and real runs.
State each original assumption, what the evidence changed, and what that means for scope.
Include what was easier or harder than expected, what was built too early, and what you would omit if starting again.
Cite the original source and the result. Do not treat success on tuned examples or cached answers as proof of general use.

### 6. Deletion candidates

Inspect callers, imports, tests, commands, docs, and dependencies for each proposed removal.
Use a table: candidate and paths, reason, what it saves, what it risks or breaks, confidence.
Quantify saved code, tests, dependencies, maintenance, or repeated reading where evidence permits.
Cite paths, dependency references, commit or PR history, and measured results supporting the expected impact.
Name shared parts that must stay and the regression command that would check a later removal.
Propose removals only; do not perform them during the audit.

### 7. Current state against the goal

Explain what the project would solve if development stopped today, for whom, and under what limits.
Assess goal alignment, core functionality, reliability, unnecessary complexity, and scope creep.
Cite the verified behavior and remaining gaps from earlier sections. Explain any scores or completion estimates.
Separate a convincing demo from usable setup, performance on unseen inputs, and delivery to the intended user.

### 8. Shortest path to done

Write ordered steps containing only removals, decisions, fixes, and validation needed for the North Star.
Put supported simplification first where it reduces the remaining work without losing the core.
Resolve conflicting goals, make setup usable, validate on an unseen case, and prove delivery where those gaps apply.
Tie each step to cited files, PRs, failures, or run outputs and name its completion check.
List parked work separately as later. Do not turn that list into another expansion plan.

### 9. Definition of Done

Write checkable items derived from the North Star and the gaps, not from the full feature list.
For each item, specify the pass condition, how to check it, and the result or artifact to retain.
Cover setup from docs, core regression, unseen inputs, honest unresolved cases, user delivery, and repeatability where relevant.
Use justified thresholds rather than inventing numbers. Cite the goal or evidence behind each check.
Mark each check passed, failed, or unverified. After all pass, recommend bug fixes; new features need a failing check to justify them.

### 10. Final recommendation

Choose exactly one option and repeat it in the opening summary:

- A. Continue as is
- B. Trim and continue
- C. Cut significant scope
- D. Restart smaller
- E. Stop

Choose from proven core value, alignment with the goal, the size of needed cuts, and the remaining path to done.
Distinguish minor trimming from removing whole subsystems. A sound core supports continuing after cuts;
a core that cannot support the smallest goal may justify restarting. No supported path to a worthwhile outcome may justify stopping.
Explain why the chosen option fits and why the nearest alternatives do not, citing the strongest findings.
Do not default to a severe cut just because drift exists. End with the concrete decisions the user needs to make.

## When to re-audit

Re-audit when the project takes a new direction, when every Definition of Done check passes,
or after about ten merged PRs. Compare against the previous North Star and checks before proposing more work.
