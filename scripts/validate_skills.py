#!/usr/bin/env python3
"""Validate skills/*/SKILL.md. Stdlib only. Exits non-zero on any failure."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^Version: \d+\.\d+\.\d+ \(\d{4}-\d{2}-\d{2}\)$")
CURSOR_RES = [
    (re.compile(r"cursor", re.I), "cursor"),
    (re.compile(r"\.mdc", re.I), ".mdc"),
    (re.compile(r"alwaysApply", re.I), "alwaysApply"),
    (re.compile(r"globs:", re.I), "globs:"),
]


def parse_frontmatter(lines):
    if not lines or lines[0].strip() != "---":
        return None, "missing opening --- frontmatter delimiter", 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = {}
            for ln in lines[1:i]:
                if not ln.strip() or ln.lstrip().startswith("#"):
                    continue
                if ln[0] in " \t":
                    continue  # continuation of a previous value; ignored
                if ":" not in ln:
                    return None, "unparseable frontmatter line: %r" % ln, i
                k, v = ln.split(":", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                fm[k.strip()] = v
            return fm, None, i
    return None, "missing closing --- frontmatter delimiter", 0


def check_skill(d):
    errs = []
    f = d / "SKILL.md"
    if not f.is_file():
        return ["SKILL.md missing"]
    text = f.read_text(encoding="utf-8", errors="replace")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    fm, err, end = parse_frontmatter(lines)
    if err:
        errs.append(err)
    else:
        for key in ("name", "description"):
            if not fm.get(key):
                errs.append("frontmatter %r missing or empty" % key)
        if fm.get("name") and fm["name"] != d.name:
            errs.append("name %r != folder %r" % (fm["name"], d.name))
        if "globs" in fm:
            errs.append("Cursor-specific frontmatter key 'globs'")
        if not any(VERSION_RE.match(l) for l in lines[end + 1:]):
            errs.append("no 'Version: X.Y.Z (YYYY-MM-DD)' line in body")
    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        if any(rx.search(p.name) for rx, _ in CURSOR_RES[:2]):
            errs.append("Cursor-specific filename: %s" % p.relative_to(d))
        try:
            content = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, ln in enumerate(content.splitlines(), 1):
            for rx, label in CURSOR_RES:
                if rx.search(ln):
                    errs.append("%s:%d Cursor-specific reference (%s)" % (p.relative_to(d), n, label))
    return errs


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "skills"
    dirs = sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    if not dirs:
        print("FAIL: no skill folders found in %s" % root)
        return 1
    bad = 0
    for d in dirs:
        errs = check_skill(d)
        if errs:
            bad += 1
            print("FAIL %s: %s" % (d.name, "; ".join(errs)))
        else:
            print("OK   %s" % d.name)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
