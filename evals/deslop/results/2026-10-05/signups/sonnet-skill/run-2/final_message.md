I cleaned up the code this branch added to `signups.py`. I didn't touch the older `is_staff` code.

- **Constants and helper:** `clean_name` now uses the existing `MAX_NAME_LEN` and `build_attendees` uses `WAITLIST_TAG` instead of hardcoded `64` and `"waitlist"`. The email cleanup goes through the existing `normalize_email` instead of a second inline strip and lowercase.
- **Removed:** the needless `rows = list(rows)` copy, the temporary `result` variable, and the doubled blank-email check.
- **Kept:** the two "why" comments, and `int(capacity)`, which I read as a trust-boundary conversion.

There's no test suite or lint config in the repo, so I only ran a quick manual check of `build_attendees`. Staff addresses, capacity and the waitlist behaved as before.