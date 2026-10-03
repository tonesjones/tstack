#!/usr/bin/env python3
"""Measure token usage and cost of a Claude Code session (incl. subagents). Stdlib only."""
import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PRICING_URLS = [
    "https://platform.claude.com/docs/en/about-claude/pricing.md",
    "https://platform.claude.com/docs/en/about-claude/pricing",
]
FIELDS = ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read")


def die(msg):
    sys.exit("ERROR: " + msg)


def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def load_transcript(path):
    """Return (calls, first_ts, last_ts). calls: dedup'd assistant usage dicts in order."""
    calls, order = {}, []
    ts_min = ts_max = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            t = parse_ts(d.get("timestamp") or "")
            if t:
                ts_min = t if ts_min is None or t < ts_min else ts_min
                ts_max = t if ts_max is None or t > ts_max else ts_max
            if d.get("type") != "assistant":
                continue
            m = d.get("message") or {}
            u = m.get("usage")
            model = m.get("model") or ""
            if not u or not model or model.startswith("<") or model == "synthetic":
                continue
            cc = u.get("cache_creation") or {}
            w5 = cc.get("ephemeral_5m_input_tokens")
            w1 = cc.get("ephemeral_1h_input_tokens")
            if w5 is None and w1 is None:
                w5, w1 = u.get("cache_creation_input_tokens") or 0, 0
            rec = {"model": model, "input": u.get("input_tokens") or 0,
                   "output": u.get("output_tokens") or 0,
                   "cache_write_5m": w5 or 0, "cache_write_1h": w1 or 0,
                   "cache_read": u.get("cache_read_input_tokens") or 0}
            if not any(rec[f] for f in FIELDS):
                continue
            key = m.get("id") or d.get("requestId") or d.get("uuid")
            if key not in calls:
                order.append(key)
            calls[key] = rec  # streamed repeats: keep the last (final) usage
    return [calls[k] for k in order], ts_min, ts_max


def model_row_name(model):
    m = re.match(r"claude-(opus|sonnet|haiku)-([\d-]+?)(?:-\d{8})?$", model)
    if not m:
        return None
    return "Claude %s %s" % (m.group(1).title(), m.group(2).replace("-", "."))


