#!/usr/bin/env python3
"""Grade a deslop run on the signups fixture. Usage: grade_signups.py <repo_dir> [--out grading.json]
Writes skill-creator's grading.json shape: expectations[{text, passed, evidence}] + summary.
None of the seeded slop here is named in skills/deslop/SKILL.md's examples."""
import ast
import io
import json
import subprocess
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixture-signups"
TOTAL = 12


def seg(tree, src, name):
    n = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)
    return (ast.get_source_segment(src, n), n) if n else (None, None)


def comments_in(src):
    return [t.string for t in tokenize.generate_tokens(io.StringIO(src).readline) if t.type == tokenize.COMMENT]


def behave(repo, part):
    r = subprocess.run([sys.executable, str(FIX / "check.py"), part], cwd=repo, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-200:]


def grade(repo):
    try:
        return _grade(repo)
    except Exception as e:
        return {"expectations": [{"text": "File parses and build_attendees/clean_name exist", "passed": False,
                                  "evidence": repr(e)}],
                "summary": {"passed": 0, "failed": TOTAL, "total": TOTAL, "pass_rate": 0.0}}


def _grade(repo):
    src = (Path(repo) / "signups.py").read_text()
    tree = ast.parse(src)
    base_src = (FIX / "base/signups.py").read_text()
    base_tree = ast.parse(base_src)
    ba_src, ba = seg(tree, src, "build_attendees")
    cn_src, cn = seg(tree, src, "clean_name")
    if ba is None:
        raise ValueError("build_attendees missing")
    added_src = (ba_src or "") + "\n" + (cn_src or "")
    added_nodes = [n for f in (ba, cn) if f is not None for n in ast.walk(f)]
    ints = [n.value for n in added_nodes if isinstance(n, ast.Constant) and n.value == 64]
    strs = [n.value for n in added_nodes if isinstance(n, ast.Constant) and n.value == "waitlist"]
    calls = {getattr(n.func, "id", None) or getattr(n.func, "attr", None)
             for n in ast.walk(ba) if isinstance(n, ast.Call)}
    coercions = [ast.unparse(n) for n in ast.walk(ba) if isinstance(n, ast.Assign)
                 and isinstance(n.value, ast.Call) and getattr(n.value.func, "id", "") == "list"
                 and any(isinstance(t, ast.Name) and t.id == "rows" for t in n.targets)]
    # v2 (2026-10-05): int(capacity) is no longer graded. Nothing in the repo pins capacity's type, so keeping
    # the coercion is a defensible boundary guard (Opus kept it on purpose and said why), not slop.
    len_zero = [ast.unparse(n) for n in added_nodes if isinstance(n, ast.Compare)
                and isinstance(n.left, ast.Call) and getattr(n.left.func, "id", "") == "len"
                and any(isinstance(c, ast.Constant) and c.value == 0 for c in n.comparators)]
    body = ba.body
    temp_return = (len(body) >= 2 and isinstance(body[-1], ast.Return) and isinstance(body[-1].value, ast.Name)
                   and isinstance(body[-2], ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == body[-1].value.id for t in body[-2].targets))
    coms = " ".join(comments_in(ba_src))
    untouched = [n for n in ("normalize_email", "read_rows", "is_staff", "count_by_tag")
                 if seg(tree, src, n)[0] != seg(base_tree, base_src, n)[0]]
    core, core_ev = behave(repo, "core")
    bound, bound_ev = behave(repo, "boundary")
    nomut, nomut_ev = behave(repo, "nomutate")
    checks = [
        ("Valid-input behavior unchanged (check.py core)", core, core_ev),
        ("Kept the CSV boundary handling: blank, missing, and None emails still skipped (check.py boundary)", bound, bound_ev),
        ("Kept the defensive dict(row) copy: caller's rows not mutated (check.py nomutate)", nomut, nomut_ev),
        ("clean_name uses the existing MAX_NAME_LEN constant, no literal 64", not ints, "literal 64 x%d" % len(ints)),
        ("Waitlist tag uses the existing WAITLIST_TAG constant, no 'waitlist' literal", not strs, "literal x%d" % len(strs)),
        ("build_attendees reuses normalize_email instead of re-implementing it", "normalize_email" in calls and "lower" not in calls,
         "calls: %s" % sorted(c for c in calls if c)),
        ("Removed the needless rows = list(rows) copy", not coercions, "left: %s" % coercions),
        ("Removed len(...) == 0 comparisons in favor of truthiness", not len_zero, "left: %s" % len_zero),
        ("Removed the assign-then-return temp variable", not temp_return, ""),
        ("Kept the why-comment about blank export rows", "deleted sign-ups" in coms, ""),
        ("Kept the why-comment about the audit log", "audit log" in coms, ""),
        ("Left pre-existing functions untouched (normalize_email, read_rows, is_staff, count_by_tag)", not untouched,
         "changed: %s" % untouched),
    ]
    assert len(checks) == TOTAL
    exp = [{"text": t, "passed": bool(p), "evidence": e or ("ok" if p else "failed")} for t, p, e in checks]
    n = sum(e["passed"] for e in exp)
    return {"expectations": exp, "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp),
                                            "pass_rate": round(n / len(exp), 2)}}


if __name__ == "__main__":
    g = grade(sys.argv[1])
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(json.dumps(g, indent=2))
    for e in g["expectations"]:
        print("%s %s" % ("PASS" if e["passed"] else "FAIL", e["text"]))
    print(g["summary"])
