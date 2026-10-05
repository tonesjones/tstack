I cleaned up the code this branch added to `signups.py` (`clean_name` and `build_attendees`), and the module still imports. I didn't run any tests or call the functions, so the behavior is unchecked beyond the import.

- **`clean_name`:** it now returns `name.strip()[:MAX_NAME_LEN]`. The old version used a hardcoded `64` even though `MAX_NAME_LEN` already existed, and its length check was redundant because slicing does the same thing.
- **`build_attendees`, email handling:** it now calls the existing `normalize_email` instead of repeating the strip-and-lowercase logic. The blank-row check is now `if not email`.
- **`build_attendees`, waitlist tag:** it uses the `WAITLIST_TAG` constant instead of the string `"waitlist"`.
- **`build_attendees`, control flow and cleanup:**
  - The staff branch is now `if / elif / else` rather than an `if` with `continue`.
  - It returns `admitted, waitlist` directly, without a temporary `result` variable.
  - I removed the unneeded `rows = list(rows)`, since the rows are only looped over once.

I kept the comments that explain why the code does something (blank rows in the export, and copying each row for the audit log). I left `is_staff`'s `== True` alone because it's on `main`, not part of this branch's changes.