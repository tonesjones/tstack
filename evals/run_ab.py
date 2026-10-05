#!/usr/bin/env python3
"""Run skill A/B evals with `claude -p` children. Idempotent: a run with a grading.json is skipped.

Usage: run_ab.py <skill> --models haiku,sonnet [--arms baseline,skill] [--runs 1,2,3] [--jobs 4]
                 [--date 2026-10-05] [--case NAME] [--work DIR]

Each run gets a fresh work dir and a throwaway HOME, so the child sees no user skills, plugins, or memory.
The skill arm copies skills/<skill>/ into <work>/.claude/skills/; the baseline arm installs nothing and is told
not to use any skill. Built-in Claude Code skills stay visible to both arms.
Results land in evals/<skill>/results/<date>/<case>/<model>-<arm>/run-N/.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
NO_SKILL = " Do not load or invoke any skill."


def setup_copy(*names):
    def f(fix, work):
        work.mkdir(parents=True, exist_ok=True)
        for n in names:
            src = fix / n
            (shutil.copytree if src.is_dir() else shutil.copy)(src, work / Path(n).name)
    return f


def setup_git(script):
    def f(fix, work):
        subprocess.run(["sh", str(fix / script), str(work)], check=True)
    return f


CASES = {
    ("unslop", "build-times-post"): dict(
        fixture="evals/unslop/fixture", setup=setup_copy("post.md"), outputs=["post.md"],
        task="Edit post.md in place so it stops reading like AI wrote it.",
        skill_suffix=" Use the unslop skill.",
        grade=["python3", "evals/unslop/grade.py"]),
    ("technical-writing", "cert-rotation-runbook"): dict(
        fixture="evals/technical-writing/fixture", setup=setup_copy("RUNBOOK.md"), outputs=["RUNBOOK.md"],
        task="Rewrite RUNBOOK.md in place so an on-call engineer can follow it.",
        skill_suffix=" Use the technical-writing skill.",
        grade=["python3", "evals/technical-writing/grade.py"]),
    ("reflect", "pypi-release-session"): dict(
        fixture="evals/reflect/fixture", setup=setup_copy("session.md", "skills"), outputs=["proposals.md"],
        task=("session.md is the transcript of a work session that just finished, and skills/ holds the skills it "
              "had. Treat that transcript as the current session. Review it for durable learnings and propose skill "
              "edits. Write your full output to proposals.md."),
        skill_suffix=" Use the reflect skill.",
        grade=["python3", "evals/reflect/grade.py", "--llm", "sonnet"], keep_dirs=["skills"]),
    ("deslop", "signups"): dict(
        fixture="evals/deslop/fixture-signups", setup=setup_git("setup_case.sh"), outputs=["signups.py"],
        task="Clean up the slop this branch (feature/signups) added to signups.py, compared with main.",
        skill_suffix=" Use the deslop skill.",
        grade=["python3", "evals/deslop/grade_signups.py"]),
}


def child_env(home):
    env = {k: v for k, v in os.environ.items() if k not in (
        "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_REMOTE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION", "CLAUDECODE")}
    env.update(HOME=str(home), CLAUDE_CODE_SYNC_SKILLS="0", CLAUDE_CODE_SYNC_PLUGINS="0",
               CLAUDE_CODE_POST_TURN_MEMORY="0")
    return env


def run_one(skill, case, cfg, model, arm, n, date, scratch):
    out = EVALS / skill / "results" / date / case / ("%s-%s" % (model, arm)) / ("run-%d" % n)
    if (out / "grading.json").exists():
        return "skip %s" % out.relative_to(ROOT)
    base = Path(tempfile.mkdtemp(prefix="%s-%s-%s-%d-" % (skill, model, arm, n), dir=scratch))
    work, home = base / "work", base / "home"
    home.mkdir()
    fix = ROOT / cfg["fixture"]
    cfg["setup"](fix, work)
    if arm == "skill":
        shutil.copytree(ROOT / "skills" / skill, work / ".claude" / "skills" / skill)
    prompt = cfg["task"] + (cfg["skill_suffix"] if arm == "skill" else NO_SKILL)
    t0 = time.time()
    with open(base / "stream.jsonl", "w") as fh:
        r = subprocess.run(["claude", "-p", prompt, "--model", model, "--output-format", "stream-json", "--verbose",
                            "--permission-mode", "bypassPermissions", "--no-session-persistence"],
                           cwd=work, env=child_env(home), stdout=fh, stderr=subprocess.PIPE, text=True,
                           stdin=subprocess.DEVNULL, timeout=1800)
    wall = time.time() - t0
    result, init, skills_called = {}, {}, []
    for line in open(base / "stream.jsonl"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") == "result":
            result = d
        elif d.get("type") == "system" and d.get("subtype") == "init":
            init = d
        elif d.get("type") == "assistant":
            for c in d["message"].get("content", []):
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    skills_called.append(c["input"].get("skill"))
    if not result or result.get("is_error"):
        (base / "stderr.txt").write_text(r.stderr)
        return "FAIL %s/%s/%s/run-%d rc=%s err=%s result=%s (kept %s)" % (
            skill, model, arm, n, r.returncode, r.stderr[-300:], str(result.get("result"))[:300], base)
    mu = result.get("modelUsage", {})
    tokens = sum(v.get(k, 0) for v in mu.values()
                 for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"))
    out.mkdir(parents=True, exist_ok=True)
    for o in cfg["outputs"]:
        if (work / o).exists():
            shutil.copy(work / o, out / o)
    for d in cfg.get("keep_dirs", []):
        if (work / d).exists():
            shutil.copytree(work / d, out / d, dirs_exist_ok=True)
    (out / "final_message.md").write_text(result.get("result") or "")
    timing = {"total_tokens": tokens, "duration_ms": result.get("duration_ms"),
              "total_duration_seconds": round((result.get("duration_ms") or wall * 1000) / 1000, 1),
              "output_tokens": sum(v.get("outputTokens", 0) for v in mu.values()),
              "cost_usd_list": result.get("total_cost_usd"), "num_turns": result.get("num_turns"),
              "model": init.get("model"), "models_used": sorted(mu), "skills_called": skills_called,
              "prompt": prompt}
    (out / "timing.json").write_text(json.dumps(timing, indent=2))
    g = subprocess.run(cfg["grade"] + [str(work), "--out", str(out / "grading.json")], cwd=ROOT,
                       capture_output=True, text=True)
    summary = g.stdout.strip().splitlines()[-1] if g.stdout.strip() else g.stderr[-300:]
    shutil.rmtree(base, ignore_errors=True)
    return "done %s/%s/%s/run-%d %s tokens=%d %.0fs skills=%s" % (
        skill, model, arm, n, summary, tokens, timing["total_duration_seconds"], skills_called)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill")
    ap.add_argument("--case")
    ap.add_argument("--models", default="haiku,sonnet")
    ap.add_argument("--arms", default="baseline,skill")
    ap.add_argument("--runs", default="1,2,3")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--date", default="2026-10-05")
    ap.add_argument("--work", default=tempfile.gettempdir())
    a = ap.parse_args()
    case = a.case or next(c for s, c in CASES if s == a.skill)
    cfg = CASES[(a.skill, case)]
    jobs = [(m, arm, int(n)) for n in a.runs.split(",") for m in a.models.split(",") for arm in a.arms.split(",")]
    with ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(run_one, a.skill, case, cfg, m, arm, n, a.date, a.work) for m, arm, n in jobs]
        for f in futs:
            try:
                print(f.result(), flush=True)
            except Exception as e:
                print("ERROR", repr(e), flush=True)


if __name__ == "__main__":
    sys.exit(main())
