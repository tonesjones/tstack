#!/usr/bin/env python3
"""Hook for shutdown-when-done. Reads hook JSON on stdin. Stdlib only.

PreToolUse: denies any shutdown, Stop-Computer, Restart-Computer or powrprof
command unless it is `shutdown /a`, or the session is armed and the command is
exactly `shutdown /s /t 600 /c "..."`. Also denies edits to the arm file and
`arm.py arm` from a tool call, so only the user can arm.

UserPromptSubmit: `/shutdown-when-done <duration>` arms this session and starts
watchdog.py, the backstop for a session that stops before its own shutdown step.
Any other prompt in an armed session disarms it and cancels a pending shutdown.

This script never starts a shutdown. The only command it runs is `shutdown /a`.
The watchdog is the only other process that can, and only once the arm expires.
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
# Squashed form: drop the skill's own names, then every non-letter, so escapes
# (shut^down), quotes, backticks and concatenation ('shut'+'down') can't hide a word.
SAFE_NAMES_RE = re.compile(r"shutdown[-_]when[-_]done|shutdown_gate", re.I)
POWER_WORDS = ("shutdown", "stopcomputer", "restartcomputer", "powrprof", "setsuspendstate",
               "initiatesystemshutdown", "exitwindowsex")
ENCODED_RE = re.compile(r"(?<![\w-])-(?:e|ec|en|enc|enco|encod|encode|encoded|encodedc\w*)(?![\w-])", re.I)
SCRIPT_SUFFIXES = {".bat", ".cmd", ".ps1", ".psm1", ".vbs"}
PREFIX = r"^\s*(?:MSYS_NO_PATHCONV=1\s+)?"
ABORT_RE = re.compile(PREFIX + r'shutdown(?:\.exe)?\s+[/-]a\s*$', re.I)
ALLOWED_RE = re.compile(PREFIX + r'shutdown(?:\.exe)?\s+/s\s+/t\s+600\s+/c\s+"[^"\r\n`$]*"\s*$', re.I)
ARM_CMD_RE = re.compile(r"arm\.py['\"]?\s+arm\b|arm\.json|SHUTDOWN_WHEN_DONE_ARM", re.I)
ARM_PROMPT_RE = re.compile(r"^\s*/shutdown-when-done(?:\s+(\S+))?\s*$", re.I)
IS_WINDOWS = os.name == "nt"
EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", SAFE_NAMES_RE.sub(" ", text).lower())


def has_power_word(text: str) -> bool:
    flat = squash(text)
    return bool(POWER_RE.search(SAFE_NAMES_RE.sub(" ", text))) or any(w in flat for w in POWER_WORDS)


dry_run = armfile.dry_run
log_dry_run = armfile.log_dry_run
WATCHDOG = Path(__file__).resolve().parent / "watchdog.py"
# Detached and outside the hook's job object, so the watchdog outlives the hook and Claude Code.
DETACH_FLAGS = 0x00000008 | 0x00000200 | 0x01000000  # DETACHED_PROCESS | NEW_PROCESS_GROUP | BREAKAWAY_FROM_JOB


def start_watchdog(state: dict, popen=None) -> bool:
    popen = popen or subprocess.Popen  # looked up per call, so tests that block Popen block this too
    args =[sys.executable, str(WATCHDOG), state["session_id"], repr(state["armed_at"])]
    flags = DETACH_FLAGS if IS_WINDOWS else 0
    for attempt in (flags, flags & ~0x01000000):  # retry without breakaway if the job forbids it
        try:
            popen(args, creationflags=attempt, close_fds=True, stdin=subprocess.DEVNULL,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            continue
    return False


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
        if Path(target).suffix.lower() in SCRIPT_SUFFIXES:
            text = json.dumps(tin)
            calls_powershell = re.search(r"powershell|pwsh", squash(text))
            if has_power_word(text) or (calls_powershell and ENCODED_RE.search(text)):
                return deny("script files that contain power commands are blocked.")
        return None

    command = tin.get("command")
    if not isinstance(command, str):
        return None
    if ARM_CMD_RE.search(command):
        return deny("only the user's typed /shutdown-when-done arms it. Use `arm.py status` or `arm.py disarm`.")
    if re.search(r"powershell|pwsh", command, re.I) and ENCODED_RE.search(command):
        return deny("encoded PowerShell commands are blocked while this skill is installed.")
    if not has_power_word(command):
        return None
    if ABORT_RE.match(command):
        return None
    if not armfile.is_armed(session):
        return deny("not armed for this session. Power commands are blocked.")
    if ALLOWED_RE.match(command):
        if dry_run():
            log_dry_run(command)
            armfile.mark_fired()
            return deny("dry run: the shutdown would have been allowed. Nothing was run. Stop here.")
        armfile.mark_fired()
        return None
    return deny('armed, but only `shutdown /s /t 600 /c "<message>"` and `shutdown /a` are allowed, alone on the line.')


def cancel_shutdown(runner=subprocess.run) -> None:
    if not IS_WINDOWS:
        return
    try:
        runner(["shutdown", "/a"], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def user_prompt_submit(event: dict, runner=subprocess.run, popen=None) -> dict | None:
    prompt = event.get("prompt") or ""
    session = event.get("session_id") or ""
    m = ARM_PROMPT_RE.match(prompt)
    if m:
        try:
            state = armfile.arm(session, m.group(1) or "")
            note = "Armed: " + armfile.status(session)
            note += (". Backstop watchdog started: if the session stops early, it starts the 10-minute shutdown when the arm expires."
                     if start_watchdog(state, popen) else
                     ". WARNING: the backstop watchdog failed to start; tell the user the shutdown depends on this session finishing.")
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


def handle(event: dict, runner=subprocess.run, popen=None) -> dict | None:
    name = event.get("hook_event_name")
    if name == "UserPromptSubmit":
        return user_prompt_submit(event, runner, popen)
    if name == "PreToolUse":
        return pre_tool_use(event)
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
        out = handle(event)
    except Exception as e:  # fail closed on anything that looks like a power command
        if has_power_word(raw) or ARM_CMD_RE.search(raw):
            print("shutdown-when-done gate error, blocking: %s" % e, file=sys.stderr)
            return 2
        return 0
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
