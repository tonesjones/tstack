Done. I cleaned up the following slop from the new code:

1. **clean_name()**: Used `MAX_NAME_LEN` constant instead of hardcoded `64`
2. **build_attendees()**:
   - Removed unnecessary `rows = list(rows)` (already a list from `read_rows`)
   - Moved email normalization before the empty check to avoid computing `strip()` twice
   - Simplified empty check from `len(raw.strip()) == 0` to `if not email`
   - Used `WAITLIST_TAG` constant instead of hardcoded `"waitlist"`
   - Removed unnecessary intermediate `result` variable