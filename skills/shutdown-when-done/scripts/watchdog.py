#!/usr/bin/env python3
"""Backstop for shutdown-when-done. Stdlib only.

Usage: watchdog.py SESSION_ID ARMED_AT

The arming hook starts this as a detached process. It sleeps until the arm
expires, then starts the 10-minute shutdown if the same arm is still in place
and nothing has fired it. That covers a session that stopped early (an error,
a tool outage, a turn that ended) and never reached its own shutdown step.

It exits without doing anything if the user disarmed (any message deletes the
arm file), re-armed (a new armed_at), or Claude already started the shutdown
(the gate marks the arm as fired). In dry run it logs instead.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arm as armfile  # noqa: E402

MESSAGE = ("Claude Code stopped before finishing. Shutting down in 10 minutes. "
           "Run shutdown /a to cancel.")
POLL_SECONDS = 60


def same_arm(state: dict | None, session_id: str, armed_at: float) -> bool:
    return bool(state) and state.get("session_id") == session_id and float(state.get("armed_at", -1)) == armed_at


def wait_and_fire(session_id: str, armed_at: float, runner=subprocess.run, sleep=time.sleep, now=time.time,
                  dry_run=None) -> str:
    """Returns what happened: 'disarmed', 'fired-by-claude', 'dry-run' or 'shutdown'."""
    dry_run = armfile.dry_run() if dry_run is None else dry_run
    while True:
        state = armfile.load()
        if not same_arm(state, session_id, armed_at):
            return "disarmed"
        if state.get("fired"):
            return "fired-by-claude"
        left = float(state["expires_at"]) - now()
        if left <= 0:
            break
        sleep(min(POLL_SECONDS, left))
    armfile.mark_fired()
    command = ["shutdown", "/s", "/t", "600", "/c", MESSAGE]
    if dry_run:
        armfile.log_dry_run("watchdog: " + " ".join(command))
        return "dry-run"
    runner(command, capture_output=True, timeout=30)
    return "shutdown"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    wait_and_fire(argv[0], float(argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
