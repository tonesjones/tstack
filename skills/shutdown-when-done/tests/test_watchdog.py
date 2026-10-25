"""Tests for watchdog.py. Fake clock and runner in-process; one real detached run in dry run."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import arm  # noqa: E402
import shutdown_gate as gate  # noqa: E402
import watchdog  # noqa: E402

REAL_RUN = subprocess.run
SID = "session-abc"


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("SHUTDOWN_WHEN_DONE_ARM", str(tmp_path / "arm.json"))
    monkeypatch.delenv("SHUTDOWN_WHEN_DONE_DRYRUN", raising=False)
    yield
    arm.disarm()


class Clock:
    def __init__(self, start):
        self.t = start

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.t += seconds


def armed(expires_in=120.0):
    now = time.time()
    state = {"session_id": SID, "armed_at": now, "deadline": now, "expires_at": now + expires_in}
    arm.arm_path().write_text(json.dumps(state), encoding="utf-8")
    return state


def wait(state, clock, calls, sleep=None, dry_run=False):
    return watchdog.wait_and_fire(SID, state["armed_at"], runner=lambda cmd, **k: calls.append(cmd),
                                  sleep=sleep or clock.sleep, now=clock.now, dry_run=dry_run)


def test_fires_once_at_expiry():
    state, calls = armed(), []
    clock = Clock(state["armed_at"])
    assert wait(state, clock, calls) == "shutdown"
    assert calls == [["shutdown", "/s", "/t", "600", "/c", watchdog.MESSAGE]]
    assert clock.t >= state["expires_at"]
    assert arm.load()["fired"] is True


def test_disarm_while_waiting_stops_it():
    state, calls = armed(), []
    clock = Clock(state["armed_at"])

    def sleep_then_disarm(seconds):
        clock.sleep(seconds)
        arm.disarm()
    assert wait(state, clock, calls, sleep=sleep_then_disarm) == "disarmed"
    assert calls == []


def test_rearm_stops_the_old_watchdog():
    state, calls = armed(), []
    old = dict(state, armed_at=state["armed_at"] - 1)
    assert wait(old, Clock(state["armed_at"]), calls) == "disarmed"
    assert calls == []


def test_claude_already_fired():
    state, calls = armed(), []
    arm.mark_fired()
    assert wait(state, Clock(state["armed_at"]), calls) == "fired-by-claude"
    assert calls == []


def test_dry_run_logs_instead():
    state, calls = armed(), []
    assert wait(state, Clock(state["armed_at"]), calls, dry_run=True) == "dry-run"
    assert calls == []
    assert "watchdog: shutdown /s /t 600" in arm.arm_path().with_name("dryrun.log").read_text(encoding="utf-8")


def test_message_matches_the_gate_rule():
    assert gate.ALLOWED_RE.match('shutdown /s /t 600 /c "%s"' % watchdog.MESSAGE)


def test_real_detached_run_outlives_its_parent(monkeypatch):
    # A short-lived child starts the watchdog the way the hook does, then exits.
    # Dry run, and the arm expires in 2 seconds, so the watchdog only writes a log line.
    monkeypatch.setenv("SHUTDOWN_WHEN_DONE_DRYRUN", "1")
    state = armed(expires_in=2.0)
    child = ("import json, sys; sys.path.insert(0, %r); import shutdown_gate as g; "
             "print(g.start_watchdog(json.loads(open(%r).read())))") % (str(Path(gate.__file__).parent), str(arm.arm_path()))
    r = REAL_RUN([sys.executable, "-c", child], capture_output=True, text=True, env=dict(os.environ), timeout=30)
    assert r.stdout.strip() == "True", r.stderr
    log = arm.arm_path().with_name("dryrun.log")
    for _ in range(40):
        if log.exists():
            break
        time.sleep(0.5)
    assert "watchdog:" in log.read_text(encoding="utf-8")
    assert arm.load()["fired"] is True and arm.load()["armed_at"] == state["armed_at"]
