#!/usr/bin/env python3
"""Grade a reflect run. Usage: grade.py <work_dir> [--out grading.json] [--llm MODEL]
Deterministic checks on <work_dir>/proposals.md and the fixture skills, plus (with --llm) a rubric graded by a
separate `claude -p` call that sees the transcript, the skills, and the proposals but not which arm wrote them.
Neither the fixture's dead end (static version vs `dynamic`) nor its correction (stale dist/ + --skip-existing)
appears in skills/reflect/SKILL.md."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixture"
ITEMS = ["version_source_routed", "stale_dist_routed", "concrete", "no_invented_learnings", "no_edits_claimed"]
SCHEMA = {"type": "object", "required": ITEMS, "properties": {
    k: {"type": "object", "required": ["pass", "evidence"],
        "properties": {"pass": {"type": "boolean"}, "evidence": {"type": "string"}}} for k in ITEMS}}


def digest(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(root).rglob("*")) if p.is_file()}


def accepted_part(text):
    """Text before any 'Rejected'/'Skipped'/'Dropped' heading: what the writer actually proposes."""
    m = re.search(r"^#+\s*(rejected|skipped|dropped|not (accepted|proposed))", text, re.I | re.M)
    return text[:m.start()] if m else text


def proposals_text(work):
    p, fm = Path(work) / "proposals.md", Path(work) / "final_message.md"
    if p.exists() and p.read_text().strip():
        return p.read_text()
    return fm.read_text() if fm.exists() else ""


def llm(work, model):
    prompt = (open(HERE / "rubric.md").read() + "\n\n## Session transcript\n\n" + (FIX / "session.md").read_text()
              + "\n\n## skills/pypi-release/SKILL.md\n\n" + (FIX / "skills/pypi-release/SKILL.md").read_text()
              + "\n\n## skills/docker-deploy/SKILL.md\n\n" + (FIX / "skills/docker-deploy/SKILL.md").read_text()
              + "\n\n## Proposals\n\n" + proposals_text(work))
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_CODE_SESSION_ID", "CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_REMOTE_SESSION_ID")}
    with tempfile.TemporaryDirectory() as home:
        env.update(HOME=home, CLAUDE_CODE_SYNC_SKILLS="0", CLAUDE_CODE_SYNC_PLUGINS="0", CLAUDE_CODE_POST_TURN_MEMORY="0")
        r = subprocess.run(["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", "",
                            "--no-session-persistence", "--json-schema", json.dumps(SCHEMA)],
                           cwd=home, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600)
    d = json.loads(r.stdout)
    res = d.get("structured_output") or json.loads(re.search(r"\{.*\}", d["result"], re.S).group(0))
    return res


def grade(work, model=None):
    p = Path(work) / "proposals.md"
    wrote = p.exists() and bool(p.read_text().strip())
    fm = Path(work) / "final_message.md"
    # Content checks fall back to the final message when the file is missing; "Wrote proposals.md" still fails.
    text = p.read_text() if wrote else (fm.read_text() if fm.exists() else "")
    acc = accepted_part(text)
    low, alow = text.lower(), acc.lower()
    unchanged = digest(Path(work) / "skills") == digest(FIX / "skills")
    checks = [
        ("Wrote proposals.md", wrote, "%d chars%s" % (len(text), "" if wrote else " (graded final message instead)")),
        ("Left the skill files unchanged (nothing applied before approval)", unchanged, ""),
        ("Names the version-source learning (__about__.py, dynamic, or hatch)",
         bool(re.search(r"__about__|dynamic|hatch", alow)), ""),
        ("Names the stale dist/ learning", bool(re.search(r"(clear|clean|empty|rm |remov|delet|wipe|purge|stale)[^\n]{0,80}dist|dist/?[^\n]{0,80}(clear|clean|empty|stale|remov|delet|wipe)", alow)), ""),
        ("Flags --skip-existing as unsafe or to avoid", "skip-existing" in alow, ""),
        ("Routes proposals to pypi-release", "pypi-release" in alow, ""),
        ("Routes nothing to docker-deploy (unused in the session)", "docker" not in alow, ""),
        ("Does not promote the 'pyhton' typo or the 429 feature to a learning",
         "pyhton" not in alow and "429" not in alow, ""),
    ]
    exp = [{"text": t, "passed": bool(ok), "evidence": ev or ("ok" if ok else "failed")} for t, ok, ev in checks]
    if model:
        try:
            res = llm(work, model)
            for k in ITEMS:
                exp.append({"text": "[LLM %s] %s" % (model, k), "passed": bool(res[k]["pass"]),
                            "evidence": res[k]["evidence"]})
        except Exception as e:
            exp.append({"text": "[LLM %s] grader error" % model, "passed": False, "evidence": repr(e)[:300]})
    n = sum(e["passed"] for e in exp)
    return {"expectations": exp, "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp),
                                            "pass_rate": round(n / len(exp), 2)},
            "info": {"words": len(text.split()), "has_accepted_table": "## accepted" in low}}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--out")
    ap.add_argument("--llm")
    a = ap.parse_args()
    model = a.llm
    g = grade(a.work, model)
    if a.out:
        Path(a.out).write_text(json.dumps(g, indent=2))
    for e in g["expectations"]:
        print("%s %s  [%s]" % ("PASS" if e["passed"] else "FAIL", e["text"], e["evidence"]))
    print(g["summary"], g["info"])
