"""Event sign-ups: parse a CSV export and build the attendee list."""
import csv

MAX_NAME_LEN = 64
WAITLIST_TAG = "waitlist"


def normalize_email(email):
    return email.strip().lower()


def read_rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def is_staff(email):
    if email.endswith("@example.org") == True:
        return True
    else:
        return False


def count_by_tag(rows):
    counts = {}
    for row in rows:
        counts[row["tag"]] = counts.get(row["tag"], 0) + 1
    return counts


def clean_name(name):
    name = name.strip()
    if len(name) > 64:
        name = name[:64]
    return name


def build_attendees(rows, capacity):
    rows = list(rows)
    capacity = int(capacity)
    admitted = []
    waitlist = []
    seen = set()
    taken = 0
    for row in rows:
        raw = row.get("email") or ""
        if len(raw.strip()) == 0:
            continue  # exports include blank rows for deleted sign-ups
        email = raw.strip().lower()
        if email in seen:
            continue
        seen.add(email)
        entry = dict(row)  # the caller reuses rows for the audit log
        entry["email"] = email
        entry["name"] = clean_name(row.get("name") or "")
        if is_staff(email):
            admitted.append(entry)
            continue
        if taken < capacity:
            admitted.append(entry)
            taken += 1
        else:
            entry["tag"] = "waitlist"
            waitlist.append(entry)
    result = (admitted, waitlist)
    return result
