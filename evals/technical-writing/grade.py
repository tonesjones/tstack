#!/usr/bin/env python3
"""Grade a technical-writing run. Usage: grade.py <work_dir> [--out grading.json]
Deterministic checks on <work_dir>/RUNBOOK.md. Writes skill-creator's grading.json shape.
The fixture's defects (a step the author forgot and appended later, a warning buried after its step, three names
for one service, a missing prerequisite section) are not literal examples in skills/technical-writing/SKILL.md;
checks that test a rule the skill states outright are marked [named]."""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIG = (HERE / "fixture/RUNBOOK.md").read_text()
COMMANDS = [
    "vault write pki/issue/billing common_name=billing.internal.example.com ttl=2160h",
    "billingctl drain --wait 120",
    "sudo mv /etc/billing/tls/new.pem /etc/billing/tls/current.pem",
    "sudo systemctl restart billing-worker",
    "curl -s https://billing.internal.example.com:8443/healthz",
    "billingctl resume",
]
FACTS = ["90 days", "14 days", "BillingCertExpiring", "billing-ops", "VPN", "#billing-oncall", "month-end",
         "3 business days", "2 minutes"]
VERBS = {"issue", "drain", "back", "copy", "swap", "move", "restart", "check", "verify", "confirm", "resume",
         "undrain", "roll", "restore", "save", "run", "connect", "get", "make", "wait", "replace", "install",
         "request", "generate", "if", "to", "log", "sign", "ensure", "open", "stop", "start", "test", "rotate",
         "create", "put", "write", "update", "do", "don't", "skip", "re-run", "rerun", "repeat", "on", "when",
         "before", "after", "keep", "use", "switch", "edit", "set", "remove", "delete", "store", "call", "drop",
         "note", "ask", "post", "contact", "notify", "page", "escalate", "once", "backup", "verify", "tell",
         "message", "unless", "while", "reach"}


def norm(s):
    return re.sub(r"\s+", " ", s)


def grade(work):
    out = (Path(work) / "RUNBOOK.md").read_text()
    flat = norm(out)
    low = flat.lower()
    lines = out.splitlines()
    step_re = r"\s*(?:#+\s*)?(?:step\s*)?\d+[.:)]\s+\W*(\w[\w'-]*)"
    numbered = [(i, l) for i, l in enumerate(lines) if re.match(step_re, l, re.I)]
    first_words = [re.match(step_re, l, re.I).group(1).lower() for _, l in numbered]
    not_imperative = [w for w in first_words if w not in VERBS]
    pos = lambda pat: (m.start() if (m := re.search(pat, out, re.I | re.S)) else -1)
    backup = pos(r"cp\s+\S*current\.pem\s+\S*previous\.pem")
    swap = pos(re.escape(COMMANDS[2]))
    drain = out.find(COMMANDS[1])
    monthend = low.find("month-end")
    vpn = out.find("VPN")
    issue = out.find(COMMANDS[0])
    heads = [l.lstrip("#").strip() for l in lines if l.startswith("#")]
    title_case = [h for h in heads if len([w for w in h.split()[1:] if w[:1].isupper() and len(w) > 3
                                           and w not in ("TLS", "Vault", "VPN")]) >= 2]
    missing_cmds = [c for c in COMMANDS if c not in flat]
    missing_facts = [f for f in FACTS if f.lower() not in low
                     and not (f == "2 minutes" and re.search(r"120 seconds|two minutes", low))]
    banned = [w for w in ("basically", "so basically", "i forgot", "!!", "its mostly", "dont ", "you should",
                          "should be saved", "it's important to note", "which is nice", "actually")
              if w in low]
    synonyms = [w for w in ("consumer", "job runner") if w in low]
    restore = re.search(r"previous\.pem", out[max(out.find(COMMANDS[4]), 0):]) is not None
    # 'consumer' and 'job runner' are reported in info, not scored: the fixture never states they are billing-worker,
    # so keeping them is defensible.
    checks = [
        ("Every original command kept verbatim", not missing_cmds, "missing: %s" % missing_cmds),
        ("Every operational fact kept (validity, alert lead time, alert name, role, VPN, channel, close window, drain time)",
         not missing_facts, "missing: %s" % missing_facts),
        ("The forgotten backup step (cp current.pem previous.pem) is written as its own command before the swap",
         backup != -1 and swap != -1 and backup < swap, "backup@%d swap@%d" % (backup, swap)),
        ("The month-end warning comes before the drain step", monthend != -1 and drain != -1 and monthend < drain,
         "month-end@%d drain@%d" % (monthend, drain)),
        ("VPN and billing-ops prerequisites come before the first command", -1 < vpn < issue, "vpn@%d issue@%d" % (vpn, issue)),
        ("[named] Steps are a numbered list (at least 6 items)", len(numbered) >= 6, "%d numbered" % len(numbered)),
        ("[named] Every numbered step starts with an imperative verb or its condition", bool(first_words) and not not_imperative,
         "non-imperative starts: %s" % not_imperative),
        ("Rollback via previous.pem is described after the health check", restore, ""),
        ("Removed the chatty and hedged phrasing (basically, you should, I forgot, !!, it's important to note)",
         not banned, "left: %s" % banned),
        ("[named] Headings in sentence case", not title_case, "title case: %s" % title_case),
    ]
    exp = [{"text": t, "passed": bool(ok), "evidence": ev} for t, ok, ev in checks]
    n = sum(e["passed"] for e in exp)
    info = {"words": len(out.split()), "orig_words": len(ORIG.split()), "numbered_steps": len(numbered),
            "mentions_2024_history": "2024" in out,
            "other_names_for_service": synonyms}
    return {"expectations": exp, "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp),
                                            "pass_rate": round(n / len(exp), 2)}, "info": info}


if __name__ == "__main__":
    g = grade(sys.argv[1])
    if "--out" in sys.argv:
        Path(sys.argv[sys.argv.index("--out") + 1]).write_text(json.dumps(g, indent=2))
    for e in g["expectations"]:
        print("%s %s  [%s]" % ("PASS" if e["passed"] else "FAIL", e["text"], e["evidence"]))
    print(g["summary"], g["info"])
