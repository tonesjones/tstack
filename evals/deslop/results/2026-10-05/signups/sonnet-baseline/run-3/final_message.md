I cleaned up the code this branch added to `signups.py`. The module imports cleanly, but I didn't run any behavior tests.

- **`clean_name`:** it's now `name.strip()[:MAX_NAME_LEN]`. The old version hardcoded 64 and had a redundant length check, and `MAX_NAME_LEN` was already defined at the top of the file.
- **Waitlist tag:** it now uses `WAITLIST_TAG` instead of the literal `"waitlist"`.
- **Email handling:** the duplicated strip/lower logic is replaced by the existing `normalize_email`, and the `len(raw.strip()) == 0` check is now `if not email`.
- **`build_attendees`:** I removed the unneeded `rows = list(rows)` copy and the `result` temporary before the return. The staff `continue` became an `if/elif/else`. I kept the comments that explain why the code does something.
- **`capacity`:** the `int(capacity)` conversion now happens inside the capacity check, on every non-staff row, rather than once up front. A bad capacity value that used to fail immediately now only fails when a non-staff row is reached. If you'd rather keep the early failure, hoist the conversion back to the top.

I left `is_staff` alone because it's on `main` already, not part of this branch's changes. It has its own redundant `== True` / `if/else` that you may want to tidy separately.