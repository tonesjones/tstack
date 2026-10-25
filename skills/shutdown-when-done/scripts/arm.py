#!/usr/bin/env python3
"""Arm file for shutdown-when-done. Stdlib only.

Commands:
  arm --session ID --duration 4h   write the arm file (the UserPromptSubmit hook does this; the gate blocks it from Bash)
  disarm                           delete the arm file
  status [--session ID]            print the arm state and time left

The arm file binds one Claude Code session to a deadline. The gate allows the
shutdown command only while the arm matches the session and has not expired.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

MAX_SECONDS = 12 * 3600
# Time after the work deadline to save state and start the 10-minute shutdown.
GRACE_SECONDS = 30 * 60
DURATION_RE = re.compile(r"^\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*$", re.I)


def arm_path() -> Path:
    override = os.environ.get("SHUTDOWN_WHEN_DONE_ARM")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "shutdown-when-done" / "arm.json"


def parse_duration(text: str) -> int:
    """'4h', '90m', '1h30m' -> seconds. Raises ValueError if missing, zero, or over 12h."""
    m = DURATION_RE.match(text or "")
    if not m or not (m.group(1) or m.group(2)):
        raise ValueError("duration required, like 4h, 90m or 1h30m")
    seconds = int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60
    if seconds <= 0:
        raise ValueError("duration must be more than zero")
    if seconds > MAX_SECONDS:
        raise ValueError("duration is capped at 12h")
    return seconds


def arm(session_id: str, duration: str, now: float | None = None) -> dict:
    if not session_id:
        raise ValueError("session id required")
    seconds = parse_duration(duration)
    now = time.time() if now is None else now
    state = {
        "session_id": session_id,
        "armed_at": now,
        "deadline": now + seconds,
        "expires_at": now + seconds + GRACE_SECONDS,
    }
    p = arm_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state), encoding="utf-8")
    return state


def disarm() -> bool:
    try:
        arm_path().unlink()
        return True
    except FileNotFoundError:
        return False


def mark_fired() -> None:
    """Record that a shutdown was started for this arm, so the watchdog doesn't start a second one."""
    state = load()
    if state:
        state["fired"] = True
        arm_path().write_text(json.dumps(state), encoding="utf-8")


def dry_run() -> bool:
    return os.environ.get("SHUTDOWN_WHEN_DONE_DRYRUN", "") not in ("", "0")


def log_dry_run(command: str) -> None:
    try:
        with open(arm_path().with_name("dryrun.log"), "a", encoding="utf-8") as f:
            f.write("%s would have allowed: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), command))
    except OSError:
        pass


def load() -> dict | None:
    try:
        state = json.loads(arm_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return state if isinstance(state, dict) else None


def is_armed(session_id: str, now: float | None = None) -> bool:
    state = load()
    if not state or not session_id or state.get("session_id") != session_id:
        return False
    now = time.time() if now is None else now
    try:
        return float(state["armed_at"]) <= now < float(state["expires_at"])
    except (KeyError, TypeError, ValueError):
        return False


def status(session_id: str | None = None, now: float | None = None) -> str:
    state = load()
    if not state:
        return "disarmed"
    now = time.time() if now is None else now
    if session_id and state.get("session_id") != session_id:
        return "disarmed (armed for another session)"
    try:
        left = float(state["deadline"]) - now
        hard = float(state["expires_at"]) - now
    except (KeyError, TypeError, ValueError):
        return "disarmed (unreadable arm file)"
    if hard <= 0:
        return "disarmed (expired)"
    if left <= 0:
        return "armed, deadline passed: save state and start the shutdown now (%d min of grace left)" % (hard // 60)
    return "armed, %dh%02dm left before the deadline" % (left // 3600, left % 3600 // 60)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("arm")
    a.add_argument("--session", required=True)
    a.add_argument("--duration", required=True)
    sub.add_parser("disarm")
    s = sub.add_parser("status")
    s.add_argument("--session")
    args = ap.parse_args(argv)
    if args.cmd == "arm":
        try:
            arm(args.session, args.duration)
        except ValueError as e:
            print("not armed: %s" % e)
            return 1
        print(status(args.session))
    elif args.cmd == "disarm":
        print("disarmed" if disarm() else "already disarmed")
    else:
        print(status(args.session))
    return 0


if __name__ == "__main__":
    sys.exit(main())
