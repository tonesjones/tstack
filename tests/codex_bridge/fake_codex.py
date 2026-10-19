#!/usr/bin/env python3
"""Stand-in for the Codex CLI. Records each call to $FAKE_CODEX_CALLS and emits `codex exec --json` events.

It enforces the argument rules checked against codex-cli 0.163.0: `exec review` rejects a prompt together
with --base, --commit or --uncommitted, and `exec resume` has no --cd or --sandbox.
"""
import json
import os
import sys
import time
import uuid
from pathlib import Path

argv = sys.argv[1:]
if argv == ["--version"]:
    print("codex-cli 0.0.0-fake")
    sys.exit(0)
if argv[:2] == ["login", "status"]:
    print("Logged in using ChatGPT")
    sys.exit(0)
if argv[:2] == ["exec", "review"] and "-" in argv and {"--base", "--commit", "--uncommitted"} & set(argv):
    sys.exit("error: the argument '--base <BRANCH>' cannot be used with '[PROMPT]'")
if argv[:2] == ["exec", "resume"] and {"-C", "--cd", "-s", "--sandbox", "--add-dir"} & set(argv):
    sys.exit("error: unexpected argument")

prompt = sys.stdin.read()
with open(os.environ["FAKE_CODEX_CALLS"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "stdin": prompt}) + "\n")

if os.environ.get("FAKE_CODEX_DAEMON"):
    # Like a dev server Codex started: outlives Codex in its own session, holding stdout and stderr open.
    import subprocess
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"], start_new_session=True)

thread = argv[-2] if argv[:2] == ["exec", "resume"] else str(uuid.uuid4())
print(json.dumps({"type": "thread.started", "thread_id": thread}), flush=True)
if os.environ.get("FAKE_CODEX_SLEEP"):
    time.sleep(float(os.environ["FAKE_CODEX_SLEEP"]))
    # Before any output, so an orphan that would die of a broken pipe still leaves its mark.
    if os.environ.get("FAKE_CODEX_DONE"):
        Path(os.environ["FAKE_CODEX_DONE"]).write_text("done", encoding="utf-8")

model = argv[argv.index("-m") + 1] if "-m" in argv else "default-model"
if "--ephemeral" not in argv:
    sessions = Path(os.environ["CODEX_HOME"]) / "sessions" / "2026"
    sessions.mkdir(parents=True, exist_ok=True)
    with open(sessions / f"rollout-{thread}.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"type": "turn_context", "payload": {"model": model}}) + "\n")

print(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}))
lines = int(os.environ.get("FAKE_CODEX_LINES", "3"))
out = Path(argv[argv.index("-o") + 1])
out.write_text("\n".join(f"finding {i}: src/app.py:{i} looks wrong" for i in range(lines)), encoding="utf-8")
