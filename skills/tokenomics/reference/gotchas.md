# Tokenomics: delegation gotchas

Problems hit while delegating to Codex in git worktrees and merging the
resulting stacked PRs. Read this before delegating to Codex or using worktrees.

- **Codex in the background waits on stdin.** A backgrounded `codex exec` with no TTY prints "Reading additional input from stdin..." and does nothing. Append `< /dev/null` to the command.
- **Codex can't commit in a git worktree.** Its `workspace-write` sandbox can't reach the git metadata, which lives outside the worktree. Tell it not to commit, and commit yourself after review.
- **Codex leaves locked pytest folders.** Cache and temp folders created in its sandbox get ACLs that block deletion, so `git worktree remove` fails. Have it run `python -m pytest -p no:cacheprovider`. If folders are already locked, the user runs `takeown /f <dir> /r /d y` from an elevated shell, then deletes them.
- **Deleting the base of stacked PRs closes them.** `gh pr merge --delete-branch` on a PR that other PRs target closes those PRs instead of retargeting them, and a closed PR whose base is gone can't be reopened. Merge the base PR without `--delete-branch`. Then retarget each stacked PR with `gh pr edit <n> --base main`, merge `main` into its branch (a plain merge, not a rebase and force-push), and delete the base branch afterwards.
