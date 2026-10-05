#!/usr/bin/env python3
"""Trigger-routing eval for the phase-1 skills. Installs unslop, technical-writing, deslop, and reflect into a
throwaway project, gives the child only the Skill tool, sends each prompt, and records which skill it loads first
(the child is stopped at the first Skill call). Built-in Claude Code skills stay visible as competitors.

Usage: run_triggers.py --model haiku --label current [--skills-dir skills] [--jobs 6] [--ids u1,t3]
Writes evals/triggers/results/<date>/<label>-<model>.json.
"""
import argparse
import json
import os
import shutil
import subprocess
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PHASE1 = ["unslop", "technical-writing", "deslop", "reflect"]


def env_for(home):
    env = {k: v for k, v in os.environ.items() if k not in (
        "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_REMOTE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION", "CLAUDECODE")}
    env.update(HOME=str(home), CLAUDE_CODE_SYNC_SKILLS="0", CLAUDE_CODE_SYNC_PLUGINS="0",
               CLAUDE_CODE_POST_TURN_MEMORY="0")
    return env


def one(p, model, skills_dir):
    base = Path(tempfile.mkdtemp(prefix="trig-"))
    work, home = base / "work", base / "home"
    home.mkdir()
    for s in PHASE1:
        shutil.copytree(skills_dir / s, work / ".claude" / "skills" / s)
    t0 = time.time()
    proc = subprocess.Popen(["claude", "-p", p["prompt"], "--model", model, "--output-format", "stream-json",
                             "--verbose", "--tools", "Skill", "--permission-mode", "bypassPermissions",
                             "--no-session-persistence"],
                            cwd=work, env=env_for(home), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL, text=True)
    called, err, said = [], None, ""
    try:
        for line in proc.stdout:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") == "assistant":
                for c in d["message"].get("content", []):
                    if c.get("type") == "tool_use" and c.get("name") == "Skill":
                        called.append(c["input"].get("skill"))
                    elif c.get("type") == "text":
                        said += c["text"]
            elif d.get("type") == "user" and not called:
                # A "/name" prompt expands the skill directly, with no Skill tool call.
                content = d["message"].get("content")
                texts = [content] if isinstance(content, str) else [
                    c.get("text", "") for c in content or [] if isinstance(c, dict)]
                for t in texts:
                    m = re.search(r"Base directory for this skill: \S*/skills/([\w-]+)", t or "")
                    if m:
                        called.append(m.group(1))
            if d.get("type") == "result":
                if d.get("is_error") or d.get("terminal_reason") == "api_error":
                    err = str(d.get("result"))[:200]
                break
            if called:
                break
            if time.time() - t0 > 240:
                err = "timeout"
                break
    finally:
        proc.kill()
        proc.wait()
        shutil.rmtree(base, ignore_errors=True)
    first = next((c.split(":")[-1] for c in called if c and c.split(":")[-1] in PHASE1), None)
    other = [c for c in called if c and c.split(":")[-1] not in PHASE1]
    got = first or "none"
    return {"id": p["id"], "prompt": p["prompt"], "ok": p["ok"], "tag": p.get("tag"), "got": got,
            "other_skills": other, "pass": got in p["ok"], "error": err, "seconds": round(time.time() - t0, 1), "said": said[:240]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--label", default="current")
    ap.add_argument("--skills-dir", default=str(ROOT / "skills"))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--ids")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--date", default="2026-10-05")
    a = ap.parse_args()
    prompts = json.load(open(HERE / "prompts.json"))["prompts"]
    if a.ids:
        prompts = [p for p in prompts if p["id"] in a.ids.split(",")]
    with ThreadPoolExecutor(a.jobs) as ex:
        rows = list(ex.map(lambda pr: dict(one(pr[0], a.model, Path(a.skills_dir)), rep=pr[1]),
                           [(p, k) for k in range(1, a.reps + 1) for p in prompts]))
    out = HERE / "results" / a.date / ("%s-%s.json" % (a.label, a.model))
    out.parent.mkdir(parents=True, exist_ok=True)
    old = {(r["id"], r.get("rep", 1)): r for r in json.load(open(out))["rows"]} if out.exists() else {}
    old.update({(r["id"], r["rep"]): r for r in rows})
    rows = sorted(old.values(), key=lambda r: (r["id"], r["rep"]))
    json.dump({"model": a.model, "label": a.label, "rows": rows}, open(out, "w"), indent=1)
    for r in rows:
        print("%s %-3s #%d got=%-17s ok=%s %s%s" % ("PASS" if r["pass"] else "FAIL", r["id"], r["rep"], r["got"], r["ok"],
                                              r["tag"] or "", " ERR " + r["error"] if r["error"] else ""))
    errs = sum(1 for r in rows if r["error"])
    print("pass %d/%d (errors %d)" % (sum(r["pass"] for r in rows), len(rows), errs))


if __name__ == "__main__":
    main()
