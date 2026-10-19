#!/usr/bin/env python3
"""Stand-in for the Codex CLI. Records each call to $FAKE_CODEX_CALLS and emits `codex exec --json` events."""
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

prompt = sys.stdin.read()
with open(os.environ["FAKE_CODEX_CALLS"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "stdin": prompt}) + "\n")

thread = str(uuid.uuid4())
print(json.dumps({"type": "thread.started", "thread_id": thread}), flush=True)
if os.environ.get("FAKE_CODEX_SLEEP"):
    time.sleep(float(os.environ["FAKE_CODEX_SLEEP"]))

model = argv[argv.index("-m") + 1] if "-m" in argv else "default-model"
if "--ephemeral" not in argv:
    sessions = Path(os.environ["CODEX_HOME"]) / "sessions" / "2026"
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / f"rollout-{thread}.jsonl").write_text(
        json.dumps({"type": "turn_context", "payload": {"model": model}}) + "\n", encoding="utf-8")

print(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}))
lines = int(os.environ.get("FAKE_CODEX_LINES", "3"))
out = Path(argv[argv.index("-o") + 1])
out.write_text("\n".join(f"finding {i}: src/app.py:{i} looks wrong" for i in range(lines)), encoding="utf-8")
