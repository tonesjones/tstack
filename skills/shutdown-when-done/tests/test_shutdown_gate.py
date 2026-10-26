"""Tests for arm.py and shutdown_gate.py with synthetic hook JSON. Nothing here runs a shutdown."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import arm  # noqa: E402
import shutdown_gate as gate  # noqa: E402

REAL_RUN = subprocess.run
REAL_POPEN = subprocess.Popen
GATE = Path(__file__).resolve().parent.parent / "scripts" / "shutdown_gate.py"
SID = "session-abc"
ALLOWED = 'shutdown /s /t 600 /c "Claude Code finished."'


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("SHUTDOWN_WHEN_DONE_ARM", str(tmp_path / "arm.json"))
    monkeypatch.delenv("SHUTDOWN_WHEN_DONE_DRYRUN", raising=False)

    def refuse(*a, **k):
        raise AssertionError("a test tried to run a process: %r" % (a,))

    def only_the_hook(args, *a, **k):
        # The one process tests may start: this Python running the hook script.
        if list(args) != [sys.executable, str(GATE)]:
            refuse(args)
        return REAL_POPEN(args, *a, **k)

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", only_the_hook)
    monkeypatch.setattr(gate.os, "system", refuse)
    yield
    arm.disarm()  # a watchdog started by an end-to-end hook run exits once its arm is gone


def bash(command, session=SID):
    return {"hook_event_name": "PreToolUse", "session_id": session,
            "tool_name": "Bash", "tool_input": {"command": command}}


def denied(out):
    return bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "deny"


# arm.py

@pytest.mark.parametrize("text,seconds", [("4h", 14400), ("90m", 5400), ("1h30m", 5400), ("12h", 43200)])
def test_parse_duration(text, seconds):
    assert arm.parse_duration(text) == seconds


@pytest.mark.parametrize("text", ["", "0h", "13h", "12h1m", "4", "four hours", "-1h"])
def test_parse_duration_rejects(text):
    with pytest.raises(ValueError):
        arm.parse_duration(text)


def test_arm_status_disarm():
    arm.arm(SID, "2h", now=1000)
    assert arm.is_armed(SID, now=1001)
    assert not arm.is_armed("other", now=1001)
    assert "1h59m" in arm.status(SID, now=1060)
    assert arm.disarm()
    assert arm.status() == "disarmed"
    assert not arm.disarm()


def test_arm_expires_after_grace():
    arm.arm(SID, "1h", now=0)
    assert arm.is_armed(SID, now=3600 + arm.GRACE_SECONDS - 1)
    assert "deadline passed" in arm.status(SID, now=3601)
    assert not arm.is_armed(SID, now=3600 + arm.GRACE_SECONDS)
    assert not arm.is_armed(SID, now=-1)


def test_corrupt_arm_file_is_disarmed():
    arm.arm_path().write_text("{not json", encoding="utf-8")
    assert not arm.is_armed(SID)


def test_cli(capsys):
    assert arm.main(["arm", "--session", SID, "--duration", "13h"]) == 1
    assert not arm.arm_path().exists()
    assert arm.main(["arm", "--session", SID, "--duration", "3h"]) == 0
    assert arm.main(["status", "--session", SID]) == 0
    assert "armed" in capsys.readouterr().out
    assert arm.main(["disarm"]) == 0


# PreToolUse

@pytest.mark.parametrize("command", [
    ALLOWED,
    "shutdown /s /t 0",
    "shutdown /s /f /t 600",
    "shutdown /r /t 600",
    "shutdown /h",
    "shutdown /l",
    "shutdown.exe /s /t 600",
    "Stop-Computer -Force",
    "Restart-Computer",
    "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
    'echo hi && shutdown /s /t 600 /c "x"',
    'powershell -c "Stop-Computer"',
])
def test_unarmed_blocks_power_commands(command):
    assert denied(gate.pre_tool_use(bash(command)))


@pytest.mark.parametrize("command", [
    "shutdown /s /t 0",
    "shutdown /s /t 600 /f /c \"x\"",
    "shutdown /s /t 60 /c \"x\"",
    "shutdown /r /t 600 /c \"x\"",
    "shutdown /h",
    'shutdown /s /t 600 /c "x" && echo done',
    'shutdown /s /t 600 /c "x"; shutdown /s /t 0',
    'shutdown /s /t 600 /c "$(whoami)"',
    "Stop-Computer",
    "Restart-Computer -Force",
    "rundll32 powrprof.dll,SetSuspendState",
])
def test_armed_allows_only_the_exact_command(command):
    arm.arm(SID, "4h")
    assert denied(gate.pre_tool_use(bash(command)))


def test_armed_allows_cancellable_shutdown():
    arm.arm(SID, "4h")
    assert gate.pre_tool_use(bash(ALLOWED)) is None


def test_arm_for_other_session_blocks():
    arm.arm("someone-else", "4h")
    assert denied(gate.pre_tool_use(bash(ALLOWED)))


def test_expired_arm_blocks(monkeypatch):
    arm.arm(SID, "1h", now=0)
    assert denied(gate.pre_tool_use(bash(ALLOWED)))


@pytest.mark.parametrize("command", ["shutdown /a", "shutdown.exe /a", "  SHUTDOWN /A "])
def test_abort_always_allowed(command):
    assert gate.pre_tool_use(bash(command)) is None


@pytest.mark.parametrize("command", [
    "git status",
    "python skills/shutdown-when-done/scripts/arm.py status",
    "python scripts/arm.py disarm",
    "pytest skills/shutdown-when-done/tests/test_shutdown_gate.py",
    "cat shutdown_gate.py",
])
def test_ordinary_commands_pass(command):
    assert gate.pre_tool_use(bash(command)) is None


@pytest.mark.parametrize("command", [
    "python scripts/arm.py arm --session x --duration 4h",
    "python 'scripts/arm.py' arm --session x --duration 4h",
    "echo {} > ~/.claude/shutdown-when-done/arm.json",
    "SHUTDOWN_WHEN_DONE_ARM=/tmp/a python scripts/arm.py status",
])
def test_tool_cannot_arm(command):
    assert denied(gate.pre_tool_use(bash(command)))


@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
def test_arm_file_edits_blocked(tool):
    ev = {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": tool,
          "tool_input": {"file_path": str(arm.arm_path())}}
    assert denied(gate.pre_tool_use(ev))


def test_other_edits_pass(tmp_path):
    ev = {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "Write",
          "tool_input": {"file_path": str(tmp_path / "HANDOFF.md")}}
    assert gate.pre_tool_use(ev) is None


def test_powershell_tool_checked():
    ev = {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "PowerShell",
          "tool_input": {"command": "Stop-Computer"}}
    assert denied(gate.pre_tool_use(ev))


# UserPromptSubmit

def prompt(text, session=SID):
    return {"hook_event_name": "UserPromptSubmit", "session_id": session, "prompt": text}


def test_typed_command_arms():
    started = []
    out = gate.handle(prompt("/shutdown-when-done 4h"), popen=lambda args, **k: started.append(args))
    note = out["hookSpecificOutput"]["additionalContext"]
    assert "Armed" in note and "watchdog started" in note
    assert arm.is_armed(SID)
    assert started == [[sys.executable, str(gate.WATCHDOG), SID, repr(arm.load()["armed_at"])]]


def test_arming_without_a_fake_popen_is_refused():
    # The fixture blocks Popen, so an arm can't start a real watchdog from a test.
    with pytest.raises(AssertionError, match="tried to run a process"):
        gate.handle(prompt("/shutdown-when-done 4h"))


def test_watchdog_start_failure_warns():
    def broken(args, **k):
        raise OSError("denied")
    out = gate.handle(prompt("/shutdown-when-done 4h"), popen=broken)
    assert "WARNING" in out["hookSpecificOutput"]["additionalContext"]
    assert arm.is_armed(SID)


def test_watchdog_retries_without_job_breakaway(monkeypatch):
    monkeypatch.setattr(gate, "IS_WINDOWS", True)
    flags = []
    def no_breakaway(args, creationflags=0, **k):
        flags.append(creationflags)
        if creationflags & 0x01000000:
            raise OSError("access denied")
    assert gate.start_watchdog({"session_id": SID, "armed_at": 1.0}, popen=no_breakaway)
    assert flags == [gate.DETACH_FLAGS, gate.DETACH_FLAGS & ~0x01000000]


def test_allowed_shutdown_marks_the_arm_fired():
    arm.arm(SID, "4h")
    assert gate.pre_tool_use(bash(ALLOWED)) is None
    assert arm.load()["fired"] is True


@pytest.mark.parametrize("text", ["/shutdown-when-done", "/shutdown-when-done 13h", "/shutdown-when-done soon"])
def test_bad_duration_does_not_arm(text):
    out = gate.handle(prompt(text))
    assert "NOT armed" in out["hookSpecificOutput"]["additionalContext"]
    assert not arm.is_armed(SID)


def test_prompt_mentioning_skill_does_not_arm():
    gate.handle(prompt("what does /shutdown-when-done 4h do?"))
    assert not arm.is_armed(SID)


def test_any_message_disarms_and_cancels(monkeypatch):
    calls = []
    monkeypatch.setattr(gate, "IS_WINDOWS", True)
    arm.arm(SID, "4h")
    out = gate.handle(prompt("I'm back"), runner=lambda cmd, **k: calls.append(cmd))
    assert not arm.arm_path().exists()
    assert calls == [["shutdown", "/a"]]
    assert "disarmed" in out["hookSpecificOutput"]["additionalContext"]


def test_message_in_other_session_leaves_arm(monkeypatch):
    arm.arm(SID, "4h")
    gate.handle(prompt("hello", session="other"), runner=lambda *a, **k: pytest.fail("ran a command"))
    assert arm.is_armed(SID)


# main()

def run_main(monkeypatch, capsys, raw):
    monkeypatch.setattr(sys, "stdin", __import__("io").StringIO(raw))
    code = gate.main()
    return code, capsys.readouterr()


def test_main_denies_as_json(monkeypatch, capsys):
    code, out = run_main(monkeypatch, capsys, json.dumps(bash("shutdown /s /t 0")))
    assert code == 0
    assert json.loads(out.out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_fails_closed_on_bad_json(monkeypatch, capsys):
    code, _ = run_main(monkeypatch, capsys, '{"command": "shutdown /s /t 0"')
    assert code == 2


def test_main_ignores_bad_json_without_power_words(monkeypatch, capsys):
    code, out = run_main(monkeypatch, capsys, "{oops")
    assert code == 0 and out.out == ""


# Bypass attempts

BYPASSES = [
    "shut^down /s /t 0",
    'cmd /c "shut^down /s /t 0"',
    "$c='shut'+'down'; & $c /s /t 0",
    '& ("shut" + "down") /s /t 0',
    "s`hutdown /s /t 0",
    "Stop-Comp`uter",
    "wmic os where primary=true call Win32Shutdown 1",
    "(Get-WmiObject Win32_OperatingSystem).Win32Shutdown(1)",
    'schtasks /create /tn x /tr "shutdown /s /t 0" /sc once /st 03:00',
    "python -c \"import os; os.system('shut'+'down /s /t 0')\"",
    "powershell -EncodedCommand UwB0AG8AcAAtAEMAbwBtAHAAdQB0AGUAcgA=",
    "pwsh -enc UwB0AG8AcAAtAEMAbwBtAHAAdQB0AGUAcgA=",
    "powershell -e UwB0AG8AcAAtAEMAbwBtAHAAdQB0AGUAcgA=",
    'MSYS_NO_PATHCONV=1 shutdown /s /t 0',
]


@pytest.mark.parametrize("command", BYPASSES)
def test_bypasses_blocked_unarmed(command):
    assert denied(gate.pre_tool_use(bash(command)))


@pytest.mark.parametrize("command", BYPASSES)
def test_bypasses_blocked_armed(command):
    arm.arm(SID, "4h")
    assert denied(gate.pre_tool_use(bash(command)))


@pytest.mark.parametrize("command", ['MSYS_NO_PATHCONV=1 shutdown /s /t 600 /c "done"', "MSYS_NO_PATHCONV=1 shutdown /a"])
def test_git_bash_prefix_allowed(command):
    arm.arm(SID, "4h")
    assert gate.pre_tool_use(bash(command)) is None


@pytest.mark.parametrize("name,content", [
    ("off.bat", "shutdown /s /t 0"),
    ("off.cmd", "shut^down /s /t 0"),
    ("off.ps1", "Stop-Computer -Force"),
    ("off.ps1", "powershell -enc AAAA"),
    ("off.ps1", "& ('power'+'shell') -e AAAA"),
    ("off.bat", "pwsh.exe -e AAAA"),
    ("off.vbs", 'CreateObject("WScript.Shell").Run "shutdown /s"'),
])
def test_script_files_with_power_commands_blocked(tmp_path, name, content):
    arm.arm(SID, "4h")
    ev = {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "Write",
          "tool_input": {"file_path": str(tmp_path / name), "content": content}}
    assert denied(gate.pre_tool_use(ev))


def test_edit_into_script_blocked(tmp_path):
    ev = {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "Edit",
          "tool_input": {"file_path": str(tmp_path / "run.ps1"), "old_string": "x", "new_string": "Restart-Computer"}}
    assert denied(gate.pre_tool_use(ev))


@pytest.mark.parametrize("content", ["npm run build", "git cat-file -e HEAD", "grep -E 'a|b' log.txt"])
def test_ordinary_script_file_passes(tmp_path, content):
    ev = {"hook_event_name": "PreToolUse", "session_id": SID, "tool_name": "Write",
          "tool_input": {"file_path": str(tmp_path / "build.ps1"), "content": content}}
    assert gate.pre_tool_use(ev) is None


# Dry run

def test_dry_run_denies_and_logs(monkeypatch):
    monkeypatch.setenv("SHUTDOWN_WHEN_DONE_DRYRUN", "1")
    arm.arm(SID, "4h")
    out = gate.pre_tool_use(bash(ALLOWED))
    assert denied(out) and "dry run" in out["hookSpecificOutput"]["permissionDecisionReason"]
    assert ALLOWED in arm.arm_path().with_name("dryrun.log").read_text(encoding="utf-8")


def test_dry_run_still_allows_abort(monkeypatch):
    monkeypatch.setenv("SHUTDOWN_WHEN_DONE_DRYRUN", "1")
    assert gate.pre_tool_use(bash("shutdown /a")) is None


# End to end: run the hook script as Claude Code does, in a child Python.
# The child only reads JSON and writes JSON. The commands are strings it judges, never runs.

def run_hook(event, env_extra=None):
    import os
    env = dict(os.environ)
    env.update(env_extra or {})
    r = REAL_RUN([sys.executable, str(GATE)], input=json.dumps(event), capture_output=True,
                 text=True, env=env, timeout=30)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else None)


def test_e2e_unarmed_denies():
    code, out = run_hook(bash(ALLOWED))
    assert code == 0 and denied(out)


def test_e2e_arm_then_allow_then_dry_run():
    # Dry run here too, so the real watchdog this starts can only log. The fixture's disarm stops it.
    code, out = run_hook(prompt("/shutdown-when-done 2h"), {"SHUTDOWN_WHEN_DONE_DRYRUN": "1"})
    assert code == 0 and "Armed" in out["hookSpecificOutput"]["additionalContext"]
    assert "watchdog started" in out["hookSpecificOutput"]["additionalContext"]
    code, out = run_hook(bash(ALLOWED))
    assert code == 0 and out is None
    code, out = run_hook(bash(ALLOWED), {"SHUTDOWN_WHEN_DONE_DRYRUN": "1"})
    assert denied(out)
    code, out = run_hook(bash("shutdown /s /t 0"))
    assert denied(out)


def test_e2e_bad_json_fails_closed():
    r = REAL_RUN([sys.executable, str(GATE)], input='{"command":"shut^down /s', capture_output=True,
                 text=True, timeout=30)
    assert r.returncode == 2
