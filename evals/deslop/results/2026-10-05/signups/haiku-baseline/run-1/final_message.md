Done. Cleaned up the added code to:
- Use `MAX_NAME_LEN` and `WAITLIST_TAG` constants instead of magic values
- Call `normalize_email()` instead of duplicating the logic
- Remove unnecessary `or ""` in the `clean_name()` call since the function now handles None
- Return directly instead of using an intermediate variable