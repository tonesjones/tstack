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
    return email.endswith("@example.org")


def count_by_tag(rows):
    counts = {}
    for row in rows:
        counts[row["tag"]] = counts.get(row["tag"], 0) + 1
    return counts


def clean_name(name):
    return name.strip()[:MAX_NAME_LEN]


def build_attendees(rows, capacity):
    capacity = int(capacity)
    admitted = []
    waitlist = []
    seen = set()
    taken = 0
    for row in rows:
        email = row.get("email", "").strip().lower()
        if not email or email in seen:
            continue
        seen.add(email)
        entry = dict(row)
        entry["email"] = email
        entry["name"] = clean_name(row.get("name") or "")
        if is_staff(email):
            admitted.append(entry)
        elif taken < capacity:
            admitted.append(entry)
            taken += 1
        else:
            entry["tag"] = WAITLIST_TAG
            waitlist.append(entry)
    return (admitted, waitlist)
