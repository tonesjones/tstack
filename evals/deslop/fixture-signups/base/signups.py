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
