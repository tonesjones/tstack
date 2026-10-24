#!/usr/bin/env python3
"""Print release notes listing each skill's version and whether its zip changed. Stdlib only."""
import sys

from validate_skills import ROOT, VERSION_RE, changed_skills, previous_tag


def skill_version(d):
    lines = (d / "SKILL.md").read_text(encoding="utf-8").splitlines()
    return next(m.group(1) for m in map(VERSION_RE.match, lines) if m)


def main():
    dirs = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    changed = changed_skills()
    prev = previous_tag()

    if changed is None:
        print("First release: upload every skill's zip.\n")
        changed = {d.name for d in dirs}
    elif changed:
        names = ", ".join("`%s`" % d.name for d in dirs if d.name in changed)
        print("**Re-upload:** %s. Every other skill is unchanged since %s, so its installed copy "
              "is already current.\n" % (names, prev))
    else:
        print("**Re-upload:** none. No skill changed since %s.\n" % prev)
    print("| Skill | Version | Changed |")
    print("|---|---|---|")
    for d in dirs:
        print("| %s | %s | %s |" % (d.name, skill_version(d), "yes" if d.name in changed else "no"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
