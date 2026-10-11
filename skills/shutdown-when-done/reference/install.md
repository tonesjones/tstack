# Install the shutdown gate

The skill does nothing safe without this hook. `scripts/shutdown_gate.py` runs on
two hook events:

- `PreToolUse` blocks every power command unless the session is armed, and then allows only `shutdown /s /t 600 /c "..."` and `shutdown /a`. It also blocks tool edits to the arm file.
- `UserPromptSubmit` arms the session when you type `/shutdown-when-done 4h`, and disarms it (running `shutdown /a`) on any other message.

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

## Check it

In a new session, without arming, ask Claude to run `shutdown /s /t 600 /c "test"`.
The gate must deny it. Then run `shutdown /a` yourself if anything was scheduled.

## Arm file

The arm lives at `%USERPROFILE%\.claude\shutdown-when-done\arm.json`. It holds the
session id, the deadline (now plus the duration, at most 12h), and an expiry 30
minutes after the deadline to finish saving and start the shutdown. Set
`SHUTDOWN_WHEN_DONE_ARM` to use another path. Delete the file to disarm by hand.
