#!/usr/bin/env python3
"""Blind LLM rubric grading for a finished run. The grader sees the rubric, the original fixture, and the output,
never the arm, model, or path. Usage:
  llm_grade.py <skill> <run_dir> [--model sonnet]   -> writes <run_dir>/llm_grading.json
  llm_grade.py <skill> --all <results_dir> [--jobs 4]
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = {
    "unslop": dict(rubric="evals/unslop/rubric.md", original="evals/unslop/fixture/post.md", output="post.md",
                   items=["meaning_preserved", "no_new_tells", "reads_human", "tone_matches"]),
    "technical-writing": dict(rubric="evals/technical-writing/rubric.md",
                              original="evals/technical-writing/fixture/RUNBOOK.md", output="RUNBOOK.md",
                              items=["no_invented_facts", "rollback_correct", "how_to_only", "first_read"]),
}


def schema(items):
    return {"type": "object", "required": items, "properties": {
        k: {"type": "object", "required": ["pass", "evidence"],
            "properties": {"pass": {"type": "boolean"}, "evidence": {"type": "string"}}} for k in items}}


def grade(skill, run_dir, model):
    spec = SPECS[skill]
    prompt = ((ROOT / spec["rubric"]).read_text() + "\n\n## Original\n\n" + (ROOT / spec["original"]).read_text()
              + "\n\n## Rewrite\n\n" + (Path(run_dir) / spec["output"]).read_text())
    env = {k: v for k, v in os.environ.items() if k not in (
        "CLAUDE_CODE_SESSION_ID", "CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_REMOTE_SESSION_ID")}
    with tempfile.TemporaryDirectory() as home:
        env.update(HOME=home, CLAUDE_CODE_SYNC_SKILLS="0", CLAUDE_CODE_SYNC_PLUGINS="0", CLAUDE_CODE_POST_TURN_MEMORY="0")
        r = subprocess.run(["claude", "-p", prompt, "--model", model, "--output-format", "json", "--tools", "",
                            "--no-session-persistence", "--json-schema", json.dumps(schema(spec["items"]))],
                           cwd=home, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=600)
    d = json.loads(r.stdout)
    if d.get("is_error") or d.get("terminal_reason") == "api_error":
        raise RuntimeError("grader call failed: %s" % str(d.get("result"))[:200])
    res = d.get("structured_output") or json.loads(re.search(r"\{.*\}", d["result"], re.S).group(0))
    exp = [{"text": "[LLM %s] %s" % (model, k), "passed": bool(res[k]["pass"]), "evidence": res[k]["evidence"]}
           for k in spec["items"]]
    n = sum(e["passed"] for e in exp)
    out = {"expectations": exp, "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp),
                                            "pass_rate": round(n / len(exp), 2)}, "grader_model": model}
    (Path(run_dir) / "llm_grading.json").write_text(json.dumps(out, indent=2))
    return out


def main():
    skill = sys.argv[1]
    model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "sonnet"
    if "--all" in sys.argv:
        base = Path(sys.argv[sys.argv.index("--all") + 1])
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 4
        runs = sorted(p.parent for p in base.rglob("grading.json") if not (p.parent / "llm_grading.json").exists())
        with ThreadPoolExecutor(jobs) as ex:
            for run, f in [(r, ex.submit(grade, skill, r, model)) for r in runs]:
                try:
                    print(run.relative_to(ROOT), f.result()["summary"], flush=True)
                except Exception as e:
                    print("ERROR", run, repr(e)[:300], flush=True)
    else:
        print(json.dumps(grade(skill, sys.argv[2], model), indent=2))


if __name__ == "__main__":
    main()
