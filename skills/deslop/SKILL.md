---
name: "deslop"
description: "Remove AI-generated slop from a code diff or pasted code: needless comments, abnormal defensive checks, type-escape casts, deep nesting. Use when asked to deslop or tidy AI-written code, or before opening a PR."
---

# Deslop

Version: 1.1.0 (2026-10-25)

Remove the AI-generated slop a branch introduced, measured against `origin/main`. Leave everything else alone.

## Get the diff

- **Git repo with a shell.** Run `git fetch origin` first. Local `main` lags behind squash merges, so a diff against it shows work that already merged. Use `origin/main`, or the remote default branch from `git symbolic-ref refs/remotes/origin/HEAD` if there is no `main`. Diff from the merge base so uncommitted work is included: `git diff $(git merge-base HEAD origin/main)`. List the touched files with `--name-only`.
- **New files the branch hasn't staged.** `git diff` skips untracked files. Add `git ls-files --others --exclude-standard` to the file list and read those files whole. Skip scratch files the user said to leave out.
- **User names files, a commit, or a range.** Use exactly that scope.
- **No repo.** If the user pasted a diff or code, work on the paste and return the edited code.

Before editing a file, read the whole file, or at least the enclosing functions and their neighbours. Slop is defined relative to the local style, so you need to see the local style.

## Focus areas

- Extra comments that are unnecessary or inconsistent with local style
- Defensive checks or try/catch blocks that are abnormal for trusted code paths
- Casts to `any` used only to bypass type issues
- Deeply nested code that should be simplified with early returns
- Other patterns inconsistent with the file and surrounding codebase

Common forms of "other patterns":

- Comments that narrate the code ("// increment the counter"), restate the function name, or describe the change itself ("// added to fix X", "// new implementation").
- Debug logging and print statements left from development.
- Fallbacks and broad catches that swallow errors the caller should see: `catch { return null }`, `?? ''` on a value that is never null.
- Redundant null, undefined, or type checks on values the type system or the caller already guarantees.
- Unused imports, variables, parameters, or helpers the branch added.
- Single-use wrapper functions that add a layer with no reason.
- Docstrings or type annotations much heavier than the rest of the file.
- Type escapes in other languages: `@ts-ignore`, `as unknown as T`, `!` non-null assertions to quiet the compiler, `# type: ignore`, `cast(Any, ...)`, `interface{}`, needless `unsafe`.

## Guardrails

- If the diff touches no code (only Markdown, prose docs, or plan files), say so in one line and stop. Prose goes to `unslop` or `technical-writing`.
- Keep behavior unchanged unless fixing a clear bug.
- Prefer minimal, focused edits over broad rewrites.
- Touch only lines the branch added or changed. Pre-existing code is out of scope, even when it has the same patterns.
- Don't inline, rename, or remove a function, class, or constant that other modules may import, even when the diff shows one caller.
- Keep defensive checks at trust boundaries: user input, network, file I/O, external APIs, deserialization.
- Keep comments that explain why: a non-obvious constraint, a linked workaround, the reason for an odd choice.
- If the project's typecheck, lint, or tests are cheap and you can find the commands (package scripts, Makefile, CI config), run them after editing. Don't guess commands.
- Keep the final summary concise (1-3 sentences).

## Output

Apply edits in place, or return the edited code when working from a paste. Then the 1-3 sentence summary: what you removed, and what you ran to check it. Mention a kept-on-purpose item only if a reviewer would otherwise flag it.