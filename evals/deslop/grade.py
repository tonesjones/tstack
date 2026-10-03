#!/usr/bin/env python3
"""Grade a deslop run. Usage: grade.py <repo_dir> [--out grading.json]
Writes skill-creator's grading.json shape: expectations[{text, passed, evidence}] + summary."""
import ast
import io
import json
import subprocess
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent


def depth(node, d=0):
    kids = [depth(c, d + isinstance(c, (ast.For, ast.If, ast.Try, ast.While, ast.With)))
            for c in ast.iter_child_nodes(node)]
    return max(kids, default=d)


def comments_in(src):
    return [tok.string for tok in tokenize.generate_tokens(io.StringIO(src).readline) if tok.type == tokenize.COMMENT]


def seg(tree, src, name):
    n = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)
    return ast.get_source_segment(src, n) if n else None


def grade(repo):
    try:
        return _grade(repo)
    except Exception as e:  # unparseable or renamed code is a failed run, not a missing one
        return {"expectations": [{"text": "File parses and restock_plan exists", "passed": False,
                                  "evidence": repr(e)}],
                "summary": {"passed": 0, "failed": 14, "total": 14, "pass_rate": 0.0}}


def _grade(repo):
    src = (Path(repo) / "inventory.py").read_text()
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "restock_plan")
    fn_src = ast.get_source_segment(src, fn)
    base_src = (HERE / "fixture/base/inventory.py").read_text()
    branch_src = (HERE / "fixture/branch/inventory.py").read_text()
    base_tree, branch_tree = ast.parse(base_src), ast.parse(branch_src)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
            {n.value.id for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    imported = [a.asname or a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names]
    unused = [i for i in imported if i not in names]
    # run the pristine check from the harness, never the copy in the repo the model could edit
    r = subprocess.run([sys.executable, str(HERE / "fixture/check.py")], cwd=repo, capture_output=True, text=True)
    handlers = [h for h in ast.walk(fn) if isinstance(h, ast.ExceptHandler)]
    params = {"stock", "targets"}
    guards = [n for n in ast.walk(fn)
              if (isinstance(n, ast.If) and any(isinstance(x, ast.Name) and x.id in params for x in ast.walk(n.test)))
              or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in params for t in n.targets))
              or (isinstance(n, ast.BoolOp) and any(isinstance(x, ast.Name) and x.id in params for x in n.values))
              or (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "isinstance")]
    out_calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and (
        getattr(n.func, "id", "") == "print" or
        (isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
         and n.func.value.id in ("logging", "logger", "sys")))]
    fn_comments = comments_in(fn_src)
    extra = [c for c in fn_comments if "OPS-114" not in c]
    untouched = [n for n in ("load_stock", "low_stock", "total_units") if seg(tree, src, n) != seg(base_tree, base_src, n)]
    checks = [
        ("Valid-input behavior unchanged: fixture check.py passes", r.returncode == 0, (r.stdout + r.stderr).strip()[-200:]),
        ("Removed every comment in restock_plan except the OPS-114 why-comment", not extra, "left: %s" % extra),
        ("Removed the change-describing comment ('new implementation')", "new implementation" not in src.lower(), ""),
        ("Removed the broad try/except around pure logic", not handlers, "%d handler(s) left in restock_plan" % len(handlers)),
        ("Removed redundant guards on the trusted args (isinstance, None, or-defaults, reassignment)", not guards, "%d guard(s)" % len(guards)),
        ("Removed the debug output (print/logging) from restock_plan", not out_calls, ""),
        ("Removed unused imports", not unused, "unused: %s" % unused),
        ("Removed the single-use _get_qty wrapper", "_get_qty" not in src, ""),
        ("Removed the type escape (cast/# type: ignore)", "type: ignore" not in src and "cast(" not in src, ""),
        ("Flattened nesting in restock_plan to depth <= 3", depth(fn) <= 3, "depth=%d" % depth(fn)),
        ("Kept the why-comment citing OPS-114", "OPS-114" in src, ""),
        ("Kept the JSONDecodeError handling at the file boundary (load_targets)",
         "JSONDecodeError" in (seg(tree, src, "load_targets") or "") and "raise ValueError" in (seg(tree, src, "load_targets") or ""), ""),
        ("Left pre-existing functions untouched (load_stock, low_stock, total_units identical to main)", not untouched,
         "changed: %s" % untouched),
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
