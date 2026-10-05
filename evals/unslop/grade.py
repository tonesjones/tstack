#!/usr/bin/env python3
"""Grade an unslop run. Usage: grade.py <work_dir> [--out grading.json]
Deterministic checks on <work_dir>/post.md against fixture/post.md. Writes skill-creator's grading.json shape.
Seeded tells are phrased so that none appears literally in skills/unslop/SKILL.md, except title-case headings
(pattern 17), marked [named]."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIG = (HERE / "fixture/post.md").read_text()
QUOTE = '"The cache was a game changer, but the benchmark is what told us where to look."'
CODE_RE = re.compile(r"```.*?```", re.S)
NUM_RE = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")


def prose(text):
    """Text outside code fences, HTML comments, and the Priya quote, lowercased, curly quotes straightened."""
    t = CODE_RE.sub(" ", text)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = t.replace("’", "'").replace("“", '"').replace("”", '"').replace(QUOTE, " ")
    return t.lower()


def gone(p, *phrases):
    left = [x for x in phrases if x in p]
    return not left, "left: %s" % left if left else "ok"


def numbers(text):
    return {n.rstrip(",").replace(",", "") for n in NUM_RE.findall(CODE_RE.sub(" ", text))}


def grade(work):
    out = (Path(work) / "post.md").read_text()
    p = prose(out)
    heads = [h.strip("# ").strip() for h in out.splitlines() if re.match(r"#{1,6} ", h)]
    title_case = [h for h in heads if len([w for w in h.split()[1:] if w[:1].isupper() and len(w) > 3]) >= 2]
    codes, orig_codes = CODE_RE.findall(out), CODE_RE.findall(ORIG)
    facts = ["41 minutes", "19 minutes", "p95", "january", "priya raman", "12%", "87%", "11 services",
             "70%", "6 minutes", "$2,400"]
    plain = CODE_RE.sub(" ", out).lower().replace("’", "'")
    missing = [f for f in facts if f not in plain and not (f == "11 services" and re.search(r"\b11\b", plain))]
    refrain = re.sub(r"<!--.*?-->", " ", out, flags=re.S).count("Measure, then cut.")
    invented = sorted(numbers(out) - numbers(ORIG))
    checks = [
        ("Removed the 'in today's fast-paced world' opener", *gone(p, "fast-paced", "in today's")),
        ("Removed the 'whether you're a seasoned engineer' audience hedge", *gone(p, "seasoned", "whether you're")),
        ("Removed 'let's dive in'", *gone(p, "dive in")),
        ("Removed the journey framing ('embarked on a journey', 'continue on this journey')", *gone(p, "journey", "embark")),
        ("Removed the buzzword cluster (leveraging, seamless, robust, empower, speed of thought, unlock)",
         *gone(p, "leverag", "seamless", "robust", "empower", "speed of thought", "unlock")),
        ("Removed 'game changer' from the author's own prose", *gone(p, "game changer", "game-changer")),
        ("Removed the staged reveals ('Here's the thing:', 'The result?')", *gone(p, "here's the thing", "the result?")),
        ("Removed 'Notably' and 'Needless to say'", *gone(p, "notably", "needless to say")),
        ("Removed 'We didn't stop there'", *gone(p, "didn't stop there", "did not stop there")),
        ("Removed the stock ending (end of the day, culture of excellence, what the future holds)",
         *gone(p, "end of the day", "culture of excellence", "future holds")),
        ("Removed the 'feel free to reach out' sign-off", *gone(p, "feel free", "reach out")),
        ("Removed the stock headings ('Navigating the Complexities', 'A Holistic Approach', 'Wrapping Up')",
         *gone(" ".join(heads).lower(), "navigating", "holistic", "wrapping up")),
        ("[named] Headings in sentence case", not title_case, "title case: %s" % title_case),
        ("Kept 'Measure, then cut.' exactly three times (outside the author's note)", refrain == 3, "count=%d" % refrain),
        ("Kept every fact (times, rates, counts, cost, name, month)", not missing, "missing: %s" % missing),
        ("Introduced no new numbers", not invented, "new: %s" % invented),
        ("Left the code block byte-identical", codes == orig_codes, "%d block(s)" % len(codes)),
        ("Kept Priya's quote verbatim (it contains 'game changer' on purpose)",
         QUOTE in out.replace("“", '"').replace("”", '"'), ""),
    ]
    exp = [{"text": t, "passed": bool(ok), "evidence": ev} for t, ok, ev in checks]
    n = sum(e["passed"] for e in exp)
    info = {"words": len(out.split()), "orig_words": len(ORIG.split()), "em_dashes": out.count("—"),
            "orig_em_dashes": ORIG.count("—")}
    return {"expectations": exp, "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp),
                                            "pass_rate": round(n / len(exp), 2)}, "info": info}


if __name__ == "__main__":
    g = grade(sys.argv[1])
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(json.dumps(g, indent=2))
    for e in g["expectations"]:
        print("%s %s  [%s]" % ("PASS" if e["passed"] else "FAIL", e["text"], e["evidence"]))
    print(g["summary"], g["info"])