def parse_pricing(text):
    rows = {}
    for ln in text.splitlines():
        if not ln.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        first = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cells[0])
        nm = re.match(r"(Claude (?:Opus|Sonnet|Haiku) [\d.]+)", first)
        if not nm:
            continue
        vals = []
        for c in cells[1:6]:
            v = re.match(r"\$([\d.]+)\s*/\s*MTok", re.sub(r"<[^>]+>", "", c))
            vals.append(float(v.group(1)) if v else None)
        if None in vals or nm.group(1) in rows:
            continue  # first table (base prices) wins
        rows[nm.group(1)] = dict(zip(
            ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output"), vals))
    return rows


def fetch_pricing():
    last = None
    for url in PRICING_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "measure_session/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                text = r.read().decode("utf-8", "replace")
                final = r.geturl()
            rows = parse_pricing(text)
            if rows:
                return rows, final, datetime.now(timezone.utc)
            last = "no pricing rows parsed from " + url
        except Exception as e:
            last = "%s: %s" % (url, e)
    die("could not fetch/parse pricing (%s). Use --pricing-file JSON for offline use." % last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-id")
    ap.add_argument("--project-dir", default=str(Path.home() / ".claude" / "projects" / "C--TestCode-tstack"))
    ap.add_argument("--routing-log", default=r"C:\TestCode\tstack\routing-log.md")
    ap.add_argument("--pricing-file", help="JSON {\"Claude Opus 5.5\": {input, cache_write_5m, cache_write_1h, cache_read, output}, ...} ($/MTok)")
    a = ap.parse_args()
    pdir = Path(a.project_dir)
    if not pdir.is_dir():
        die("project dir not found: %s" % pdir)
    if a.session_id:
        main_f = pdir / (a.session_id + ".jsonl")
    else:
        fs = sorted(pdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not fs:
            die("no *.jsonl in %s" % pdir)
        main_f = fs[-1]
    if not main_f.is_file():
        die("session file not found: %s" % main_f)
    sid = main_f.stem
    sub_files = sorted((pdir / sid / "subagents").glob("*.jsonl"))

    usage = {}
    all_ts = []
    cold = []
    for f in [main_f] + sub_files:
        calls, t0, t1 = load_transcript(f)
        all_ts += [t for t in (t0, t1) if t]
        for c in calls:
            u = usage.setdefault(c["model"], dict.fromkeys(FIELDS, 0))
            for k in FIELDS:
                u[k] += c[k]
        if f != main_f and calls:
            c0 = calls[0]
            cold.append((c0["model"], c0["cache_write_5m"], c0["cache_write_1h"]))
    if not usage:
        die("no usage found in transcripts")

    if a.pricing_file:
        with open(a.pricing_file, encoding="utf-8") as fh:
            pr = json.load(fh)
        src, when = "file:" + a.pricing_file, datetime.now(timezone.utc)
    else:
        pr, src, when = fetch_pricing()
    print("Pricing source: %s (fetched %s)" % (src, when.strftime("%Y-%m-%d %H:%M:%SZ")))

    def rates(model):
        n = model_row_name(model)
        if n not in pr:
            die("model %r (row %r) not found in pricing table; rows: %s" % (model, n, ", ".join(pr)))
        return pr[n]

    def cost(u, r):
        return sum(u[k] * r[k] for k in FIELDS) / 1e6

    opus_models = sorted((m for m in usage if "opus" in m), key=lambda m: model_row_name(m) or "")
    if opus_models:
        opus_name = model_row_name(opus_models[-1])
        opus_r = rates(opus_models[-1])
    else:
        opus_name = next((k for k in pr if "Opus" in k), None)
        if not opus_name:
            die("no Opus row in pricing")
        opus_r = pr[opus_name]

    print("Session %s: 1 main + %d subagent transcript(s)\n" % (sid, len(sub_files)))
    hdr = "%-26s %10s %10s %12s %12s %9s" % ("model", "input", "output", "cache_write", "cache_read", "cost")
    print(hdr)
    print("-" * len(hdr))
    tot = cf = 0.0
    for m in sorted(usage):
        u = usage[m]
        c = cost(u, rates(m))
        tot += c
        cf += cost(u, opus_r)
        print("%-26s %10d %10d %12d %12d %9s" % (
            m, u["input"], u["output"], u["cache_write_5m"] + u["cache_write_1h"],
            u["cache_read"], "$%.4f" % c))
    sav = cf - tot
    print("\nTotal actual:            $%.4f" % tot)
    print("Counterfactual all-Opus: $%.4f (at %s rates)" % (cf, opus_name))
    print("Savings:                 $%.4f (%.1f%%)" % (sav, 100 * sav / cf if cf else 0))

    loss = 0.0
    for m, w5, w1 in cold:
        r = rates(m)
        loss += (w5 * (r["cache_write_5m"] - r["cache_read"])
                 + w1 * (r["cache_write_1h"] - r["cache_read"])) / 1e6
    print("Cold-cache loss est.:    $%.4f over %d subagent(s)" % (loss, len(cold)))
    print("  (definition: per subagent transcript, cache_creation tokens of its first API call, priced at")
    print("   the subagent model's cache-write rate minus the same tokens priced as cache reads)")
    if all_ts:
        s = int((max(all_ts) - min(all_ts)).total_seconds())
        print("Wall-clock:              %dm%02ds (%s -> %s)" % (
            s // 60, s % 60, min(all_ts).strftime("%Y-%m-%d %H:%M:%S"), max(all_ts).strftime("%H:%M:%SZ")))

    fix = esc = 0
    rl = Path(a.routing_log)
    if rl.is_file():
        for ln in rl.read_text(encoding="utf-8", errors="replace").splitlines():
            if "|" not in ln:
                continue
            cells = [c.strip().lower() for c in ln.strip().strip("|").split("|")]
            fix += "fix" in cells
            esc += "escalate" in cells
    print("Routing verdicts:        fix=%d escalate=%d (%s)" % (fix, esc, rl))


if __name__ == "__main__":
    main()
