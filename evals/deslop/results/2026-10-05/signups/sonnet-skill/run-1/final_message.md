I tidied the code this branch added to `signups.py`. I didn't run any tests, and I only checked that the module still imports.

- **Name and email cleanup:** `clean_name` and the email handling now use the existing `MAX_NAME_LEN`, `WAITLIST_TAG` and `normalize_email` instead of repeating their values.
- **Redundant code removed:** I dropped the `list(rows)` copy, the verbose empty-email check, and the temporary `result` variable.
- **Kept on purpose:** the two comments that explain why (blank rows in exports, and rows being reused for the audit log) and `int(capacity)`.