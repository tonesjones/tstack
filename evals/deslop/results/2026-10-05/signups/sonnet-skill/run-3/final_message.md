I cleaned up the code this branch added to `signups.py`. The file compiles with `py_compile`, but I didn't run any tests.

- **Simplified:** `clean_name` is now a one-line slice, `build_attendees` returns the tuple directly, and the blank-email check is simpler.
- **Removed:** the redundant `rows = list(rows)` copy.
- **Reused existing code:** it now uses the file's existing `MAX_NAME_LEN`, `WAITLIST_TAG` and `normalize_email` instead of repeating the literals.
- **Kept:** the two comments that explain why, and `int(capacity)`, since removing it could change behavior. `is_staff` isn't from this branch, so I left it alone.