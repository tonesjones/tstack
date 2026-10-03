#!/usr/bin/env python3
"""Grade a deslop run. Usage: grade.py <repo_dir> [--out grading.json]
Writes skill-creator's grading.json shape: expectations[{text, passed, evidence}] + summary."""
import ast
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def depth(node, d=0):
    kids = [depth(c, d + isinstance(c, (ast.For, ast.If, ast.Try, ast.While, ast.With)))
            for c in ast.iter_child_nodes(node)]
    return max(kids, default=d)


def grade(repo):
    src = (Path(repo) / "inventory.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "restock_plan")
    fn_src = ast.get_source_segment(src, fn)
    base = (HERE / "fixture/base/inventory.py").read_text().splitlines()
    lines = set(src.splitlines())
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
            {n.value.id for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    imported = [a.asname or a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names]
    unused = [i for i in imported if i not in names]
    r = subprocess.run([sys.executable, "check.py"], cwd=repo, capture_output=True, text=True)
    broad = [h for h in ast.walk(fn) if isinstance(h, ast.ExceptHandler)]
    checks = [
        ("Behavior unchanged: check.py passes", r.returncode == 0, (r.stdout + r.stderr).strip()[-200:]),
        ("Removed comments that narrate the code (loop over / get the current / return the plan)",
         not any(p in src for p in ("loop over each sku", "get the current quantity", "return the plan")), ""),
        ("Removed the change-describing comment ('new implementation')", "new implementation" not in src, ""),
        ("Removed the broad try/except Exception around pure logic", not broad, "%d handler(s) left in restock_plan" % len(broad)),
        ("Removed redundant isinstance/None checks on trusted args",
         "isinstance" not in fn_src and "is None" not in fn_src, ""),
        ("Removed the debug print", "print(" not in fn_src, ""),
        ("Removed unused imports", not unused, "unused: %s" % unused),
        ("Removed the single-use _get_qty wrapper", "_get_qty" not in src, ""),
        ("Removed the type escape (cast/# type: ignore)", "type: ignore" not in src and "cast(" not in src, ""),
        ("Flattened nesting in restock_plan to depth <= 3", depth(fn) <= 3, "depth=%d" % depth(fn)),
        ("Kept the why-comment citing OPS-114", "OPS-114" in src, ""),
        ("Kept the JSONDecodeError handling at the file boundary (load_targets)", "JSONDecodeError" in src, ""),
        ("Left pre-existing code untouched: all base lines still present",
         all(l in lines for l in base if l.strip()), ""),
        ("Left the pre-existing narrating comment in total_units alone", "# loop over the stock and add it up" in src, ""),
    ]
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
