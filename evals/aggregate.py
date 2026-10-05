#!/usr/bin/env python3
"""Summarize A/B results as markdown tables. Usage: aggregate.py <skill> [--date 2026-10-05]
Reads evals/<skill>/results/<date>/<case>/<model>-<arm>/run-N/{grading,llm_grading,timing}.json."""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORDER = {"haiku": 0, "sonnet": 1, "opus": 2}
NAMES = {"haiku": "Haiku 4.5", "sonnet": "Sonnet 5.5", "opus": "Opus 5.5"}


def pct(x):
    return "%d%%" % round(100 * x)


def rate(exps):
    return sum(e["passed"] for e in exps) / len(exps) if exps else None


def load(p):
    return json.load(open(p)) if p.exists() else None


def main():
    skill = sys.argv[1]
    date = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else "2026-10-05"
    base = ROOT / "evals" / skill / "results" / date
    for case in sorted(p for p in base.iterdir() if p.is_dir()):
        cells = defaultdict(list)
        for run in sorted(case.glob("*/run-*")):
            model, arm = run.parent.name.rsplit("-", 1)
            cells[(model, arm)].append(run)
        has_llm = any((r / "llm_grading.json").exists() or "[LLM" in (r / "grading.json").read_text()
                      for rs in cells.values() for r in rs)
        print("### %s / %s\n" % (skill, case.name))
        hdr = "| Model | Arm | Det. mean | Det. per run |" + (" LLM mean | LLM per run |" if has_llm else "") + \
              " Tokens (mean) | Time (mean) | Skill loaded |"
        print(hdr)
        print("|" + "---|" * hdr.count("|")[:-1] if False else "|" + "|".join(["---"] * (hdr.count("|") - 1)) + "|")
        misses = {}
        for (model, arm) in sorted(cells, key=lambda k: (ORDER.get(k[0], 9), k[1])):
            runs = cells[(model, arm)]
            g = [load(r / "grading.json") for r in runs]
            l = [load(r / "llm_grading.json") for r in runs]
            t = [load(r / "timing.json") for r in runs]
            det = [rate([e for e in x["expectations"] if not e["text"].startswith("[LLM")]) for x in g]
            row = "| %s | %s | %s | %s |" % (NAMES.get(model, model), "skill" if arm == "skill" else "no skill",
                                           pct(sum(det) / len(det)), ", ".join(pct(x) for x in det))
            if has_llm:
                lv = [rate([e for e in x["expectations"] if e["text"].startswith("[LLM")]
                           + (y["expectations"] if y else [])) for x, y in zip(g, l)]
                lv = [v for v in lv if v is not None]
                row += " %s | %s |" % (pct(sum(lv) / len(lv)) if lv else "-", ", ".join(pct(x) for x in lv) or "-")
            tok = sum(x["total_tokens"] for x in t) / len(t)
            sec = sum(x["total_duration_seconds"] for x in t) / len(t)
            loaded = sum(1 for x in t if x.get("skills_called"))
            row += " %s | %.0fs | %d/%d |" % ("{:,.0f}".format(tok), sec, loaded, len(t))
            print(row)
            fails = defaultdict(int)
            for x in g + [y for y in l if y]:
                for e in x["expectations"]:
                    if not e["passed"]:
                        fails[e["text"]] += 1
            misses[(model, arm)] = dict(fails)
        print("\nMisses (count of runs):\n")
        for (model, arm), f in sorted(misses.items(), key=lambda k: (ORDER.get(k[0][0], 9), k[0][1])):
            if f:
                print("- %s %s: %s" % (NAMES.get(model, model), "skill" if arm == "skill" else "no skill",
                                       "; ".join("%s (%d)" % (k, v) for k, v in sorted(f.items(), key=lambda kv: -kv[1]))))
        print()


if __name__ == "__main__":
    main()
