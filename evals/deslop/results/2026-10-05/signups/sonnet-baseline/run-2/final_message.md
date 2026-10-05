I cleaned up the code this branch added to `signups.py`. The module imports cleanly, but I didn't run any tests or check behaviour.

- **`clean_name`:** it now uses the existing `MAX_NAME_LEN` constant instead of a hardcoded 64. The length check and reassignment became one slice.
- **`build_attendees`:**
  - I removed the redundant `rows = list(rows)`, since the rows are only iterated once.
  - Email handling now calls the existing `normalize_email` helper, with a plain `if not email` check in place of the strip-and-length test.
  - The staff and capacity branches are now one `if/elif/else` chain, with no `continue`.
  - The waitlist tag uses `WAITLIST_TAG` instead of a string literal.
  - It returns the tuple directly instead of going through a temporary `result`.
- **Left alone:** `capacity = int(capacity)` stays in case callers pass a string. I also kept the two comments explaining blank rows and the audit-log copy. `is_staff` is already on main, so I didn't touch it.