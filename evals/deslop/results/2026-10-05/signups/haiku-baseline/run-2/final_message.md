Done. Cleaned up the slop:

- **`is_staff`**: Removed verbose `== True` and unnecessary else clause
- **`clean_name`**: Used the `MAX_NAME_LEN` constant instead of hardcoding 64, simplified to one-liner
- **`build_attendees`**: Removed pointless `list()` conversion, simplified email validation to one line, used `WAITLIST_TAG` constant instead of hardcoded string, converted `if/continue` pattern to `elif`, eliminated intermediate `result` variable, removed unnecessary comments