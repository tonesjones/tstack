I cleaned up the code this branch added to `signups.py` (19 lines → 6 changed, net −7). The changes aren't committed yet. I didn't run a test suite; I ran a quick check with sample rows (an uppercase email with spaces, a blank row, a duplicate, a staff address and a capacity of 1), and the output was correct.

**What changed:**
- **Uses what's already in the file:** the new code now uses `MAX_NAME_LEN`, `WAITLIST_TAG` and `normalize_email` instead of a hardcoded `64`, `"waitlist"` and a copy of the `.strip().lower()` logic.
- **`clean_name`:** now one line, `name.strip()[:MAX_NAME_LEN]`. The length check before truncating did nothing.
- **Blank emails:** the code normalises the email once and skips the row if it's empty (`if not email`), instead of stripping it twice and checking `len(...) == 0`.
- **Removed `rows = list(rows)`:** the function only loops over the rows once, so copying them into a list first wasn't needed.
- **Staff / capacity / waitlist:** this is now a single `if/elif/else` instead of `append` followed by `continue`.
- **Return value:** returns `admitted, waitlist` directly instead of going through a `result` variable.

**What I kept on purpose:**
- `capacity = int(capacity)`. Nothing else in the repo calls `build_attendees`, so I couldn't tell whether a caller might pass the capacity as a string. Removing it could break that.
- The two comments about blank export rows and copying the row for the audit log, because they explain why the code does what it does.

**Left alone:** `is_staff` has the same kind of clutter (`== True` with an if/else), but it already exists on `main`, so it's outside what this branch added.