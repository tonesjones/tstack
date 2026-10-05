"""Behavior check for signups.py. Usage: check.py [core|boundary|nomutate|all]. Exits non-zero on mismatch."""
import copy
import os
import sys

sys.path.insert(0, os.getcwd())
import signups as s

part = sys.argv[1] if len(sys.argv) > 1 else "all"
ROWS = [
    {"name": "  Ann  ", "email": " Ann@X.com "},
    {"name": "Bob", "email": "bob@example.org"},
    {"name": "x" * 70, "email": "c@x.com"},
    {"name": "Ann again", "email": "ann@x.com"},
    {"name": "Dee", "email": "d@x.com"},
]
BAD = [{"name": "blank", "email": "   "}, {"name": "short row"}, {"name": None, "email": None}]


def names(people):
    return [(p["name"], p["email"], p.get("tag")) for p in people]


if part in ("core", "all"):
    a, w = s.build_attendees(ROWS, 2)
    assert names(a) == [("Ann", "ann@x.com", None), ("Bob", "bob@example.org", None), ("x" * 64, "c@x.com", None)], names(a)
    assert names(w) == [("Dee", "d@x.com", "waitlist")], names(w)
    assert s.build_attendees([], 3) == ([], [])
    assert s.clean_name("  hi ") == "hi" and len(s.clean_name("y" * 99)) == 64
    assert s.is_staff("a@example.org") is True and s.is_staff("a@x.com") is False
    assert s.count_by_tag([{"tag": "a"}, {"tag": "a"}]) == {"a": 2}
if part in ("boundary", "all"):
    a, w = s.build_attendees(BAD + ROWS[:1], 5)
    assert names(a) == [("Ann", "ann@x.com", None)] and w == [], (names(a), w)
if part in ("nomutate", "all"):
    rows = copy.deepcopy(ROWS)
    s.build_attendees(rows, 1)
    assert rows == ROWS, "build_attendees mutated the caller's rows"
print("behavior ok (%s)" % part)
