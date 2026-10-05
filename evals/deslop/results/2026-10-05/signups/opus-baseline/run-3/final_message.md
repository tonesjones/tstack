I cleaned up the code this branch added to `signups.py`; the changes aren't committed. A quick hand-run test gave the expected results: duplicates and blank emails are skipped, staff skip the capacity limit, the waitlist gets tagged, names are trimmed to 64 characters, and the input rows aren't changed. There's no test suite in the repo, so that's the only check I ran.

**`clean_name`**
- It now uses the existing `MAX_NAME_LEN` constant instead of a hard-coded `64`.
- The length check before trimming wasn't needed, so it's now one line: `name.strip()[:MAX_NAME_LEN]`.

**`build_attendees`**
- It now calls the existing `normalize_email()` instead of repeating `.strip().lower()`.
- The blank-email check is now `if not email`, run after normalizing. Before, it stripped the string twice and checked `len(...) == 0`.
- It uses the existing `WAITLIST_TAG` constant instead of the `"waitlist"` string.
- I removed the unneeded `rows = list(rows)` copy, since the loop only goes through the rows once.
- I replaced `append` + `continue` with `if/elif/else`, and the function now returns the pair directly instead of through a temporary `result` variable.

**What I kept**
- The two comments that explain why (blank rows in exports, and copying rows because the caller reuses them for the audit log).
- The `int(capacity)` conversion. Nothing calls `build_attendees` yet, so I couldn't rule out that it gets passed a string capacity, for example from config. Removing it is safe if capacity is always an int.

I left `is_staff` alone even though its `== True` / `else` is clumsy, because it was already on `main`.