---
name: shutdown-when-done
description: On Windows, keep a Claude Code desktop session working after the user goes to sleep, then turn the PC off with a 10-minute cancellable shutdown. Runs only when the user types /shutdown-when-done with a duration, such as /shutdown-when-done 4h. Needs the hook in reference/install.md.
disable-model-invocation: true
---

# Shutdown when done

Version: 1.1.0 (2026-10-25)

The user typed `/shutdown-when-done <duration>` and is going to sleep. Finish the
work in this session, leave it safe to pick up, then turn the PC off. The PC must
never shut down unplanned.

## Rules

- Never run `shutdown /t 0`, `/f`, `/r`, `/g`, `/h`, `/hybrid`, `/l` or `/p`. Never restart, hibernate, sleep or log off.
- The only power commands are `shutdown /s /t 600 /c "<message>"` and `shutdown /a`, each alone in its own command.
- In the Bash tool (Git Bash), prefix both with `MSYS_NO_PATHCONV=1 `, or Git Bash rewrites `/s` and `/a` as paths and the command fails. In PowerShell, run them as written.
- Never run `arm.py arm`, edit the arm file, or change hook settings. The gate blocks these; don't work around it.
- A denied power command is final. Don't retry it in another form. Write the handoff note and stop.
- Any message from the user disarms the skill. The hook runs `shutdown /a`; run it too, then answer the user and do nothing more for this skill.

## 1. Check the arm

The hook adds a line to your context: `shutdown-when-done Armed: ...` or
`shutdown-when-done NOT armed (...)`. If it is missing or says NOT armed, tell the
user why and stop. The duration is required and capped at 12h. Without the hook
nothing is armed; point the user to `reference/install.md`.

Run `python scripts/arm.py status` from this skill's folder at the start, then
between tasks, to see the time left before the deadline.

Warn the user now, before they leave: Windows force-closes other open apps at
shutdown, so they should save and close everything else.

The armed line also says whether the backstop watchdog started. The watchdog
starts the 10-minute shutdown when the arm expires (deadline plus 30 minutes) if
this session never got to step 3. If the line has a WARNING instead, tell the
user that the shutdown depends on this session finishing.

## 2. Work

Carry on with the session's task. Don't start work you can't finish before the
deadline. Commit as you go.

## 3. Finish

When the work is done, or `status` says the deadline passed, run these in order:

1. **Save the work.** Commit, then push. If the push fails or there is no remote, run `git bundle create <repo>-<date>.bundle --all` in the parent folder of the repo.
2. **Write a handoff note.** Write `HANDOFF.md` in the repo root, or next to the bundle: what was done, what is left, what failed, where the work is (branch, PR link, or bundle path), and the deadline hit if it did.
3. **Check for background work.** Confirm no background shells, subagents, builds or test runs are still going. Wait for them or stop them, and note it in the handoff.
4. **Start the shutdown.** Run exactly:

   ```
   MSYS_NO_PATHCONV=1 shutdown /s /t 600 /c "Claude Code finished. Shutting down in 10 minutes. Run shutdown /a to cancel."
   ```

5. Say in one line that the shutdown starts in 10 minutes and `shutdown /a` cancels it. Then stop.

If `/s` or `/a` fails with a path or usage error, Git Bash rewrote it. Rerun with the prefix.

If the deadline arrives mid-task, stop the task and go straight to step 1. Save
state over finishing.

## Gotchas

- **Tool calls fail with "no verdict" from the auto-mode check.** This blocks the
  shutdown command as well as the work, and after 10 such responses in a row the
  turn ends. If the first `arm.py status` call fails this way, tell the user at
  once, while they may still be at the PC: the session may stop early, and only
  the watchdog will shut the PC down, at the arm's expiry. Don't spend the
  remaining attempts retrying work edits. Use them for the handoff note, then the
  shutdown.
