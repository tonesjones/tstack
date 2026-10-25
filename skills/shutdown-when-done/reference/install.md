# Install the shutdown gate

The skill does nothing safe without this hook. `scripts/shutdown_gate.py` runs on
two hook events:

- `PreToolUse` blocks every power command unless the session is armed, and then allows only `shutdown /s /t 600 /c "..."` and `shutdown /a`. It also blocks tool edits to the arm file.
- `UserPromptSubmit` arms the session when you type `/shutdown-when-done 4h`, and disarms it (running `shutdown /a`) on any other message. Arming also starts `scripts/watchdog.py` as a detached process. If the session stops before its own shutdown step (an error, a tool outage, a turn that ended), the watchdog starts the 10-minute shutdown when the arm expires. It exits without acting if you disarm, re-arm, or Claude already started the shutdown.

Needs Python 3.9+ on PATH as `python`.

## Settings

Add this to `%USERPROFILE%\.claude\settings.json`, merging with any `hooks` you
already have. Replace `<skill>` with the full path to this skill's folder, using
forward slashes, such as `C:/Users/you/.claude/skills/shutdown-when-done`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell|Write|Edit|MultiEdit|NotebookEdit",
        "hooks": [
          { "type": "command", "command": "python \"<skill>/scripts/shutdown_gate.py\"" }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python \"<skill>/scripts/shutdown_gate.py\"" }
        ]
      }
    ]
  }
}
```

Start a new session after editing settings.

## Dry run

Set `SHUTDOWN_WHEN_DONE_DRYRUN=1` in the environment Claude Code starts from, or
under `"env"` in settings. The gate then denies even the allowed shutdown, and
logs it to `dryrun.log` next to the arm file. Everything else works as normal, so
you can run the whole skill and nothing can turn the PC off.

## Test it before trusting it

Do this in Windows Sandbox or a VM first, then once on your PC with dry run on.

1. Install the hook as above and set `SHUTDOWN_WHEN_DONE_DRYRUN=1`. Start a new session.
2. Without arming, ask Claude to run `shutdown /s /t 600 /c "test"`. The gate must deny it.
3. Ask Claude to run `shut^down /s /t 0` and `Stop-Computer`. Both must be denied.
4. Type `/shutdown-when-done 15m`. Claude's reply must mention that it's armed. If it says NOT armed, or nothing about arming, the hook didn't see the typed command. Stop and report it.
5. Ask Claude to run `python scripts/arm.py status`. It must say armed.
6. Give it a small task and let it finish. It must push or bundle, write `HANDOFF.md`, and try the shutdown, which the gate must deny as a dry run. Check `dryrun.log`.
7. Arm again, then send any message. `arm.py status` must say disarmed.
8. Arm with `1m` and confirm a `watchdog.py` python process is running. Send any message; the watchdog must exit within a minute. Arm with `1m` once more and close the session without a reply. About 31 minutes later, `dryrun.log` must show a `watchdog:` line.
9. In the Sandbox or VM only: remove the dry-run setting, start a new session, arm with `15m`, and let it finish. A 10-minute warning must appear. Run `shutdown /a` in a terminal and confirm the warning is cancelled. Repeat, and this time let it shut down.

Use it on your main PC only after these pass. Keep the first real runs short,
with every other app saved and closed.

## Arm file

The arm lives at `%USERPROFILE%\.claude\shutdown-when-done\arm.json`. It holds the
session id, the deadline (now plus the duration, at most 12h), and an expiry 30
minutes after the deadline to finish saving and start the shutdown. Set
`SHUTDOWN_WHEN_DONE_ARM` to use another path. Delete the file to disarm by hand.
