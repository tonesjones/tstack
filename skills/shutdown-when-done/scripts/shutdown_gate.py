#!/usr/bin/env python3
"""Hook for shutdown-when-done. Reads hook JSON on stdin. Stdlib only.

PreToolUse: denies any shutdown, Stop-Computer, Restart-Computer or powrprof
command unless it is `shutdown /a`, or the session is armed and the command is
exactly `shutdown /s /t 600 /c "..."`. Also denies edits to the arm file and
`arm.py arm` from a tool call, so only the user can arm.

UserPromptSubmit: `/shutdown-when-done <duration>` arms this session. Any other
prompt in an armed session disarms it and cancels a pending shutdown.

This script never starts a shutdown. The only command it runs is `shutdown /a`.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arm as armfile  # noqa: E402

# "shutdown" as a command word, not part of shutdown-when-done or shutdown_gate.
POWER_RE = re.compile(
    r"(?<![\w-])shutdown(?:\.exe)?(?![\w-])|stop-computer|restart-computer|powrprof|setsuspendstate"
    r"|initiatesystemshutdown|exitwindowsex",
    re.I,
)
ABORT_RE = re.compile(r'^\s*shutdown(?:\.exe)?\s+[/-]a\s*$', re.I)
ALLOWED_RE = re.compile(r'^\s*shutdown(?:\.exe)?\s+/s\s+/t\s+600\s+/c\s+"[^"\r\n`$]*"\s*$', re.I)
ARM_CMD_RE = re.compile(r"arm\.py['\"]?\s+arm\b|arm\.json|SHUTDOWN_WHEN_DONE_ARM", re.I)
ARM_PROMPT_RE = re.compile(r"^\s*/shutdown-when-done(?:\s+(\S+))?\s*$", re.I)
IS_WINDOWS = os.name == "nt"
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def deny(reason: str) -> dict:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "shutdown-when-done: " + reason,
    }}


def _same_file(a: str, b: Path) -> bool:
    try:
        return Path(a).expanduser().resolve() == b.expanduser().resolve()
    except (OSError, ValueError):
        return False


def pre_tool_use(event: dict) -> dict | None:
    tool = event.get("tool_name") or ""
    tin = event.get("tool_input") or {}
    session = event.get("session_id") or ""
    arm_path = armfile.arm_path()

    if tool in EDIT_TOOLS:
        target = tin.get("file_path") or tin.get("notebook_path") or ""
        if target and _same_file(target, arm_path):
            return deny("the arm file can't be edited by a tool. Only the user arms it.")
        return None

    command = tin.get("command")
    if not isinstance(command, str):
        return None
    if ARM_CMD_RE.search(command):
        return deny("only the user's typed /shutdown-when-done arms it. Use `arm.py status` or `arm.py disarm`.")
    if not POWER_RE.search(command):
        return None
    if ABORT_RE.match(command):
        return None
    if not armfile.is_armed(session):
        return deny("not armed for this session. Power commands are blocked.")
    if ALLOWED_RE.match(command):
        return None
    return deny('armed, but only `shutdown /s /t 600 /c "<message>"` and `shutdown /a` are allowed, alone on the line.')


def cancel_shutdown(runner=subprocess.run) -> None:
    if not IS_WINDOWS:
        return
    try:
        runner(["shutdown", "/a"], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def user_prompt_submit(event: dict, runner=subprocess.run) -> dict | None:
    prompt = event.get("prompt") or ""
    session = event.get("session_id") or ""
    m = ARM_PROMPT_RE.match(prompt)
    if m:
        try:
            armfile.arm(session, m.group(1) or "")
            note = "Armed: " + armfile.status(session)
        except ValueError as e:
            armfile.disarm()
            note = "NOT armed (%s). Tell the user and stop; do not run the skill." % e
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "shutdown-when-done " + note}}
    state = armfile.load()
    if state and state.get("session_id") == session:
        armfile.disarm()
        cancel_shutdown(runner)
        return {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                       "additionalContext": "shutdown-when-done disarmed: the user sent a message. Any pending shutdown was cancelled."}}
    return None


def handle(event: dict, runner=subprocess.run) -> dict | None:
    name = event.get("hook_event_name")
    if name == "UserPromptSubmit":
        return user_prompt_submit(event, runner)
    if name == "PreToolUse":
        return pre_tool_use(event)
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
        out = handle(event)
    except Exception as e:  # fail closed on anything that looks like a power command
        if POWER_RE.search(raw) or ARM_CMD_RE.search(raw):
            print("shutdown-when-done gate error, blocking: %s" % e, file=sys.stderr)
            return 2
        return 0
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
